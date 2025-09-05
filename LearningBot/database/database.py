"""
Подключение к базе данных и настройка SQLAlchemy
"""
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from config import settings


class Base(DeclarativeBase):
    """Базовый класс для всех моделей"""
    pass


# Создание асинхронного движка
engine = create_async_engine(
    settings.db.url,
    echo=settings.db.echo,
    future=True
)

# Создание фабрики сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Получение сессии базы данных
    Используется как зависимость для внедрения в handlers
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Инициализация базы данных - создание таблиц"""
    from . import models  # Импорт всех моделей
    
    async with engine.begin() as conn:
        # Создание всех таблиц
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Закрытие соединения с базой данных"""
    await engine.dispose()


class DatabaseManager:
    """Менеджер для работы с базой данных"""
    
    def __init__(self):
        self.engine = engine
        self.session_factory = AsyncSessionLocal
    
    async def get_session(self) -> AsyncSession:
        """Получение новой сессии"""
        return self.session_factory()
    
    async def health_check(self) -> bool:
        """Проверка подключения к базе данных"""
        try:
            async with self.session_factory() as session:
                await session.execute("SELECT 1")
                return True
        except Exception:
            return False


# Глобальный экземпляр менеджера БД
db_manager = DatabaseManager()