"""change user.password type from varchar to Text

Revision ID: c9accdc85091
Revises: 
Create Date: 2026-08-25 12:11:18.530859

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9accdc85091'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "password", existing_type=sa.String(length=80), type_=sa.Text(), existing_nullable=False)
    pass


def downgrade() -> None:
    op.alter_column("users", "password", existing_type=sa.Text(), type_=sa.String(length=80), existing_nullable=False)
    pass
