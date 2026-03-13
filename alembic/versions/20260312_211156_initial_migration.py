"""Initial migration

Revision ID: 20260312_211156
Revises: 
Create Date: 2026-03-12 21:11:56.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260312_211156'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create raw_players table
    op.create_table(
        'raw_players',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('source_site', sa.String(length=100), nullable=True),
        sa.Column('captured_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_raw_players_id', 'raw_players', ['id'], unique=False)
    op.create_index('ix_raw_players_username', 'raw_players', ['username'], unique=False)
    op.create_index('ix_raw_players_source_site', 'raw_players', ['source_site'], unique=False)
    op.create_index('idx_username_source', 'raw_players', ['username', 'source_site'], unique=False)
    
    # Create identity_matches table
    op.create_table(
        'identity_matches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('raw_player_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('social_handle', sa.String(length=255), nullable=False),
        sa.Column('social_url', sa.String(length=512), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.String(length=512), nullable=True),
        sa.Column('public_contact_type', sa.String(length=50), nullable=True),
        sa.Column('public_contact_value', sa.String(length=255), nullable=True),
        sa.Column('match_score', sa.Integer(), nullable=False),
        sa.Column('confidence_label', sa.String(length=50), nullable=False),
        sa.Column('scoring_reasons', postgresql.JSONB(), nullable=True),
        sa.Column('evidence_json', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['raw_player_id'], ['raw_players.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_identity_matches_id', 'identity_matches', ['id'], unique=False)
    op.create_index('ix_identity_matches_raw_player_id', 'identity_matches', ['raw_player_id'], unique=False)
    op.create_index('ix_identity_matches_platform', 'identity_matches', ['platform'], unique=False)
    op.create_index('idx_raw_player_platform', 'identity_matches', ['raw_player_id', 'platform'], unique=False)
    op.create_index('idx_match_score', 'identity_matches', ['match_score'], unique=False)
    
    # Create qualified_leads table
    op.create_table(
        'qualified_leads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('raw_player_id', sa.Integer(), nullable=False),
        sa.Column('best_contact_type', sa.String(length=50), nullable=True),
        sa.Column('best_contact_value', sa.String(length=255), nullable=True),
        sa.Column('confidence', sa.Integer(), nullable=True),
        sa.Column('confidence_label', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['raw_player_id'], ['raw_players.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('raw_player_id')
    )
    op.create_index('ix_qualified_leads_raw_player_id', 'qualified_leads', ['raw_player_id'], unique=True)
    op.create_index('idx_confidence_label', 'qualified_leads', ['confidence_label'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_confidence_label', table_name='qualified_leads')
    op.drop_table('qualified_leads')
    op.drop_index('idx_match_score', table_name='identity_matches')
    op.drop_index('idx_raw_player_platform', table_name='identity_matches')
    op.drop_index('ix_identity_matches_platform', table_name='identity_matches')
    op.drop_index('ix_identity_matches_raw_player_id', table_name='identity_matches')
    op.drop_index('ix_identity_matches_id', table_name='identity_matches')
    op.drop_table('identity_matches')
    op.drop_index('idx_username_source', table_name='raw_players')
    op.drop_index('ix_raw_players_source_site', table_name='raw_players')
    op.drop_index('ix_raw_players_username', table_name='raw_players')
    op.drop_index('ix_raw_players_id', table_name='raw_players')
    op.drop_table('raw_players')
