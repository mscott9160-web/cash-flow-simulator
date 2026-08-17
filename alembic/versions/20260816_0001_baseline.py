"""Create the initial cash-flow schema."""

from alembic import op
import sqlalchemy as sa


revision = "20260816_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.Integer(), autoincrement=True, nullable=False), sa.Column("email", sa.Text(), nullable=False), sa.Column("password_hash", sa.Text(), nullable=False), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("email"))
    op.create_table("accounts", sa.Column("id", sa.Integer(), autoincrement=True, nullable=False), sa.Column("user_id", sa.Integer(), nullable=True), sa.Column("starting_balance", sa.Text(), nullable=False), sa.Column("as_of", sa.Text(), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_table("items", sa.Column("id", sa.Integer(), autoincrement=True, nullable=False), sa.Column("account_id", sa.Integer(), nullable=False), sa.Column("kind", sa.Text(), nullable=False), sa.Column("name", sa.Text(), nullable=False), sa.Column("amount", sa.Text(), nullable=False), sa.Column("variance_pct", sa.Text(), nullable=False), sa.Column("recurrence_kind", sa.Text(), nullable=False), sa.Column("recurrence_anchor", sa.Text(), nullable=False), sa.Column("day_of_month", sa.Integer(), nullable=True), sa.Column("second_day_of_month", sa.Integer(), nullable=True), sa.Column("flexibility", sa.Text(), nullable=True), sa.Column("window_start", sa.Integer(), nullable=True), sa.Column("window_end", sa.Integer(), nullable=True), sa.Column("enabled", sa.Integer(), nullable=False, server_default=sa.text("1")), sa.CheckConstraint("kind IN ('income', 'bill')"), sa.CheckConstraint("enabled IN (0, 1)"), sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"))
    op.create_table("overrides", sa.Column("id", sa.Integer(), autoincrement=True, nullable=False), sa.Column("account_id", sa.Integer(), nullable=False), sa.Column("item_id", sa.Integer(), nullable=False), sa.Column("occurrence_date", sa.Text(), nullable=False), sa.Column("new_date", sa.Text(), nullable=False), sa.Column("created_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")), sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("account_id", "item_id", "occurrence_date"))


def downgrade() -> None:
    op.drop_table("overrides")
    op.drop_table("items")
    op.drop_table("accounts")
    op.drop_table("users")