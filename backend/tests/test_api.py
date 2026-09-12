from fastapi.testclient import TestClient
import sqlite3

import backend.api as api
from backend.api import app
from backend.auth import create_access_token
from backend.storage import ScenarioStore


class AuthenticatedClient:
    def __init__(self, wrapped):
        self.wrapped = wrapped
        self.headers = {"Authorization": f"Bearer {create_access_token(1, api.settings.auth_secret)}"}

    def __getattr__(self, name):
        method = getattr(self.wrapped, name)
        if name not in {"get", "post", "put", "patch", "delete"}:
            return method

        def authenticated_request(*args, **kwargs):
            headers = {**self.headers, **kwargs.pop("headers", {})}
            return method(*args, headers=headers, **kwargs)

        return authenticated_request


client = AuthenticatedClient(TestClient(app))


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_request_id_is_propagated_and_logged_without_secrets(caplog):
    request_id = "test-request-123"
    token = "Bearer secret-token-value"

    with caplog.at_level("INFO", logger="cashflow.api"):
        response = client.get("/health", headers={"X-Request-ID": request_id, "Authorization": token})

    assert response.headers["X-Request-ID"] == request_id
    assert f"request_id={request_id}" in caplog.text
    assert token not in caplog.text
    assert "method=GET" in caplog.text
    assert "path=/health" in caplog.text
    assert "status=200" in caplog.text


def test_request_id_is_generated_when_missing():
    response = client.get("/health")

    assert response.headers["X-Request-ID"]
    assert len(response.headers["X-Request-ID"]) == 36


def test_ready_endpoint_checks_database(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "store", ScenarioStore(str(tmp_path / "ready.sqlite")))

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}

    broken_store = ScenarioStore(str(tmp_path / "broken.sqlite"))
    broken_store.path = str(tmp_path / "missing" / "ready.sqlite")
    monkeypatch.setattr(api, "store", broken_store)
    assert client.get("/ready").status_code == 503


def test_cors_uses_explicit_origin_without_credentials():
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-credentials" not in response.headers


def test_projection_endpoint_returns_daily_results():
    response = client.post(
        "/api/v1/projection",
        json={
            "account": {"starting_balance": "100.00", "as_of": "2025-06-13"},
            "incomes": [
                {
                    "name": "Paycheck",
                    "amount": "500.00",
                    "recurrence": {"kind": "ONCE", "anchor": "2025-06-14"},
                }
            ],
            "bills": [
                {
                    "name": "Rent",
                    "amount": "200.00",
                    "recurrence": {"kind": "ONCE", "anchor": "2025-06-16"},
                    "flexibility": "FIXED",
                }
            ],
            "horizon_days": 5,
        },
    )
    assert response.status_code == 200
    days = response.json()
    assert len(days) == 5
    assert days[0]["closing_balance"] == "600.00"
    assert days[3]["closing_balance"] == "400.00"
    assert days[0]["events"][0]["kind"] == "income"


def test_projection_endpoint_rejects_invalid_amounts_and_horizons():
    response = client.post(
        "/api/v1/projection",
        json={
            "account": {"starting_balance": "100.00", "as_of": "2025-06-13"},
            "bills": [
                {
                    "name": "Rent",
                    "amount": "-1.00",
                    "recurrence": {"kind": "ONCE", "anchor": "2025-06-16"},
                    "flexibility": "FIXED",
                }
            ],
            "horizon_days": 0,
        },
    )
    assert response.status_code == 422


def test_saved_account_projection_reads_persisted_schedule(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "store", ScenarioStore(str(tmp_path / "cashflow.sqlite")))
    account_response = client.post("/api/v1/accounts", json={"starting_balance": "100.00", "as_of": "2025-06-13"})
    account_id = account_response.json()["id"]
    income_response = client.post(
        f"/api/v1/accounts/{account_id}/incomes",
        json={
            "name": "Paycheck",
            "amount": "500.00",
            "recurrence": {"kind": "ONCE", "anchor": "2025-06-14"},
        },
    )
    assert income_response.status_code == 200
    bill_response = client.post(
        f"/api/v1/accounts/{account_id}/bills",
        json={
            "name": "Rent",
            "amount": "200.00",
            "recurrence": {"kind": "ONCE", "anchor": "2025-06-16"},
            "flexibility": "FIXED",
        },
    )
    assert bill_response.status_code == 200
    projection_response = client.get(f"/api/v1/accounts/{account_id}/projection?horizon_days=5")
    assert projection_response.status_code == 200
    assert projection_response.json()[3]["closing_balance"] == "400.00"


