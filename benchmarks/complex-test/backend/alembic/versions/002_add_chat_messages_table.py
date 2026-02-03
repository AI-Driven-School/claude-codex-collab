"""add chat_messages table

Revision ID: 002_add_chat_messages
Revises: 001_add_departments
Create Date: 2026-02-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '002_add_chat_messages'
down_revision = '001_add_departments'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'chat_messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('role', sa.String(), nullable=False),  # "user" or "ai"
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # user_idとcreated_atの複合インデックスを作成（履歴取得の高速化）
    op.create_index('ix_chat_messages_user_id', 'chat_messages', ['user_id'])
    op.create_index('ix_chat_messages_user_created', 'chat_messages', ['user_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_chat_messages_user_created', table_name='chat_messages')
    op.drop_index('ix_chat_messages_user_id', table_name='chat_messages')
    op.drop_table('chat_messages')
