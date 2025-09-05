"""
Тесты для сервиса управления пользователями
"""
import pytest
from datetime import datetime, timedelta

from services.user import UserService
from database.models import User
# from database.models import UserActivity  # ❌ Закомментировано для MVP


class TestUserService:
    """Тесты для UserService"""

    @pytest.mark.asyncio
    async def test_get_user_by_telegram_id_existing(self, user_service, sample_user):
        """Тест получения существующего пользователя по Telegram ID"""
        user = await user_service.get_user_by_telegram_id(sample_user.user_id)
        
        assert user is not None
        assert user.user_id == sample_user.user_id
        assert user.username == sample_user.username
        assert user.full_name == sample_user.full_name

    @pytest.mark.asyncio
    async def test_get_user_by_telegram_id_not_existing(self, user_service):
        """Тест получения несуществующего пользователя"""
        user = await user_service.get_user_by_telegram_id(999999999)
        
        assert user is None

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service):
        """Тест успешного создания пользователя"""
        user_id = 987654321
        username = "new_user"
        full_name = "Новый Пользователь"
        
        user = await user_service.create_user(user_id, username, full_name)
        
        assert user is not None
        assert user.user_id == user_id
        assert user.username == username
        assert user.full_name == full_name
        assert user.is_active is True
        assert user.language == 'ru'
        assert user.total_spent == 0

    @pytest.mark.asyncio
    async def test_create_user_duplicate(self, user_service, sample_user):
        """Тест создания пользователя с существующим ID (должно вернуть None)"""
        user = await user_service.create_user(
            sample_user.user_id, 
            "duplicate_user", 
            "Дубликат"
        )
        
        # Ожидаем None из-за нарушения уникальности
        assert user is None

    @pytest.mark.asyncio
    async def test_get_or_create_user_existing(self, user_service, sample_user):
        """Тест получения существующего пользователя через get_or_create"""
        user = await user_service.get_or_create_user(
            sample_user.user_id,
            sample_user.username,
            sample_user.full_name
        )
        
        assert user is not None
        assert user.id == sample_user.id
        assert user.user_id == sample_user.user_id

    @pytest.mark.asyncio
    async def test_get_or_create_user_new(self, user_service):
        """Тест создания нового пользователя через get_or_create"""
        user_id = 111222333
        username = "auto_created"
        full_name = "Авто Созданный"
        
        user = await user_service.get_or_create_user(user_id, username, full_name)
        
        assert user is not None
        assert user.user_id == user_id
        assert user.username == username
        assert user.full_name == full_name

    @pytest.mark.asyncio
    async def test_update_user_activity(self, user_service, sample_user):
        """Тест обновления времени последней активности"""
        # Сохраняем время до обновления
        old_activity = sample_user.last_activity
        # Делаем timezone-aware если нужно
        from datetime import timezone
        if old_activity.tzinfo is None:
            old_activity = old_activity.replace(tzinfo=timezone.utc)
        
        # Небольшая задержка для изменения времени
        await asyncio.sleep(0.01)
        
        success = await user_service.update_user_activity(sample_user.user_id)
        
        assert success is True
        
        # Получаем обновленного пользователя
        updated_user = await user_service.get_user_by_telegram_id(sample_user.user_id)
        assert updated_user.last_activity > old_activity

    @pytest.mark.asyncio
    async def test_update_user_language(self, user_service, sample_user):
        """Тест изменения языка пользователя"""
        new_language = 'en'
        
        success = await user_service.update_user_language(sample_user.user_id, new_language)
        
        assert success is True
        
        # Проверяем изменение
        updated_user = await user_service.get_user_by_telegram_id(sample_user.user_id)
        assert updated_user.language == new_language

    @pytest.mark.asyncio
    async def test_update_user_status(self, user_service, sample_user):
        """Тест изменения статуса активности пользователя"""
        new_status = False
        
        success = await user_service.update_user_status(sample_user.user_id, new_status)
        
        assert success is True
        
        # Проверяем изменение
        updated_user = await user_service.get_user_by_telegram_id(sample_user.user_id)
        assert updated_user.is_active == new_status

    @pytest.mark.asyncio
    async def test_log_user_activity(self, user_service, sample_user):
        """Тест логирования активности пользователя"""
        action = "test_action"
        lesson_id = 1
        extra_data = "test_metadata"
        
        success = await user_service.log_user_activity(
            sample_user.user_id,
            action,
            lesson_id=lesson_id,
            extra_data=extra_data
        )
        
        assert success is True
        
        # Проверяем создание записи активности
        from sqlalchemy import select
        result = await user_service.session.execute(
            # select(UserActivity).where(  # ❌ Закомментировано для MVP
            #     UserActivity.user_id == sample_user.user_id,
            #     UserActivity.action == action
            # )
        )
        activity = result.scalar_one_or_none()
        
        assert activity is not None
        assert activity.action == action
        assert activity.lesson_id == lesson_id
        assert activity.extra_data == extra_data

    @pytest.mark.asyncio
    async def test_block_user(self, user_service, sample_user):
        """Тест блокировки пользователя"""
        success = await user_service.block_user(sample_user.user_id)
        
        assert success is True
        
        # Проверяем статус
        updated_user = await user_service.get_user_by_telegram_id(sample_user.user_id)
        assert updated_user.is_active is False

    @pytest.mark.asyncio
    async def test_unblock_user(self, user_service, sample_user):
        """Тест разблокировки пользователя"""
        # Сначала блокируем
        await user_service.block_user(sample_user.user_id)
        
        # Затем разблокируем
        success = await user_service.unblock_user(sample_user.user_id)
        
        assert success is True
        
        # Проверяем статус
        updated_user = await user_service.get_user_by_telegram_id(sample_user.user_id)
        assert updated_user.is_active is True


# Дополнительный импорт для теста
import asyncio