from datetime import date
from decimal import Decimal
from enum import Enum
import logging
import sqlite3
from time import perf_counter
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from .core.models import Account, Bill, Flexibility, IncomeSource, RecurrenceRule, RecurrenceType
from .core.optimizer import OptimizationResult, optimize_schedule
from .core.projection import project
from .auth import create_access_token, current_user_id, hash_password, verify_password
from .storage import ItemRecord, ScenarioStore
from .settings import Settings


class RecurrenceRequest(BaseModel):
    kind: RecurrenceType
    anchor: date
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    second_day_of_month: int | None = Field(default=None, ge=1, le=31)


class AccountRequest(BaseModel):
    starting_balance: Decimal
    as_of: date


class AuthRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=72)


class IncomeRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(gt=0)
    recurrence: RecurrenceRequest
    variance_pct: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    enabled: bool = True


class BillRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(gt=0)
    recurrence: RecurrenceRequest
    flexibility: Flexibility
    variance_pct: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    window_start: int | None = Field(default=None, ge=1, le=31)
    window_end: int | None = Field(default=None, ge=1, le=31)
    enabled: bool = True


class EnabledRequest(BaseModel):
    enabled: bool


class OverrideRequest(BaseModel):
    item_id: int | None = Field(default=None, gt=0)
    bill_id: int | None = Field(default=None, gt=0)
    occurrence_date: date
    new_date: date


class OverrideResponse(BaseModel):
    id: int
    item_id: int
    bill_name: str
    occurrence_date: date
    new_date: date
    created_at: str


class RecurrenceResponse(BaseModel):
    kind: RecurrenceType
    anchor: date
    day_of_month: int | None
    second_day_of_month: int | None


class AccountExportAccountResponse(BaseModel):
    id: int
    starting_balance: str
    as_of: date


class AccountExportItemResponse(BaseModel):
    id: int
    item_id: int
    kind: str
    enabled: bool
    name: str
    amount: str
    variance_pct: str
    recurrence: RecurrenceResponse
    flexibility: str | None = None
    window_start: int | None = None
    window_end: int | None = None


class AccountExportResponse(BaseModel):
    account: AccountExportAccountResponse
    incomes: list[AccountExportItemResponse]
    bills: list[AccountExportItemResponse]
    overrides: list[OverrideResponse]


class ProjectionRequest(BaseModel):
    account: AccountRequest
    incomes: list[IncomeRequest] = Field(default_factory=list)
    bills: list[BillRequest] = Field(default_factory=list)
    horizon_days: int = Field(default=90, ge=1, le=3660)


class EventResponse(BaseModel):
    name: str
    amount: Decimal
    source_date: date
    posted_date: date
    kind: str


class ProjectedDayResponse(BaseModel):
    date: date
    opening_balance: Decimal
    events: list[EventResponse]
    closing_balance: Decimal


class BillMoveResponse(BaseModel):
    bill_name: str
    original_date: date
    new_date: date


class OptimizationResponse(BaseModel):
    moves: list[BillMoveResponse]
    before_min_balance: Decimal
    after_min_balance: Decimal
    before_negative_days: int
    after_negative_days: int
    recommendation: str


settings = Settings.from_environment()
app = FastAPI(title="Cashflow Simulator API", version="0.1.0")
logger = logging.getLogger("cashflow.api")


@app.middleware("http")
async def request_context_middleware(request, call_next):
    request_id = request.headers.get("X-Request-ID", "").strip() or str(uuid4())
    started_at = perf_counter()
    response = None
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration_ms = (perf_counter() - started_at) * 1000
        logger.info(
            "request method=%s path=%s status=%s duration_ms=%.2f request_id=%s",
            request.method,
            request.url.path,
            status_code,
            duration_ms,
            request_id,
        )
        if response is not None:
            response.headers["X-Request-ID"] = request_id


app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
store = ScenarioStore(settings.database_url or settings.database_path)


def _recurrence(request: RecurrenceRequest) -> RecurrenceRule:
    return RecurrenceRule(request.kind, request.anchor, request.day_of_month, request.second_day_of_month)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    try:
        store.check_ready()
    except Exception:
        raise HTTPException(status_code=503, detail="Database is unavailable")
    return {"status": "ready"}


@app.post("/api/v1/auth/register")
def register(request: AuthRequest) -> dict[str, str]:
    email = request.email.strip().lower()
    if store.get_user_by_email(email) is not None:
        raise HTTPException(status_code=409, detail="Email is already registered")
    try:
        user_id = store.create_user(email, hash_password(request.password))
    except (sqlite3.IntegrityError, IntegrityError) as error:
        raise HTTPException(status_code=409, detail="Email is already registered") from error
    return {"access_token": create_access_token(user_id, settings.auth_secret), "token_type": "bearer"}


@app.post("/api/v1/auth/login")
def login(request: AuthRequest) -> dict[str, str]:
    user = store.get_user_by_email(request.email.strip().lower())
    if user is None or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password", headers={"WWW-Authenticate": "Bearer"})
    return {"access_token": create_access_token(int(user["id"]), settings.auth_secret), "token_type": "bearer"}