def test_saved_account_optimization_returns_recommendation(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "store", ScenarioStore(str(tmp_path / "optimization.sqlite")))
    account_id = client.post("/api/v1/accounts", json={"starting_balance": "50.00", "as_of": "2025-06-02"}).json()["id"]
    client.post(
        f"/api/v1/accounts/{account_id}/incomes",
        json={"name": "Paycheck", "amount": "100.00", "recurrence": {"kind": "ONCE", "anchor": "2025-06-05"}},
    )
    client.post(
        f"/api/v1/accounts/{account_id}/bills",
        json={
            "name": "Card payment",
            "amount": "100.00",
            "recurrence": {"kind": "ONCE", "anchor": "2025-06-03"},
            "flexibility": "WINDOW",
            "window_start": 3,
            "window_end": 5,
        },
    )

    response = client.get(f"/api/v1/accounts/{account_id}/optimization?horizon_days=5")

    assert response.status_code == 200
    body = response.json()
    assert body["moves"] == [{"bill_name": "Card payment", "original_date": "2025-06-03", "new_date": "2025-06-05"}]
    assert body["before_min_balance"] == "-50.00"
    assert body["after_min_balance"] == "50.00"
    assert body["before_negative_days"] == 2
    assert body["after_negative_days"] == 0
    assert "Recommendation:" in body["recommendation"]


def test_saved_account_optimization_rejects_missing_account_and_invalid_horizon(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "store", ScenarioStore(str(tmp_path / "optimization-errors.sqlite")))

    missing_account = client.get("/api/v1/accounts/999/optimization")
    assert missing_account.status_code == 404

    account_id = client.post("/api/v1/accounts", json={"starting_balance": "0.00", "as_of": "2025-06-02"}).json()["id"]
    invalid_horizon = client.get(f"/api/v1/accounts/{account_id}/optimization?horizon_days=3661")
    assert invalid_horizon.status_code == 422


def test_saved_items_can_be_listed_updated_and_deleted(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "store", ScenarioStore(str(tmp_path / "crud.sqlite")))
    account_id = client.post("/api/v1/accounts", json={"starting_balance": "100.00", "as_of": "2025-06-13"}).json()["id"]
    item_id = client.post(
        f"/api/v1/accounts/{account_id}/bills",
        json={"name": "Internet", "amount": "80.00", "recurrence": {"kind": "MONTHLY", "anchor": "2025-06-18"}, "flexibility": "FLEXIBLE"},
    ).json()["id"]
    listed = client.get(f"/api/v1/accounts/{account_id}/bills")
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == item_id
    updated = client.put(
        f"/api/v1/accounts/{account_id}/bills/{item_id}",
        json={"name": "Internet", "amount": "90.00", "recurrence": {"kind": "MONTHLY", "anchor": "2025-06-18"}, "flexibility": "WINDOW", "window_start": 18, "window_end": 22},
    )
    assert updated.status_code == 200
    assert client.get(f"/api/v1/accounts/{account_id}/bills").json()[0]["amount"] == "90.00"
    deleted = client.delete(f"/api/v1/accounts/{account_id}/bills/{item_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/accounts/{account_id}/bills").json() == []


