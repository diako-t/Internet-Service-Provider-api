"""add volume feature to subscriptions

Revision ID: 92e4cf674679
Revises: 889068ab98c8
Create Date: 2026-09-01 16:51:14.638334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '92e4cf674679'
down_revision: Union[str, Sequence[str], None] = '889068ab98c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("subscriptions", sa.Column("total_traffic", sa.Numeric(precision=10, scale=2), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("subscriptions", "total_traffic")
