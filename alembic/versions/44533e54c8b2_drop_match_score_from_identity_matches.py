"""drop_match_score_from_identity_matches

Revision ID: 44533e54c8b2
Revises: 1ff3baba0646
Create Date: 2026-03-13 15:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '44533e54c8b2'
down_revision = '1ff3baba0646'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use raw SQL with IF EXISTS to avoid transaction abort on missing objects
    op.execute('DROP INDEX IF EXISTS idx_match_score')
    op.execute('ALTER TABLE identity_matches DROP COLUMN IF EXISTS match_score')


def downgrade() -> None:
    # Restore match_score column
    op.add_column('identity_matches', sa.Column('match_score', sa.Integer(), nullable=False, server_default='0'))
    op.create_index('idx_match_score', 'identity_matches', ['match_score'])
