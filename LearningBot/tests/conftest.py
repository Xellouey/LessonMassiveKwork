"""
Базовые фикстуры и конфигурация тестов
"""
import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from unittest.mock import AsyncMock, MagicMock

from database.database import Base
from database.models import User, Lesson, Purchase, Admin
from services.user import UserService
from services.lesson import LessonService
from services.payment import PaymentService
from services.admin import AdminService


# Тестовая БД в памяти
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для всей сессии тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_engine():
    """Создание тестового движка БД"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )
    
    # Создание всех таблиц
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Очистка после тестов
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine):
    """Создание тестовой сессии БД"""
    async_session = async_sessionmaker(
        test_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
async def sample_user(db_session):
    """Создание тестового пользователя"""
    user = User(
        user_id=123456789,
        username="test_user",
        full_name="Тестовый Пользователь",
        registration_date=datetime.now(timezone.utc),
        is_active=True,
        language='ru',
        total_spent=0,
        last_activity=datetime.now(timezone.utc)
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture
async def sample_lesson(db_session):
    """Создание тестового урока с тематикой ИИ"""
    lesson = Lesson(
        title="Основы нейронных сетей",
        description="Изучение основ построения и обучения нейронных сетей для решения задач машинного обучения",
        price_stars=100,
        content_type="video",
        file_id="test_file_id_123",
        duration=300,  # 5 минут
        is_active=True,
        is_free=False,
        category="Нейронные сети",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        views_count=0
    )
    
    db_session.add(lesson)
    await db_session.commit()
    await db_session.refresh(lesson)
    
    return lesson


@pytest.fixture
async def sample_free_lesson(db_session):
    """Создание тестового бесплатного урока по ИИ"""
    lesson = Lesson(
        title="Бесплатное введение в ИИ",
        description="Краткое введение в мир искусственного интеллекта и машинного обучения",
        price_stars=0,
        content_type="video",
        file_id="free_lesson_file_id",
        duration=180,  # 3 минуты
        is_active=True,
        is_free=True,
        category="Основы ИИ",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        views_count=0
    )
    
    db_session.add(lesson)
    await db_session.commit()
    await db_session.refresh(lesson)
    
    return lesson


@pytest.fixture
async def sample_purchase(db_session, sample_user, sample_lesson):
    """Создание тестовой покупки"""
    purchase = Purchase(
        user_id=sample_user.user_id,
        lesson_id=sample_lesson.id,
        payment_charge_id="test_payment_123",
        purchase_date=datetime.now(timezone.utc),
        status="completed",
        amount_stars=sample_lesson.price_stars
    )
    
    db_session.add(purchase)
    await db_session.commit()
    await db_session.refresh(purchase)
    
    return purchase


@pytest.fixture
def mock_bot():
    """Мок объект бота для тестирования"""
    bot = AsyncMock()
    bot.send_invoice = AsyncMock()
    bot.get_star_transactions = AsyncMock()
    return bot


@pytest.fixture
async def user_service(db_session):
    """Сервис для работы с пользователями"""
    return UserService(db_session)


@pytest.fixture
async def lesson_service(db_session):
    """Сервис для работы с уроками"""
    return LessonService(db_session)


@pytest.fixture
async def payment_service(db_session, mock_bot):
    """Сервис для работы с платежами"""
    return PaymentService(db_session, mock_bot)


@pytest.fixture
async def admin_service(db_session):
    """Сервис для работы с администраторами"""
    return AdminService(db_session)


@pytest.fixture
async def sample_admin(db_session):
    """Создание тестового администратора"""
    admin = Admin(
        user_id=987654321,
        username="test_admin",
        permissions="all",
        created_at=datetime.now(timezone.utc),
        is_active=True,
        last_login=datetime.now(timezone.utc)
    )
    
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    
    return admin


@pytest.fixture
def sample_telegram_payment():
    """Создание тестовых данных платежа Telegram"""
    return {
        "telegram_payment_charge_id": "test_charge_123456789",
        "provider_payment_charge_id": "provider_charge_123",
        "total_amount": 100,
        "currency": "XTR",
        "invoice_payload": "lesson_1_123456789_1672531200",
        "shipping_option_id": None,
        "order_info": None
    }