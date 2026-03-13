"""add_enriched_at_to_raw_players

Revision ID: 604f79e7bf58
Revises: 6f41d04e3aa1
Create Date: 2026-03-13 13:57:15.194575

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '604f79e7bf58'
down_revision = '6f41d04e3aa1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('raw_players', sa.Column('enriched_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix_raw_players_enriched_at'), 'raw_players', ['enriched_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_raw_players_enriched_at'), table_name='raw_players')
    op.drop_column('raw_players', 'enriched_at')
