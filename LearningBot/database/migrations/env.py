"""
Конфигурация Alembic для миграций
"""
import os
import sys
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from alembic import context

# Добавление родительской директории в sys.path для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database.database import Base
from database.models import *  # Импорт всех моделей
from config import settings

# Объект конфигурации Alembic
config = context.config

# Интерпретация конфигурационного файла для Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные для автогенерации
target_metadata = Base.metadata

# Установка URL базы данных из настроек (синхронная версия для миграций)
db_url = settings.db.url
if '+aiosqlite' in db_url:
    db_url = db_url.replace('+aiosqlite', '')
elif '+asyncpg' in db_url:
    db_url = db_url.replace('+asyncpg', '+psycopg2')
config.set_main_option('sqlalchemy.url', db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Запуск миграций с соединением"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Запуск миграций в 'online' режиме (синхронно)"""
    from sqlalchemy import create_engine
    
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()