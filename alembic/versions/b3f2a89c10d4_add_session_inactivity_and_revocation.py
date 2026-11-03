"""add_session_inactivity_and_revocation

Revision ID: b3f2a89c10d4
Revises: aa79f2e749d9
Create Date: 2026-10-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f2a89c10d4'

down_revision: Union[str, None] = 'aa79f2e749d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add lastActivity, isRevoked and refreshTokenHash to session table
    op.add_column(
        'session',
        sa.Column('lastActivity', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'))
    )
    op.add_column(
        'session',
        sa.Column('isRevoked', sa.Boolean(), nullable=False, server_default=sa.text('false'))
    )
    op.add_column(
        'session',
        sa.Column('refreshTokenHash', sa.String(length=255), nullable=True)
    )
    op.create_index(
        op.f('ix_session_refreshTokenHash'),
        'session',
        ['refreshTokenHash'],
        unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_session_refreshTokenHash'), table_name='session')
    op.drop_column('session', 'refreshTokenHash')
    op.drop_column('session', 'isRevoked')
    op.drop_column('session', 'lastActivity')
