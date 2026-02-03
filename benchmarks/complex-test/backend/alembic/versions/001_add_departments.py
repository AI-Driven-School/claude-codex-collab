"""add departments table and user department_id

Revision ID: 001_add_departments
Revises:
Create Date: 2026-01-30

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_add_departments'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # departmentsテーブルを作成
    op.create_table(
        'departments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # usersテーブルにdepartment_idカラムを追加
    op.add_column(
        'users',
        sa.Column('department_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('departments.id'), nullable=True)
    )

    # インデックスを作成
    op.create_index('ix_departments_company_id', 'departments', ['company_id'])
    op.create_index('ix_users_department_id', 'users', ['department_id'])


def downgrade() -> None:
    # インデックスを削除
    op.drop_index('ix_users_department_id', table_name='users')
    op.drop_index('ix_departments_company_id', table_name='departments')

    # usersテーブルからdepartment_idカラムを削除
    op.drop_column('users', 'department_id')

    # departmentsテーブルを削除
    op.drop_table('departments')
