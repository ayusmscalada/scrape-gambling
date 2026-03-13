"""add_platform_match_fields_to_raw_players

Revision ID: f8ae8596c7d4
Revises: 604f79e7bf58
Create Date: 2026-03-13 14:28:31.347843

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8ae8596c7d4'
down_revision = '604f79e7bf58'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('raw_players', sa.Column('telegram_url', sa.String(length=512), nullable=True))
    op.add_column('raw_players', sa.Column('telegram_match_score', sa.Integer(), nullable=True))
    op.add_column('raw_players', sa.Column('instagram_url', sa.String(length=512), nullable=True))
    op.add_column('raw_players', sa.Column('instagram_match_score', sa.Integer(), nullable=True))
    op.add_column('raw_players', sa.Column('x_url', sa.String(length=512), nullable=True))
    op.add_column('raw_players', sa.Column('x_match_score', sa.Integer(), nullable=True))
    op.add_column('raw_players', sa.Column('youtube_url', sa.String(length=512), nullable=True))
    op.add_column('raw_players', sa.Column('youtube_match_score', sa.Integer(), nullable=True))
    op.add_column('raw_players', sa.Column('overall_match_score', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('raw_players', 'overall_match_score')
    op.drop_column('raw_players', 'youtube_match_score')
    op.drop_column('raw_players', 'youtube_url')
    op.drop_column('raw_players', 'x_match_score')
    op.drop_column('raw_players', 'x_url')
    op.drop_column('raw_players', 'instagram_match_score')
    op.drop_column('raw_players', 'instagram_url')
    op.drop_column('raw_players', 'telegram_match_score')
    op.drop_column('raw_players', 'telegram_url')