@app.post("/api/v1/accounts")
def create_account(request: AccountRequest, user_id: int = Depends(current_user_id)) -> dict[str, int]:
    account_id = store.create_account(Account(request.starting_balance, request.as_of), user_id)
    return {"id": account_id}


@app.post("/api/v1/accounts/{account_id}/incomes")
def create_income(account_id: int, request: IncomeRequest, user_id: int = Depends(current_user_id)) -> dict[str, int]:
    if store.get_account(account_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Account not found")
    income = IncomeSource(request.name, request.amount, _recurrence(request.recurrence), request.variance_pct)
    return {"id": store.create_income(account_id, income, request.enabled)}


def _item_response(record: ItemRecord) -> dict:
    item = record.item
    response = {
        "id": record.id,
        "item_id": record.item_id,
        "kind": record.kind,
        "enabled": record.enabled,
        "name": item.name,
        "amount": str(item.amount),
        "variance_pct": str(item.variance_pct),
        "recurrence": {
            "kind": item.recurrence.kind.value,
            "anchor": item.recurrence.anchor,
            "day_of_month": item.recurrence.day_of_month,
            "second_day_of_month": item.recurrence.second_day_of_month,
        },
    }
    if isinstance(item, Bill):
        response.update({"flexibility": item.flexibility.value, "window_start": item.window_start, "window_end": item.window_end})
    return response


def _account_response(account_id: int, account: Account) -> dict:
    return {"id": account_id, "starting_balance": str(account.starting_balance), "as_of": account.as_of}


@app.get("/api/v1/accounts/{account_id}/incomes")
def list_incomes(account_id: int, user_id: int = Depends(current_user_id)) -> list[dict]:
    if store.get_account(account_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return [_item_response(record) for record in store.list_items(account_id, "income")]


@app.get("/api/v1/accounts/{account_id}/export", response_model=AccountExportResponse)
def export_account(account_id: int, user_id: int = Depends(current_user_id)) -> dict:
    account = store.get_account(account_id, user_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return {
        "account": _account_response(account_id, account),
        "incomes": [_item_response(record) for record in store.list_items(account_id, "income")],
        "bills": [_item_response(record) for record in store.list_items(account_id, "bill")],
        "overrides": store.list_overrides(account_id),
    }


@app.delete("/api/v1/accounts/{account_id}", status_code=204)
def delete_account(account_id: int, user_id: int = Depends(current_user_id)) -> None:
    if not store.delete_account(account_id, user_id):
        raise HTTPException(status_code=404, detail="Account not found")


@app.put("/api/v1/accounts/{account_id}/incomes/{item_id}")
def update_income(account_id: int, item_id: int, request: IncomeRequest, user_id: int = Depends(current_user_id)) -> dict[str, int]:
    if store.get_account(account_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Account not found")
    item = IncomeSource(request.name, request.amount, _recurrence(request.recurrence), request.variance_pct)
    if not store.update_income(account_id, item_id, item, request.enabled):
        raise HTTPException(status_code=404, detail="Income not found")
    return {"id": item_id}


@app.delete("/api/v1/accounts/{account_id}/incomes/{item_id}", status_code=204)
def delete_income(account_id: int, item_id: int, user_id: int = Depends(current_user_id)) -> None:
    if store.get_account(account_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if not store.delete_item(account_id, item_id, "income"):
        raise HTTPException(status_code=404, detail="Income not found")


@app.patch("/api/v1/accounts/{account_id}/incomes/{item_id}/enabled")
def set_income_enabled(account_id: int, item_id: int, request: EnabledRequest, user_id: int = Depends(current_user_id)) -> dict[str, int | bool]:
    if store.get_account(account_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if not store.set_item_enabled(account_id, item_id, "income", request.enabled):
        raise HTTPException(status_code=404, detail="Income not found")
    return {"id": item_id, "enabled": request.enabled}


@app.post("/api/v1/accounts/{account_id}/bills")
def create_bill(account_id: int, request: BillRequest, user_id: int = Depends(current_user_id)) -> dict[str, int]:
    if store.get_account(account_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Account not found")
    bill = Bill(request.name, request.amount, _recurrence(request.recurrence), request.flexibility, request.variance_pct, request.window_start, request.window_end)
    return {"id": store.create_bill(account_id, bill, request.enabled)}


@app.get("/api/v1/accounts/{account_id}/bills")
def list_bills(account_id: int, user_id: int = Depends(current_user_id)) -> list[dict]:
    if store.get_account(account_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return [_item_response(record) for record in store.list_items(account_id, "bill")]


@app.put("/api/v1/accounts/{account_id}/bills/{item_id}")
def update_bill(account_id: int, item_id: int, request: BillRequest, user_id: int = Depends(current_user_id)) -> dict[str, int]:
    if store.get_account(account_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Account not found")
    item = Bill(request.name, request.amount, _recurrence(request.recurrence), request.flexibility, request.variance_pct, request.window_start, request.window_end)
    if not store.update_bill(account_id, item_id, item, request.enabled):
        raise HTTPException(status_code=404, detail="Bill not found")
    return {"id": item_id}


@app.delete("/api/v1/accounts/{account_id}/bills/{item_id}", status_code=204)
def delete_bill(account_id: int, item_id: int, user_id: int = Depends(current_user_id)) -> None:
    if store.get_account(account_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if not store.delete_item(account_id, item_id, "bill"):
        raise HTTPException(status_code=404, detail="Bill not found")


@app.patch("/api/v1/accounts/{account_id}/bills/{item_id}/enabled")
def set_bill_enabled(account_id: int, item_id: int, request: EnabledRequest, user_id: int = Depends(current_user_id)) -> dict[str, int | bool]:
    if store.get_account(account_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if not store.set_item_enabled(account_id, item_id, "bill", request.enabled):
        raise HTTPException(status_code=404, detail="Bill not found")
    return {"id": item_id, "enabled": request.enabled}


@app.post("/api/v1/accounts/{account_id}/overrides", response_model=dict[str, int])
def create_override(account_id: int, request: OverrideRequest, user_id: int = Depends(current_user_id)) -> dict[str, int]:
    if store.get_account(account_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Account not found")
    item_id = request.item_id or request.bill_id
    if item_id is None:
        raise HTTPException(status_code=422, detail="item_id or bill_id is required")
    try:
        override_id = store.create_override(account_id, item_id, request.occurrence_date, request.new_date)
    except (sqlite3.IntegrityError, IntegrityError) as error:
        raise HTTPException(status_code=409, detail="Override already exists for this bill occurrence") from error
    if override_id is None:
        raise HTTPException(status_code=404, detail="Bill not found")
    return {"id": override_id}


@app.get("/api/v1/accounts/{account_id}/overrides", response_model=list[OverrideResponse])
def list_overrides(account_id: int, user_id: int = Depends(current_user_id)) -> list[dict]:
    if store.get_account(account_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return store.list_overrides(account_id)


@app.delete("/api/v1/accounts/{account_id}/overrides/{override_id}", status_code=204)
def delete_override(account_id: int, override_id: int, user_id: int = Depends(current_user_id)) -> None:
    if store.get_account(account_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if not store.delete_override(account_id, override_id):
        raise HTTPException(status_code=404, detail="Override not found")


def _projection_response(account: Account, incomes: list[IncomeSource], bills: list[Bill], horizon_days: int, overrides=()) -> list[ProjectedDayResponse]:
    series = project(account, incomes, bills, horizon_days, overrides)
    return [
        ProjectedDayResponse(
            date=day.date,
            opening_balance=day.opening_balance,
            events=[EventResponse(name=event.name, amount=event.amount, source_date=event.source_date, posted_date=event.posted_date, kind=event.kind.value) for event in day.events],
            closing_balance=day.closing_balance,
        )
        for day in series
    ]


@app.get("/api/v1/accounts/{account_id}/projection", response_model=list[ProjectedDayResponse])
def saved_projection(account_id: int, horizon_days: int = 90, user_id: int = Depends(current_user_id)) -> list[ProjectedDayResponse]:
    account = store.get_account(account_id, user_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if horizon_days < 1 or horizon_days > 3660:
        raise HTTPException(status_code=422, detail="horizon_days must be between 1 and 3660")
    return _projection_response(account, store.get_items(account_id, "income"), store.get_items(account_id, "bill"), horizon_days, store.get_core_overrides(account_id))


def _optimization_response(result: OptimizationResult) -> OptimizationResponse:
    return OptimizationResponse(
        moves=[BillMoveResponse(bill_name=move.bill_name, original_date=move.original_date, new_date=move.new_date) for move in result.moves],
        before_min_balance=result.before_min_balance,
        after_min_balance=result.after_min_balance,
        before_negative_days=result.before_negative_days,
        after_negative_days=result.after_negative_days,
        recommendation=result.recommendation,
    )


@app.get("/api/v1/accounts/{account_id}/optimization", response_model=OptimizationResponse)
def saved_optimization(account_id: int, horizon_days: int = 90, user_id: int = Depends(current_user_id)) -> OptimizationResponse:
    account = store.get_account(account_id, user_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if horizon_days < 1 or horizon_days > 3660:
        raise HTTPException(status_code=422, detail="horizon_days must be between 1 and 3660")
    result = optimize_schedule(account, store.get_items(account_id, "income"), store.get_items(account_id, "bill"), horizon_days, store.get_core_overrides(account_id))
    return _optimization_response(result)


@app.post("/api/v1/projection", response_model=list[ProjectedDayResponse])
def projection(request: ProjectionRequest) -> list[ProjectedDayResponse]:
    account = Account(request.account.starting_balance, request.account.as_of)
    incomes = [IncomeSource(item.name, item.amount, _recurrence(item.recurrence), item.variance_pct) for item in request.incomes]
    bills = [
        Bill(
            item.name,
            item.amount,
            _recurrence(item.recurrence),
            item.flexibility,
            item.variance_pct,
            item.window_start,
            item.window_end,
        )
        for item in request.bills
    ]
    return _projection_response(account, incomes, bills, request.horizon_days)
