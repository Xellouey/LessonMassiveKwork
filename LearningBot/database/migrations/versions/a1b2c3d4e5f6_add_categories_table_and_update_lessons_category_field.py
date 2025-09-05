"""add_categories_table_and_update_lessons_category_field

Revision ID: a1b2c3d4e5f6
Revises: f54955f9f186
Create Date: 2025-09-05 11:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f54955f9f186'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema"""
    # Создаём таблицу categories
    op.create_table('categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Добавляем поле category_id в таблицу lessons
    op.add_column('lessons', sa.Column('category_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_lessons_category_id', 'lessons', 'categories', ['category_id'], ['id'])
    
    # Создаём индекс для быстрого поиска по категориям
    op.create_index('ix_lessons_category_id', 'lessons', ['category_id'])


def downgrade() -> None:
    """Downgrade database schema"""
    # Удаляем индекс и внешний ключ
    op.drop_index('ix_lessons_category_id', 'lessons')
    op.drop_constraint('fk_lessons_category_id', 'lessons', type_='foreignkey')
    op.drop_column('lessons', 'category_id')
    
    # Удаляем таблицу categories
    op.drop_table('categories')