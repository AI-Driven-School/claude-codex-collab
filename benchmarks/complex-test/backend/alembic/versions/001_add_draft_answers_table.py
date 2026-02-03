"""add draft_answers table

Revision ID: 001_add_draft_answers
Revises:
Create Date: 2026-01-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '001_add_draft_answers'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'draft_answers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('answers', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    # user_idにインデックスを作成
    op.create_index('ix_draft_answers_user_id', 'draft_answers', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_draft_answers_user_id', table_name='draft_answers')
    op.drop_table('draft_answers')
