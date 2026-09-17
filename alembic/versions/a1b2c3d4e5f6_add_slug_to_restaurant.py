"""add slug column to restaurant table

Revision ID: a1b2c3d4e5f6
Revises: 5d168195c2c2
Create Date: 2026-09-17 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '5d168195c2c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('restaurant', sa.Column('slug', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_restaurant_slug'), 'restaurant', ['slug'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_restaurant_slug'), table_name='restaurant')
    op.drop_column('restaurant', 'slug')
