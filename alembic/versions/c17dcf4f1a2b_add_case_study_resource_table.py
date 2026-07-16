"""add case_study_resource table

Revision ID: c17dcf4f1a2b
Revises: f9f51e5ae944
Create Date: 2026-07-16 12:16:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c17dcf4f1a2b'
down_revision: Union[str, Sequence[str], None] = 'aaf7b86a2e14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('case_study_resource',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_study_id', sa.Integer(), nullable=False),
        sa.Column('video_title', sa.String(), nullable=False),
        sa.Column('youtube_url', sa.String(), nullable=False),
        sa.Column('youtube_video_id', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('is_important', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['case_study_id'], ['case_study.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_case_study_resource_case_study_id'), 'case_study_resource', ['case_study_id'], unique=False)
    op.create_index(op.f('ix_case_study_resource_display_order'), 'case_study_resource', ['display_order'], unique=False)
    op.create_index(op.f('ix_case_study_resource_id'), 'case_study_resource', ['id'], unique=False)
    op.create_index(op.f('ix_case_study_resource_youtube_video_id'), 'case_study_resource', ['youtube_video_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_case_study_resource_youtube_video_id'), table_name='case_study_resource')
    op.drop_index(op.f('ix_case_study_resource_id'), table_name='case_study_resource')
    op.drop_index(op.f('ix_case_study_resource_display_order'), table_name='case_study_resource')
    op.drop_index(op.f('ix_case_study_resource_case_study_id'), table_name='case_study_resource')
    op.drop_table('case_study_resource')
