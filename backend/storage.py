from contextlib import contextmanager
from datetime import date
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterator, Mapping

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Connection, Engine

from .core.models import Account, Bill, BillOccurrenceOverride, Flexibility, IncomeSource, RecurrenceRule, RecurrenceType
from .settings import Settings


@dataclass(frozen=True)
class ItemRecord:
    item_id: int
    kind: str
    item: IncomeSource | Bill
    enabled: bool

    @property
    def id(self) -> int:
        return self.item_id


StoredItem = ItemRecord


class ScenarioStore:
    """Persistence adapter that keeps the API contract independent of the SQL dialect."""

    def __init__(self, path: str | None = None):
        settings = Settings.from_environment()
        self.path = path or settings.database_url or settings.database_path
        self._engine: Engine | None = None
        self._engine_url: str | None = None
        self._initialize()

    @staticmethod
    def _url_for(path: str) -> str:
        if "://" in path:
            return path
        if path == ":memory:":
            return "sqlite:///:memory:"
        return f"sqlite:///{path.replace(chr(92), '/') }"

    def _get_engine(self) -> Engine:
        url = self._url_for(self.path)
        if self._engine is None or self._engine_url != url:
            if self._engine is not None:
                self._engine.dispose()
            self._engine = create_engine(url, pool_pre_ping=True)
            self._engine_url = url
            if url.startswith("sqlite:"):
                event.listen(self._engine, "connect", self._enable_sqlite_foreign_keys)
        return self._engine

    @staticmethod
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    @contextmanager
    def _connect(self) -> Iterator[Connection]:
        with self._get_engine().begin() as connection:
            yield connection

    def _initialize(self) -> None:
        engine = self._get_engine()
        id_type = "SERIAL" if engine.dialect.name == "postgresql" else "INTEGER"
        with engine.begin() as connection:
            connection.execute(text(f"CREATE TABLE IF NOT EXISTS users (id {id_type} PRIMARY KEY, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL)"))
            connection.execute(text(f"CREATE TABLE IF NOT EXISTS accounts (id {id_type} PRIMARY KEY, user_id INTEGER, starting_balance TEXT NOT NULL, as_of TEXT NOT NULL)"))
            connection.execute(text(f"""CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY, account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                kind TEXT NOT NULL CHECK(kind IN ('income', 'bill')), name TEXT NOT NULL, amount TEXT NOT NULL,
                variance_pct TEXT NOT NULL, recurrence_kind TEXT NOT NULL, recurrence_anchor TEXT NOT NULL,
                day_of_month INTEGER, second_day_of_month INTEGER, flexibility TEXT, window_start INTEGER,
                window_end INTEGER, enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0, 1)))"""))
            connection.execute(text(f"""CREATE TABLE IF NOT EXISTS overrides (
                id INTEGER PRIMARY KEY, account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE, occurrence_date TEXT NOT NULL,
                new_date TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(account_id, item_id, occurrence_date))"""))
            if engine.dialect.name == "sqlite":
                columns = {column["name"] for column in inspect(connection).get_columns("items")}
                if "enabled" not in columns:
                    connection.execute(text("ALTER TABLE items ADD COLUMN enabled INTEGER NOT NULL DEFAULT 1"))
                account_columns = {column["name"] for column in inspect(connection).get_columns("accounts")}
                if "user_id" not in account_columns:
                    connection.execute(text("ALTER TABLE accounts ADD COLUMN user_id INTEGER"))

    def check_ready(self) -> None:
        self._initialize()
        with self._connect() as connection:
            connection.execute(text("SELECT 1")).scalar_one()

    def create_user(self, email: str, password_hash: str) -> int:
        with self._connect() as connection:
            result = connection.execute(text("INSERT INTO users (email, password_hash) VALUES (:email, :password_hash) RETURNING id"), {"email": email, "password_hash": password_hash})
            return int(result.scalar_one())

    def get_user_by_email(self, email: str) -> Mapping | None:
        with self._connect() as connection:
            return connection.execute(text("SELECT id, email, password_hash FROM users WHERE email = :email"), {"email": email}).mappings().first()

    def create_account(self, account: Account, user_id: int | None = None) -> int:
        with self._connect() as connection:
            result = connection.execute(text("INSERT INTO accounts (user_id, starting_balance, as_of) VALUES (:user_id, :starting_balance, :as_of) RETURNING id"), {"user_id": user_id, "starting_balance": str(account.starting_balance), "as_of": account.as_of.isoformat()})
            return int(result.scalar_one())

    def get_account(self, account_id: int, user_id: int | None = None) -> Account | None:
        query = "SELECT starting_balance, as_of FROM accounts WHERE id = :account_id"
        params = {"account_id": account_id}
        if user_id is not None:
            query += " AND user_id = :user_id"
            params["user_id"] = user_id
        with self._connect() as connection:
            row = connection.execute(text(query), params).mappings().first()
        return None if row is None else Account(Decimal(row["starting_balance"]), date.fromisoformat(row["as_of"]))

    def create_income(self, account_id: int, income: IncomeSource, enabled: bool = True) -> int:
        return self._create_item(account_id, "income", income.name, income.amount, income.variance_pct, income.recurrence, None, enabled)

    def create_bill(self, account_id: int, bill: Bill, enabled: bool = True) -> int:
        return self._create_item(account_id, "bill", bill.name, bill.amount, bill.variance_pct, bill.recurrence, bill, enabled)

    def _create_item(self, account_id: int, kind: str, name: str, amount: Decimal, variance_pct: Decimal, recurrence: RecurrenceRule, bill: Bill | None, enabled: bool) -> int:
        values = {"account_id": account_id, "kind": kind, "name": name, "amount": str(amount), "variance_pct": str(variance_pct), "recurrence_kind": recurrence.kind.value, "recurrence_anchor": recurrence.anchor.isoformat(), "day_of_month": recurrence.day_of_month, "second_day_of_month": recurrence.second_day_of_month, "flexibility": bill.flexibility.value if bill else None, "window_start": bill.window_start if bill else None, "window_end": bill.window_end if bill else None, "enabled": int(enabled)}
        with self._connect() as connection:
            result = connection.execute(text("""INSERT INTO items (account_id, kind, name, amount, variance_pct, recurrence_kind, recurrence_anchor, day_of_month, second_day_of_month, flexibility, window_start, window_end, enabled)
                VALUES (:account_id, :kind, :name, :amount, :variance_pct, :recurrence_kind, :recurrence_anchor, :day_of_month, :second_day_of_month, :flexibility, :window_start, :window_end, :enabled) RETURNING id"""), values)
            return int(result.scalar_one())

    def get_items(self, account_id: int, kind: str) -> list[IncomeSource] | list[Bill]:
        return [record.item for record in self.list_items(account_id, kind) if record.enabled]

    def list_items(self, account_id: int, kind: str) -> list[ItemRecord]:
        with self._connect() as connection:
            rows = connection.execute(text("SELECT * FROM items WHERE account_id = :account_id AND kind = :kind ORDER BY id"), {"account_id": account_id, "kind": kind}).mappings().all()
        result = []
        for row in rows:
            recurrence = self._recurrence_from_row(row)
            if kind == "income":
                item = IncomeSource(row["name"], Decimal(row["amount"]), recurrence, Decimal(row["variance_pct"]))
            else:
                item = Bill(row["name"], Decimal(row["amount"]), recurrence, Flexibility(row["flexibility"]), Decimal(row["variance_pct"]), row["window_start"], row["window_end"], int(row["id"]))
            result.append(ItemRecord(int(row["id"]), kind, item, bool(row["enabled"])))
        return result

    @staticmethod
    def _recurrence_from_row(row: Mapping) -> RecurrenceRule:
        return RecurrenceRule(RecurrenceType(row["recurrence_kind"]), date.fromisoformat(row["recurrence_anchor"]), row["day_of_month"], row["second_day_of_month"])

    def _update_item(self, account_id: int, item_id: int, kind: str, name: str, amount: Decimal, variance_pct: Decimal, recurrence: RecurrenceRule, bill: Bill | None, enabled: bool) -> bool:
        values = {"name": name, "amount": str(amount), "variance_pct": str(variance_pct), "recurrence_kind": recurrence.kind.value, "recurrence_anchor": recurrence.anchor.isoformat(), "day_of_month": recurrence.day_of_month, "second_day_of_month": recurrence.second_day_of_month, "flexibility": bill.flexibility.value if bill else None, "window_start": bill.window_start if bill else None, "window_end": bill.window_end if bill else None, "enabled": int(enabled), "item_id": item_id, "account_id": account_id, "kind": kind}
        with self._connect() as connection:
            result = connection.execute(text("""UPDATE items SET name = :name, amount = :amount, variance_pct = :variance_pct, recurrence_kind = :recurrence_kind, recurrence_anchor = :recurrence_anchor, day_of_month = :day_of_month, second_day_of_month = :second_day_of_month, flexibility = :flexibility, window_start = :window_start, window_end = :window_end, enabled = :enabled WHERE id = :item_id AND account_id = :account_id AND kind = :kind"""), values)
            return result.rowcount == 1

    def update_income(self, account_id: int, item_id: int, income: IncomeSource, enabled: bool = True) -> bool:
        return self._update_item(account_id, item_id, "income", income.name, income.amount, income.variance_pct, income.recurrence, None, enabled)

    def update_bill(self, account_id: int, item_id: int, bill: Bill, enabled: bool = True) -> bool:
        return self._update_item(account_id, item_id, "bill", bill.name, bill.amount, bill.variance_pct, bill.recurrence, bill, enabled)

    def set_item_enabled(self, account_id: int, item_id: int, kind: str, enabled: bool) -> bool:
        with self._connect() as connection:
            result = connection.execute(text("UPDATE items SET enabled = :enabled WHERE id = :item_id AND account_id = :account_id AND kind = :kind"), {"enabled": int(enabled), "item_id": item_id, "account_id": account_id, "kind": kind})
            return result.rowcount == 1

    def delete_item(self, account_id: int, item_id: int, kind: str) -> bool:
        with self._connect() as connection:
            result = connection.execute(text("DELETE FROM items WHERE id = :item_id AND account_id = :account_id AND kind = :kind"), {"item_id": item_id, "account_id": account_id, "kind": kind})
            return result.rowcount == 1

    def create_override(self, account_id: int, item_id: int, occurrence_date: date, new_date: date) -> int | None:
        with self._connect() as connection:
            item = connection.execute(text("SELECT id FROM items WHERE id = :item_id AND account_id = :account_id AND kind = 'bill'"), {"item_id": item_id, "account_id": account_id}).first()
            if item is None:
                return None
            result = connection.execute(text("INSERT INTO overrides (account_id, item_id, occurrence_date, new_date) VALUES (:account_id, :item_id, :occurrence_date, :new_date) RETURNING id"), {"account_id": account_id, "item_id": item_id, "occurrence_date": occurrence_date.isoformat(), "new_date": new_date.isoformat()})
            return int(result.scalar_one())

    def list_overrides(self, account_id: int) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(text("""SELECT overrides.id, overrides.item_id, items.name, overrides.occurrence_date, overrides.new_date, overrides.created_at
                FROM overrides JOIN items ON items.id = overrides.item_id WHERE overrides.account_id = :account_id ORDER BY overrides.id"""), {"account_id": account_id}).mappings().all()
        return [{"id": int(row["id"]), "item_id": int(row["item_id"]), "bill_name": row["name"], "occurrence_date": date.fromisoformat(row["occurrence_date"]), "new_date": date.fromisoformat(row["new_date"]), "created_at": row["created_at"]} for row in rows]

    def get_core_overrides(self, account_id: int) -> tuple[BillOccurrenceOverride, ...]:
        return tuple(BillOccurrenceOverride(item["bill_name"], item["occurrence_date"], item["new_date"], item["item_id"]) for item in self.list_overrides(account_id))

    def delete_override(self, account_id: int, override_id: int) -> bool:
        with self._connect() as connection:
            existing = connection.execute(text("SELECT id FROM overrides WHERE id = :override_id AND account_id = :account_id"), {"override_id": override_id, "account_id": account_id}).first()
            if existing is None:
                return False
            result = connection.execute(text("DELETE FROM overrides WHERE id = :override_id AND account_id = :account_id"), {"override_id": override_id, "account_id": account_id})
            return result.rowcount in {-1, 1}
