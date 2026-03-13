"""make_social_url_nullable_in_identity_matches

Revision ID: ba3d0604a9cd
Revises: 44533e54c8b2
Create Date: 2026-03-13 15:12:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ba3d0604a9cd'
down_revision = '44533e54c8b2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make social_url nullable (platforms not found will have NULL URL)
    op.alter_column('identity_matches', 'social_url',
                    existing_type=sa.String(length=512),
                    nullable=True)


def downgrade() -> None:
    # Make social_url NOT NULL again
    op.alter_column('identity_matches', 'social_url',
                    existing_type=sa.String(length=512),
                    nullable=False)