def test_override_apply_changes_projection_and_delete_restores_it(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "store", ScenarioStore(str(tmp_path / "overrides.sqlite")))
    account_id = client.post("/api/v1/accounts", json={"starting_balance": "50.00", "as_of": "2025-06-02"}).json()["id"]
    client.post(
        f"/api/v1/accounts/{account_id}/incomes",
        json={"name": "Paycheck", "amount": "100.00", "recurrence": {"kind": "ONCE", "anchor": "2025-06-05"}},
    )
    bill_id = client.post(
        f"/api/v1/accounts/{account_id}/bills",
        json={
            "name": "Card payment",
            "amount": "100.00",
            "recurrence": {"kind": "ONCE", "anchor": "2025-06-03"},
            "flexibility": "WINDOW",
            "window_start": 3,
            "window_end": 5,
        },
    ).json()["id"]

    baseline = client.get(f"/api/v1/accounts/{account_id}/projection?horizon_days=5").json()
    assert baseline[1]["closing_balance"] == "-50.00"
    recommendation = client.get(f"/api/v1/accounts/{account_id}/optimization?horizon_days=5").json()
    move = recommendation["moves"][0]

    applied = client.post(
        f"/api/v1/accounts/{account_id}/overrides",
        json={"bill_id": bill_id, "occurrence_date": move["original_date"], "new_date": move["new_date"]},
    )
    assert applied.status_code == 200
    override_id = applied.json()["id"]
    changed = client.get(f"/api/v1/accounts/{account_id}/projection?horizon_days=5").json()
    assert changed[1]["closing_balance"] == "50.00"
    assert client.get(f"/api/v1/accounts/{account_id}/bills").json()[0]["recurrence"]["anchor"] == "2025-06-03"
    assert client.get(f"/api/v1/accounts/{account_id}/overrides").json()[0]["item_id"] == bill_id

    assert client.delete(f"/api/v1/accounts/{account_id}/overrides/{override_id}").status_code == 204
    restored = client.get(f"/api/v1/accounts/{account_id}/projection?horizon_days=5").json()
    assert restored[1]["closing_balance"] == baseline[1]["closing_balance"]
    assert client.get(f"/api/v1/accounts/{account_id}/overrides").json() == []


def test_overrides_are_account_scoped_and_missing_resources_are_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "store", ScenarioStore(str(tmp_path / "override-scope.sqlite")))
    first_account = client.post("/api/v1/accounts", json={"starting_balance": "0.00", "as_of": "2025-06-02"}).json()["id"]
    second_account = client.post("/api/v1/accounts", json={"starting_balance": "0.00", "as_of": "2025-06-02"}).json()["id"]
    bill_id = client.post(
        f"/api/v1/accounts/{first_account}/bills",
        json={"name": "Rent", "amount": "100.00", "recurrence": {"kind": "ONCE", "anchor": "2025-06-03"}, "flexibility": "WINDOW", "window_start": 3, "window_end": 5},
    ).json()["id"]

    assert client.post(
        f"/api/v1/accounts/{second_account}/overrides",
        json={"item_id": bill_id, "occurrence_date": "2025-06-03", "new_date": "2025-06-04"},
    ).status_code == 404
    assert client.get(f"/api/v1/accounts/{second_account}/overrides").json() == []
    assert client.delete(f"/api/v1/accounts/{second_account}/overrides/1").status_code == 404
    assert client.get("/api/v1/accounts/999/overrides").status_code == 404


def test_disabling_and_reenabling_income_and_bill_changes_saved_projection(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "store", ScenarioStore(str(tmp_path / "enabled.sqlite")))
    account_id = client.post("/api/v1/accounts", json={"starting_balance": "100.00", "as_of": "2025-06-13"}).json()["id"]
    income_id = client.post(
        f"/api/v1/accounts/{account_id}/incomes",
        json={"name": "Paycheck", "amount": "50.00", "recurrence": {"kind": "ONCE", "anchor": "2025-06-14"}},
    ).json()["id"]
    bill_id = client.post(
        f"/api/v1/accounts/{account_id}/bills",
        json={"name": "Rent", "amount": "30.00", "recurrence": {"kind": "ONCE", "anchor": "2025-06-16"}, "flexibility": "FIXED"},
    ).json()["id"]

    baseline = client.get(f"/api/v1/accounts/{account_id}/projection?horizon_days=4").json()
    assert baseline[1]["closing_balance"] == "150.00"
    assert baseline[3]["closing_balance"] == "120.00"

    disabled_bill = client.patch(f"/api/v1/accounts/{account_id}/bills/{bill_id}/enabled", json={"enabled": False})
    assert disabled_bill.status_code == 200
    assert disabled_bill.json() == {"id": bill_id, "enabled": False}
    without_bill = client.get(f"/api/v1/accounts/{account_id}/projection?horizon_days=4").json()
    assert without_bill[3]["closing_balance"] == "150.00"

    disabled_income = client.patch(f"/api/v1/accounts/{account_id}/incomes/{income_id}/enabled", json={"enabled": False})
    assert disabled_income.status_code == 200
    without_income_or_bill = client.get(f"/api/v1/accounts/{account_id}/projection?horizon_days=4").json()
    assert without_income_or_bill[1]["closing_balance"] == "100.00"
    assert without_income_or_bill[3]["closing_balance"] == "100.00"

    assert client.patch(f"/api/v1/accounts/{account_id}/incomes/{income_id}/enabled", json={"enabled": True}).status_code == 200
    assert client.patch(f"/api/v1/accounts/{account_id}/bills/{bill_id}/enabled", json={"enabled": True}).status_code == 200
    restored = client.get(f"/api/v1/accounts/{account_id}/projection?horizon_days=4").json()
    assert restored[1]["closing_balance"] == baseline[1]["closing_balance"]
    assert restored[2]["closing_balance"] == baseline[2]["closing_balance"]

    listed_incomes = client.get(f"/api/v1/accounts/{account_id}/incomes").json()
    listed_bills = client.get(f"/api/v1/accounts/{account_id}/bills").json()
    assert listed_incomes[0]["item_id"] == income_id
    assert listed_incomes[0]["enabled"] is True
    assert listed_bills[0]["item_id"] == bill_id
    assert listed_bills[0]["enabled"] is True


