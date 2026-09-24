"""refactor menu boisson

Revision ID: a7b8c9d0e1f2
Revises: 5d168195c2c2
Create Date: 2026-09-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, None] = '5d168195c2c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create menuboissonfamille table
    op.create_table(
        'menuboissonfamille',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('restaurantId', sa.UUID(), nullable=False),
        sa.Column('nom', sa.String(length=255), nullable=False),
        sa.Column('createdAt', sa.DateTime(), nullable=False),
        sa.Column('updatedAt', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['restaurantId'], ['restaurant.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Create menuboissonimage table
    op.create_table(
        'menuboissonimage',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('menuBoissonFamilleId', sa.UUID(), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('createdAt', sa.DateTime(), nullable=False),
        sa.Column('updatedAt', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['menuBoissonFamilleId'], ['menuboissonfamille.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Alter menuboisson table: drop old columns and add menuBoissonFamilleId
    op.add_column('menuboisson', sa.Column('menuBoissonFamilleId', sa.UUID(), nullable=False))
    op.create_foreign_key(
        'fk_menuboisson_menuboissonfamille',
        'menuboisson', 'menuboissonfamille',
        ['menuBoissonFamilleId'], ['id']
    )

    # Alter boissonId to nullable=False
    op.alter_column('menuboisson', 'boissonId', existing_type=sa.UUID(), nullable=False)

    # Drop old unused columns
    op.drop_column('menuboisson', 'ordre')
    op.drop_column('menuboisson', 'imageUrl')


def downgrade() -> None:
    op.add_column('menuboisson', sa.Column('imageUrl', sa.VARCHAR(length=500), autoincrement=False, nullable=True))
    op.add_column('menuboisson', sa.Column('ordre', sa.INTEGER(), autoincrement=False, nullable=True))
    op.alter_column('menuboisson', 'boissonId', existing_type=sa.UUID(), nullable=True)
    op.drop_constraint('fk_menuboisson_menuboissonfamille', 'menuboisson', type_='foreignkey')
    op.drop_column('menuboisson', 'menuBoissonFamilleId')
    op.drop_table('menuboissonimage')
    op.drop_table('menuboissonfamille')
