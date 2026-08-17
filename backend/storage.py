import sqlite3
from datetime import date
from dataclasses import dataclass
from decimal import Decimal

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
    def __init__(self, path: str | None = None):
        self.path = path or Settings.from_environment().database_path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    starting_balance TEXT NOT NULL,
                    as_of TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                    kind TEXT NOT NULL CHECK(kind IN ('income', 'bill')),
                    name TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    variance_pct TEXT NOT NULL,
                    recurrence_kind TEXT NOT NULL,
                    recurrence_anchor TEXT NOT NULL,
                    day_of_month INTEGER,
                    second_day_of_month INTEGER,
                    flexibility TEXT,
                    window_start INTEGER,
                    window_end INTEGER,
                    enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0, 1))
                );
                CREATE TABLE IF NOT EXISTS overrides (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                    item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
                    occurrence_date TEXT NOT NULL,
                    new_date TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(account_id, item_id, occurrence_date)
                );
                """
            )
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(items)")}
            if "enabled" not in columns:
                connection.execute("ALTER TABLE items ADD COLUMN enabled INTEGER NOT NULL DEFAULT 1")
            account_columns = {row["name"] for row in connection.execute("PRAGMA table_info(accounts)")}
            if "user_id" not in account_columns:
                connection.execute("ALTER TABLE accounts ADD COLUMN user_id INTEGER")

    def check_ready(self) -> None:
        self._initialize()
        with self._connect() as connection:
            connection.execute("SELECT 1").fetchone()

    def create_user(self, email: str, password_hash: str) -> int:
        with self._connect() as connection:
            cursor = connection.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", (email, password_hash))
            return int(cursor.lastrowid)

    def get_user_by_email(self, email: str) -> sqlite3.Row | None:
        with self._connect() as connection:
            return connection.execute("SELECT id, email, password_hash FROM users WHERE email = ?", (email,)).fetchone()

    def create_account(self, account: Account, user_id: int | None = None) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO accounts (user_id, starting_balance, as_of) VALUES (?, ?, ?)",
                (user_id, str(account.starting_balance), account.as_of.isoformat()),
            )
            return int(cursor.lastrowid)

    def get_account(self, account_id: int, user_id: int | None = None) -> Account | None:
        with self._connect() as connection:
            query = "SELECT starting_balance, as_of FROM accounts WHERE id = ?"
            params: tuple = (account_id,)
            if user_id is not None:
                query += " AND user_id = ?"
                params += (user_id,)
            row = connection.execute(query, params).fetchone()
        if row is None:
            return None
        return Account(Decimal(row["starting_balance"]), date.fromisoformat(row["as_of"]))

    def create_income(self, account_id: int, income: IncomeSource, enabled: bool = True) -> int:
        return self._create_item(account_id, "income", income.name, income.amount, income.variance_pct, income.recurrence, None, enabled)

    def create_bill(self, account_id: int, bill: Bill, enabled: bool = True) -> int:
        return self._create_item(account_id, "bill", bill.name, bill.amount, bill.variance_pct, bill.recurrence, bill, enabled)

    def _create_item(self, account_id: int, kind: str, name: str, amount: Decimal, variance_pct: Decimal, recurrence: RecurrenceRule, bill: Bill | None, enabled: bool) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """INSERT INTO items (
                    account_id, kind, name, amount, variance_pct, recurrence_kind,
                    recurrence_anchor, day_of_month, second_day_of_month,
                    flexibility, window_start, window_end, enabled
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    account_id,
                    kind,
                    name,
                    str(amount),
                    str(variance_pct),
                    recurrence.kind.value,
                    recurrence.anchor.isoformat(),
                    recurrence.day_of_month,
                    recurrence.second_day_of_month,
                    bill.flexibility.value if bill else None,
                    bill.window_start if bill else None,
                    bill.window_end if bill else None,
                    int(enabled),
                ),
            )
            return int(cursor.lastrowid)

    def get_items(self, account_id: int, kind: str) -> list[IncomeSource] | list[Bill]:
        return [record.item for record in self.list_items(account_id, kind) if record.enabled]

    def list_items(self, account_id: int, kind: str) -> list[ItemRecord]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM items WHERE account_id = ? AND kind = ? ORDER BY id", (account_id, kind)).fetchall()
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
    def _recurrence_from_row(row: sqlite3.Row) -> RecurrenceRule:
        return RecurrenceRule(RecurrenceType(row["recurrence_kind"]), date.fromisoformat(row["recurrence_anchor"]), row["day_of_month"], row["second_day_of_month"])

    def update_income(self, account_id: int, item_id: int, income: IncomeSource, enabled: bool = True) -> bool:
        return self._update_item(account_id, item_id, "income", income.name, income.amount, income.variance_pct, income.recurrence, None, enabled)

    def update_bill(self, account_id: int, item_id: int, bill: Bill, enabled: bool = True) -> bool:
        return self._update_item(account_id, item_id, "bill", bill.name, bill.amount, bill.variance_pct, bill.recurrence, bill, enabled)

    def _update_item(self, account_id: int, item_id: int, kind: str, name: str, amount: Decimal, variance_pct: Decimal, recurrence: RecurrenceRule, bill: Bill | None, enabled: bool) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """UPDATE items SET name = ?, amount = ?, variance_pct = ?, recurrence_kind = ?,
                    recurrence_anchor = ?, day_of_month = ?, second_day_of_month = ?, flexibility = ?,
                    window_start = ?, window_end = ?, enabled = ? WHERE id = ? AND account_id = ? AND kind = ?""",
                (name, str(amount), str(variance_pct), recurrence.kind.value, recurrence.anchor.isoformat(), recurrence.day_of_month, recurrence.second_day_of_month, bill.flexibility.value if bill else None, bill.window_start if bill else None, bill.window_end if bill else None, int(enabled), item_id, account_id, kind),
            )
            return cursor.rowcount == 1

    def set_item_enabled(self, account_id: int, item_id: int, kind: str, enabled: bool) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE items SET enabled = ? WHERE id = ? AND account_id = ? AND kind = ?",
                (int(enabled), item_id, account_id, kind),
            )
            return cursor.rowcount == 1

    def delete_item(self, account_id: int, item_id: int, kind: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM items WHERE id = ? AND account_id = ? AND kind = ?", (item_id, account_id, kind))
            return cursor.rowcount == 1

    def create_override(self, account_id: int, item_id: int, occurrence_date: date, new_date: date) -> int | None:
        with self._connect() as connection:
            item = connection.execute(
                "SELECT id FROM items WHERE id = ? AND account_id = ? AND kind = 'bill'",
                (item_id, account_id),
            ).fetchone()
            if item is None:
                return None
            cursor = connection.execute(
                "INSERT INTO overrides (account_id, item_id, occurrence_date, new_date) VALUES (?, ?, ?, ?)",
                (account_id, item_id, occurrence_date.isoformat(), new_date.isoformat()),
            )
            return int(cursor.lastrowid)

    def list_overrides(self, account_id: int) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT overrides.id, overrides.item_id, items.name, overrides.occurrence_date,
                          overrides.new_date, overrides.created_at
                   FROM overrides JOIN items ON items.id = overrides.item_id
                   WHERE overrides.account_id = ? ORDER BY overrides.id""",
                (account_id,),
            ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "item_id": int(row["item_id"]),
                "bill_name": row["name"],
                "occurrence_date": date.fromisoformat(row["occurrence_date"]),
                "new_date": date.fromisoformat(row["new_date"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def get_core_overrides(self, account_id: int) -> tuple[BillOccurrenceOverride, ...]:
        return tuple(
            BillOccurrenceOverride(item["bill_name"], item["occurrence_date"], item["new_date"], item["item_id"])
            for item in self.list_overrides(account_id)
        )

    def delete_override(self, account_id: int, override_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM overrides WHERE id = ? AND account_id = ?", (override_id, account_id))
            return cursor.rowcount == 1