def test_enabled_state_is_account_scoped_and_legacy_items_default_enabled(tmp_path):
    database_path = tmp_path / "legacy.sqlite"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, starting_balance TEXT NOT NULL, as_of TEXT NOT NULL);
            CREATE TABLE items (
                id INTEGER PRIMARY KEY AUTOINCREMENT, account_id INTEGER NOT NULL, kind TEXT NOT NULL,
                name TEXT NOT NULL, amount TEXT NOT NULL, variance_pct TEXT NOT NULL,
                recurrence_kind TEXT NOT NULL, recurrence_anchor TEXT NOT NULL,
                day_of_month INTEGER, second_day_of_month INTEGER, flexibility TEXT,
                window_start INTEGER, window_end INTEGER
            );
            INSERT INTO accounts (starting_balance, as_of) VALUES ('0.00', '2025-06-13');
            INSERT INTO items (account_id, kind, name, amount, variance_pct, recurrence_kind, recurrence_anchor, flexibility)
            VALUES (1, 'income', 'Legacy income', '10.00', '0', 'ONCE', '2025-06-14', NULL);
            """
        )

    store = ScenarioStore(str(database_path))
    record = store.list_items(1, "income")[0]
    assert record.item_id == 1
    assert record.enabled is True
    assert store.get_items(1, "income")[0].name == "Legacy income"


def test_account_export_returns_account_items_and_overrides_shape(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "store", ScenarioStore(str(tmp_path / "account-export.sqlite")))
    account_id = client.post("/api/v1/accounts", json={"starting_balance": "250.00", "as_of": "2025-06-01"}).json()["id"]
    income_id = client.post(
        f"/api/v1/accounts/{account_id}/incomes",
        json={
            "name": "Payroll",
            "amount": "1000.00",
            "recurrence": {"kind": "MONTHLY", "anchor": "2025-06-01", "day_of_month": 1},
            "enabled": False,
        },
    ).json()["id"]
    bill_id = client.post(
        f"/api/v1/accounts/{account_id}/bills",
        json={
            "name": "Rent",
            "amount": "750.00",
            "recurrence": {"kind": "MONTHLY", "anchor": "2025-06-03", "day_of_month": 3},
            "flexibility": "WINDOW",
            "window_start": 1,
            "window_end": 5,
        },
    ).json()["id"]
    override_id = client.post(
        f"/api/v1/accounts/{account_id}/overrides",
        json={"item_id": bill_id, "occurrence_date": "2025-07-03", "new_date": "2025-07-04"},
    ).json()["id"]

    response = client.get(f"/api/v1/accounts/{account_id}/export")

    assert response.status_code == 200
    payload = response.json()
    assert payload["account"] == {"id": account_id, "starting_balance": "250.00", "as_of": "2025-06-01"}
    assert len(payload["incomes"]) == 1
    assert payload["incomes"][0]["item_id"] == income_id
    assert payload["incomes"][0]["enabled"] is False
    assert payload["incomes"][0]["recurrence"]["day_of_month"] == 1
    assert len(payload["bills"]) == 1
    assert payload["bills"][0]["item_id"] == bill_id
    assert payload["bills"][0]["flexibility"] == "WINDOW"
    assert payload["bills"][0]["window_start"] == 1
    assert payload["bills"][0]["window_end"] == 5
    assert payload["overrides"] == [
        {
            "id": override_id,
            "item_id": bill_id,
            "bill_name": "Rent",
            "occurrence_date": "2025-07-03",
            "new_date": "2025-07-04",
            "created_at": payload["overrides"][0]["created_at"],
        }
    ]


def test_account_export_and_delete_enforce_auth_and_ownership(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "store", ScenarioStore(str(tmp_path / "account-authz.sqlite")))
    account_id = client.post("/api/v1/accounts", json={"starting_balance": "10.00", "as_of": "2025-06-01"}).json()["id"]
    other_user_headers = {"Authorization": f"Bearer {create_access_token(2, api.settings.auth_secret)}"}

    unauthenticated_export = TestClient(app).get(f"/api/v1/accounts/{account_id}/export")
    assert unauthenticated_export.status_code == 401
    assert unauthenticated_export.headers["www-authenticate"] == "Bearer"

    unauthorized_export = client.get(f"/api/v1/accounts/{account_id}/export", headers=other_user_headers)
    assert unauthorized_export.status_code == 404

    unauthorized_delete = client.delete(f"/api/v1/accounts/{account_id}", headers=other_user_headers)
    assert unauthorized_delete.status_code == 404


def test_account_delete_cascades_owned_data_and_persists(tmp_path, monkeypatch):
    db_path = tmp_path / "account-delete.sqlite"
    monkeypatch.setattr(api, "store", ScenarioStore(str(db_path)))

    account_id = client.post("/api/v1/accounts", json={"starting_balance": "100.00", "as_of": "2025-06-01"}).json()["id"]
    retained_account_id = client.post("/api/v1/accounts", json={"starting_balance": "5.00", "as_of": "2025-06-01"}).json()["id"]
    income_id = client.post(
        f"/api/v1/accounts/{account_id}/incomes",
        json={"name": "Pay", "amount": "500.00", "recurrence": {"kind": "ONCE", "anchor": "2025-06-02"}},
    ).json()["id"]
    bill_id = client.post(
        f"/api/v1/accounts/{account_id}/bills",
        json={"name": "Rent", "amount": "200.00", "recurrence": {"kind": "ONCE", "anchor": "2025-06-03"}, "flexibility": "FIXED"},
    ).json()["id"]
    client.post(
        f"/api/v1/accounts/{retained_account_id}/bills",
        json={"name": "Phone", "amount": "30.00", "recurrence": {"kind": "ONCE", "anchor": "2025-06-04"}, "flexibility": "FIXED"},
    )
    override_id = client.post(
        f"/api/v1/accounts/{account_id}/overrides",
        json={"item_id": bill_id, "occurrence_date": "2025-06-03", "new_date": "2025-06-04"},
    ).json()["id"]

    with sqlite3.connect(db_path) as connection:
        items_before = connection.execute("SELECT COUNT(*) FROM items WHERE id IN (?, ?)", (income_id, bill_id)).fetchone()[0]
        overrides_before = connection.execute("SELECT COUNT(*) FROM overrides WHERE id = ?", (override_id,)).fetchone()[0]
    assert items_before == 2
    assert overrides_before == 1

    deleted = client.delete(f"/api/v1/accounts/{account_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/accounts/{account_id}/export").status_code == 404
    assert client.get(f"/api/v1/accounts/{retained_account_id}/bills").status_code == 200

    monkeypatch.setattr(api, "store", ScenarioStore(str(db_path)))
    assert client.get(f"/api/v1/accounts/{account_id}/projection").status_code == 404

    with sqlite3.connect(db_path) as connection:
        accounts_after = connection.execute("SELECT COUNT(*) FROM accounts WHERE id = ?", (account_id,)).fetchone()[0]
        items_after = connection.execute("SELECT COUNT(*) FROM items WHERE id IN (?, ?)", (income_id, bill_id)).fetchone()[0]
        overrides_after = connection.execute("SELECT COUNT(*) FROM overrides WHERE id = ?", (override_id,)).fetchone()[0]
        retained_items_after = connection.execute("SELECT COUNT(*) FROM items WHERE account_id = ?", (retained_account_id,)).fetchone()[0]
    assert accounts_after == 0
    assert items_after == 0
    assert overrides_after == 0
    assert retained_items_after == 1
