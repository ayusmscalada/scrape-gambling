"""reimplement_identity_enrichment_with_uuid_and_new_schema

Revision ID: 8c58a2c55cc8
Revises: ba3d0604a9cd
Create Date: 2026-03-13 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '8c58a2c55cc8'
down_revision = 'ba3d0604a9cd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old tables if they exist (in reverse dependency order)
    op.execute("DROP TABLE IF EXISTS qualified_leads CASCADE")
    op.execute("DROP TABLE IF EXISTS identity_matches CASCADE")
    op.execute("DROP TABLE IF EXISTS raw_players CASCADE")
    
    # Create raw_players table with new schema
    op.create_table(
        'raw_players',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('site', sa.String(255), nullable=False),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('metric_value', sa.Numeric(), nullable=True),
        sa.Column('source_url', sa.String(512), nullable=True),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create indexes for raw_players
    op.create_index('ix_raw_players_id', 'raw_players', ['id'], unique=False)
    op.create_index('ix_raw_players_site', 'raw_players', ['site'], unique=False)
    op.create_index('ix_raw_players_username', 'raw_players', ['username'], unique=False)
    op.create_index('ix_raw_players_captured_at', 'raw_players', ['captured_at'], unique=False)
    op.create_index('idx_site_username', 'raw_players', ['site', 'username'], unique=False)
    
    # Create identity_matches table with new schema
    op.create_table(
        'identity_matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('raw_player_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('telegram_url', sa.String(512), nullable=True),
        sa.Column('instagram_url', sa.String(512), nullable=True),
        sa.Column('x_url', sa.String(512), nullable=True),
        sa.Column('youtube_url', sa.String(512), nullable=True),
        sa.Column('telegram_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('instagram_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('x_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('youtube_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_score', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['raw_player_id'], ['raw_players.id'], ondelete='CASCADE'),
    )
    
    # Create indexes and unique constraint for identity_matches
    op.create_index('ix_identity_matches_id', 'identity_matches', ['id'], unique=False)
    op.create_index('ix_identity_matches_raw_player_id', 'identity_matches', ['raw_player_id'], unique=False)
    op.create_index('ix_identity_matches_created_at', 'identity_matches', ['created_at'], unique=False)
    op.create_index('idx_total_score', 'identity_matches', ['total_score'], unique=False)
    op.create_unique_constraint('unique_identity_match', 'identity_matches', ['raw_player_id'])


def downgrade() -> None:
    # Drop new tables
    op.drop_constraint('unique_identity_match', 'identity_matches', type_='unique')
    op.drop_index('idx_total_score', table_name='identity_matches')
    op.drop_index('ix_identity_matches_created_at', table_name='identity_matches')
    op.drop_index('ix_identity_matches_raw_player_id', table_name='identity_matches')
    op.drop_index('ix_identity_matches_id', table_name='identity_matches')
    op.drop_table('identity_matches')
    
    op.drop_index('idx_site_username', table_name='raw_players')
    op.drop_index('ix_raw_players_captured_at', table_name='raw_players')
    op.drop_index('ix_raw_players_username', table_name='raw_players')
    op.drop_index('ix_raw_players_site', table_name='raw_players')
    op.drop_index('ix_raw_players_id', table_name='raw_players')
    op.drop_table('raw_players')
