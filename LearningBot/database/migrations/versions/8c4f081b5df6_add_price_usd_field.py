"""add price_usd to lessons

Revision ID: 8c4f081b5df6
Revises: f54955f9f186
Create Date: 2025-09-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = '8c4f081b5df6'
down_revision: Union[str, None] = 'f54955f9f186'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем поле price_usd
    op.add_column('lessons', sa.Column('price_usd', sa.Numeric(10, 2), nullable=False, server_default='0.0'))
    
    # Обновляем существующие записи - конвертируем price_stars в price_usd
    connection = op.get_bind()
    connection.execute(text("""
        UPDATE lessons 
        SET price_usd = ROUND(price_stars * 0.013, 2) 
        WHERE price_stars > 0 AND is_free = false
    """))
    
    # Для бесплатных уроков устанавливаем price_usd = 0
    connection.execute(text("""
        UPDATE lessons 
        SET price_usd = 0 
        WHERE is_free = true
    """))


def downgrade() -> None:
    # Удаляем поле price_usd
    op.drop_column('lessons', 'price_usd')