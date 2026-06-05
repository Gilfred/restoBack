"""add status column to restaurantactivationhistory

Revision ID: 7428b02ddf7c
Revises: 4c34912cb2de
Create Date: 2026-06-05 13:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7428b02ddf7c'
down_revision: Union[str, None] = '4c34912cb2de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create the enum type first if it doesn't exist
    status_enum = sa.Enum('PENDING', 'ACTIVATED', 'REJECTED', name='activationstatus')

    # Check if the type already exists
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        existing_types = bind.execute(sa.text("SELECT n.nspname, t.typname FROM pg_type t JOIN pg_namespace n ON t.typnamespace = n.oid WHERE t.typname = 'activationstatus'")).fetchall()
        if not existing_types:
            status_enum.create(bind)
    else:
        status_enum.create(bind)

    # Add the column
    op.add_column('restaurantactivationhistory',
        sa.Column('status', sa.Enum('PENDING', 'ACTIVATED', 'REJECTED', name='activationstatus'), nullable=False, server_default='PENDING')
    )

def downgrade() -> None:
    op.drop_column('restaurantactivationhistory', 'status')
    sa.Enum(name='activationstatus').drop(op.get_bind())
