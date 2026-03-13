"""add_unique_constraint_username_source_site

Revision ID: 6f41d04e3aa1
Revises: 20260312_211156
Create Date: 2026-03-13 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '6f41d04e3aa1'
down_revision = '20260312_211156'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add unique constraint on (username, source_site)
    # This ensures that the combination of username + platform is unique
    op.create_unique_constraint(
        'uq_raw_players_username_source',
        'raw_players',
        ['username', 'source_site']
    )


def downgrade() -> None:
    # Remove the unique constraint
    op.drop_constraint(
        'uq_raw_players_username_source',
        'raw_players',
        type_='unique'
    )
