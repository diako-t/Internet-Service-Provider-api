"""change some Columns in orders and transactions tables

Revision ID: 4e7b61363cc1
Revises: c9accdc85091
Create Date: 2026-08-30 20:43:53.448724

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e7b61363cc1'
down_revision: Union[str, Sequence[str], None] = 'c9accdc85091'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("total_amount", sa.Numeric(10, 2), nullable=False))
    op.alter_column("transactions", "payment_time", existing_type=sa.TIMESTAMP(timezone=True), nullable=True, server_default=None)
    op.alter_column("transactions", "track_code", existing_type=sa.String(length=100), nullable=True)
    op.drop_constraint("order_items_plan_id_fkey", "order_items", type_="foreignkey")
    op.create_foreign_key("order_items_plan_id_fkey", "order_items", "plans", ["plan_id"], ["id"])
    op.drop_constraint("subscriptions_item_id_fkey", "subscriptions", type_="foreignkey")
    op.create_foreign_key("subscriptions_item_id_fkey", "subscriptions","order_items" , ["item_id"], ["id"])


def downgrade() -> None:
    op.drop_column("orders", "total_amount")
    op.alter_column("transactions", "payment_time", existing_type=sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()"))
    op.alter_column("transactions", "track_code", existing_comment=sa.String(length=100), nullable=False)
    op.drop_constraint("order_items_plan_id_fkey", "order_items", type_="foreignkey")
    op.create_foreign_key("order_items_plan_id_fkey", "order_items", "plans", ["plan_id"], ["id"], ondelete="CASCADE")
    op.drop_constraint("subscriptions_item_id_fkey", "subscriptions", type_="foreignkey")
    op.create_foreign_key("subscriptions_item_id_fkey", "subscriptions","order_items" , ["item_id"], ["id"], ondelete="CASCADE")