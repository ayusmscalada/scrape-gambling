"""remove_platform_fields_from_raw_players_add_to_identity_matches

Revision ID: 1ff3baba0646
Revises: f8ae8596c7d4
Create Date: 2026-03-13 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1ff3baba0646'
down_revision = 'f8ae8596c7d4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove platform fields from raw_players
    op.drop_column('raw_players', 'overall_match_score')
    op.drop_column('raw_players', 'youtube_match_score')
    op.drop_column('raw_players', 'youtube_url')
    op.drop_column('raw_players', 'x_match_score')
    op.drop_column('raw_players', 'x_url')
    op.drop_column('raw_players', 'instagram_match_score')
    op.drop_column('raw_players', 'instagram_url')
    op.drop_column('raw_players', 'telegram_match_score')
    op.drop_column('raw_players', 'telegram_url')
    
    # Remove old match_score column and index from identity_matches
    op.drop_index('idx_match_score', table_name='identity_matches')
    op.drop_column('identity_matches', 'match_score')
    
    # Add platform_score and overall_match_score to identity_matches
    op.add_column('identity_matches', sa.Column('platform_score', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('identity_matches', sa.Column('overall_match_score', sa.Integer(), nullable=True))
    
    # Create new indexes
    op.create_index('idx_platform_score', 'identity_matches', ['platform_score'])
    op.create_index('idx_overall_match_score', 'identity_matches', ['overall_match_score'])


def downgrade() -> None:
    # Remove new indexes and fields from identity_matches (if they exist)
    try:
        op.drop_index('idx_overall_match_score', table_name='identity_matches')
    except:
        pass
    try:
        op.drop_index('idx_platform_score', table_name='identity_matches')
    except:
        pass
    op.drop_column('identity_matches', 'overall_match_score')
    op.drop_column('identity_matches', 'platform_score')
    
    # Restore old match_score column to identity_matches
    op.add_column('identity_matches', sa.Column('match_score', sa.Integer(), nullable=False, server_default='0'))
    op.create_index('idx_match_score', 'identity_matches', ['match_score'])
    
    # Restore platform fields to raw_players
    op.add_column('raw_players', sa.Column('telegram_url', sa.String(length=512), nullable=True))
    op.add_column('raw_players', sa.Column('telegram_match_score', sa.Integer(), nullable=True))
    op.add_column('raw_players', sa.Column('instagram_url', sa.String(length=512), nullable=True))
    op.add_column('raw_players', sa.Column('instagram_match_score', sa.Integer(), nullable=True))
    op.add_column('raw_players', sa.Column('x_url', sa.String(length=512), nullable=True))
    op.add_column('raw_players', sa.Column('x_match_score', sa.Integer(), nullable=True))
    op.add_column('raw_players', sa.Column('youtube_url', sa.String(length=512), nullable=True))
    op.add_column('raw_players', sa.Column('youtube_match_score', sa.Integer(), nullable=True))
    op.add_column('raw_players', sa.Column('overall_match_score', sa.Integer(), nullable=True))
