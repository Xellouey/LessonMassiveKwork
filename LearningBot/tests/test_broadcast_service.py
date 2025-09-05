"""
Тесты для BroadcastService
"""
import pytest
from datetime import datetime, timedelta, timezone
import json
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Admin, Broadcast
# from database.models import BroadcastDelivery  # ❌ Закомментировано для MVP
from services.broadcast import BroadcastService


class TestBroadcastService:
    """Тесты для сервиса массовых рассылок"""

    @pytest.fixture
    async def broadcast_service(self, db_session: AsyncSession):
        """Фикстура для создания BroadcastService"""
        return BroadcastService(db_session)

    @pytest.fixture
    async def sample_broadcast_data(self, db_session: AsyncSession):
        """Создание тестовых данных для рассылок"""
        # Создаем администратора
        admin = Admin(
            user_id=99999,
            username="test_admin",
            permissions="all",
            is_active=True
        )
        
        # Создаем пользователей
        user1 = User(
            user_id=11111,
            full_name="Иван Иванов",
            username="ivan_ivanov",
            language="ru",
            registration_date=datetime.now(timezone.utc) - timedelta(days=30),
            last_activity=datetime.now(timezone.utc) - timedelta(days=1),
            is_active=True
        )
        user2 = User(
            user_id=22222,
            full_name="Мария Петрова",
            username="maria_petrova",
            language="ru",
            registration_date=datetime.now(timezone.utc) - timedelta(days=20),
            last_activity=datetime.now(timezone.utc) - timedelta(hours=2),
            is_active=True
        )
        user3 = User(
            user_id=33333,
            full_name="John Smith",
            username="john_smith",
            language="en",
            registration_date=datetime.now(timezone.utc) - timedelta(days=10),
            last_activity=datetime.now(timezone.utc) - timedelta(hours=1),
            is_active=False  # Заблокированный пользователь
        )
        
        db_session.add_all([admin, user1, user2, user3])
        await db_session.commit()
        
        return {
            'admin': admin,
            'users': [user1, user2, user3],
            'active_users': [user1, user2],
            'blocked_users': [user3]
        }

    async def test_create_broadcast_text_only(self, broadcast_service: BroadcastService, sample_broadcast_data):
        """Тест создания текстовой рассылки"""
        admin = sample_broadcast_data['admin']
        
        broadcast = await broadcast_service.create_broadcast(
            admin_id=admin.user_id,
            text="Тестовое сообщение рассылки",
            media_type=None,
            file_id=None
        )
        
        assert broadcast is not None
        assert broadcast.admin_id == admin.user_id
        assert broadcast.text == "Тестовое сообщение рассылки"
        assert broadcast.media_type is None
        assert broadcast.file_id is None
        assert broadcast.status == "pending"
        assert broadcast.total_users == 0
        assert broadcast.success_count == 0

    async def test_create_broadcast_with_media(self, broadcast_service: BroadcastService, sample_broadcast_data):
        """Тест создания рассылки с медиа"""
        admin = sample_broadcast_data['admin']
        
        broadcast = await broadcast_service.create_broadcast(
            admin_id=admin.user_id,
            text="Рассылка с фото",
            media_type="photo",
            file_id="test_photo_file_id"
        )
        
        assert broadcast is not None
        assert broadcast.text == "Рассылка с фото"
        assert broadcast.media_type == "photo"
        assert broadcast.file_id == "test_photo_file_id"

    @patch('services.broadcast.Bot')
    async def test_send_broadcast_to_all_users(self, mock_bot_class, broadcast_service: BroadcastService, sample_broadcast_data):
        """Тест отправки рассылки всем пользователям"""
        admin = sample_broadcast_data['admin']
        
        # Создаем рассылку
        broadcast = await broadcast_service.create_broadcast(
            admin_id=admin.user_id,
            text="Рассылка всем пользователям"
        )
        
        # Настраиваем мок бота
        mock_bot = AsyncMock()
        mock_bot_class.return_value = mock_bot
        mock_bot.send_message = AsyncMock()
        
        # Отправляем рассылку
        result = await broadcast_service.send_broadcast(
            broadcast_id=broadcast.id,
            target_audience="all",
            bot_token="test_token"
        )
        
        assert result is True
        
        # Проверяем обновление статистики рассылки
        updated_broadcast = await broadcast_service.get_broadcast_by_id(broadcast.id)
        assert updated_broadcast.status == "completed"
        assert updated_broadcast.total_users == 3  # Все пользователи
        assert updated_broadcast.success_count >= 0

    @patch('services.broadcast.Bot')
    async def test_send_broadcast_to_active_users_only(self, mock_bot_class, broadcast_service: BroadcastService, sample_broadcast_data):
        """Тест отправки рассылки только активным пользователям"""
        admin = sample_broadcast_data['admin']
        
        broadcast = await broadcast_service.create_broadcast(
            admin_id=admin.user_id,
            text="Рассылка активным пользователям"
        )
        
        mock_bot = AsyncMock()
        mock_bot_class.return_value = mock_bot
        mock_bot.send_message = AsyncMock()
        
        result = await broadcast_service.send_broadcast(
            broadcast_id=broadcast.id,
            target_audience="active",
            bot_token="test_token"
        )
        
        assert result is True
        
        # Проверяем, что рассылка отправлена только активным пользователям
        updated_broadcast = await broadcast_service.get_broadcast_by_id(broadcast.id)
        assert updated_broadcast.total_users == 2  # Только активные пользователи

    @patch('services.broadcast.Bot')
    async def test_send_broadcast_with_delivery_tracking(self, mock_bot_class, broadcast_service: BroadcastService, sample_broadcast_data):
        """Тест отслеживания доставки рассылки"""
        admin = sample_broadcast_data['admin']
        
        broadcast = await broadcast_service.create_broadcast(
            admin_id=admin.user_id,
            text="Рассылка с отслеживанием"
        )
        
        mock_bot = AsyncMock()
        mock_bot_class.return_value = mock_bot
        mock_bot.send_message = AsyncMock()
        
        await broadcast_service.send_broadcast(
            broadcast_id=broadcast.id,
            target_audience="active",
            bot_token="test_token"
        )
        
        # Проверяем создание записей о доставке
        deliveries = await broadcast_service.get_broadcast_deliveries(broadcast.id)
        assert len(deliveries) == 2  # Для двух активных пользователей
        
        for delivery in deliveries:
            assert delivery.broadcast_id == broadcast.id
            assert delivery.status in ["sent", "pending", "failed"]

    async def test_get_broadcast_statistics(self, broadcast_service: BroadcastService, sample_broadcast_data):
        """Тест получения статистики рассылки"""
        admin = sample_broadcast_data['admin']
        
        broadcast = await broadcast_service.create_broadcast(
            admin_id=admin.user_id,
            text="Рассылка для статистики"
        )
        
        # Имитируем отправленную рассылку
        broadcast.status = "completed"
        broadcast.total_users = 3
        broadcast.success_count = 2
        await broadcast_service.session.commit()
        
        stats = await broadcast_service.get_broadcast_statistics(broadcast.id)
        
        assert stats is not None
        assert stats['broadcast_id'] == broadcast.id
        assert stats['total_users'] == 3
        assert stats['success_count'] == 2
        assert stats['failed_count'] == 1
        assert stats['success_rate'] == 66.67  # 2/3 * 100

    async def test_get_broadcasts_history(self, broadcast_service: BroadcastService, sample_broadcast_data):
        """Тест получения истории рассылок"""
        admin = sample_broadcast_data['admin']
        
        # Создаем несколько рассылок
        broadcast1 = await broadcast_service.create_broadcast(
            admin_id=admin.user_id,
            text="Первая рассылка"
        )
        broadcast2 = await broadcast_service.create_broadcast(
            admin_id=admin.user_id,
            text="Вторая рассылка"
        )
        
        history = await broadcast_service.get_broadcasts_history(admin_id=admin.user_id, limit=10)
        
        assert len(history) == 2
        assert history[0].id == broadcast2.id  # Новые первыми
        assert history[1].id == broadcast1.id

    async def test_cancel_broadcast(self, broadcast_service: BroadcastService, sample_broadcast_data):
        """Тест отмены рассылки"""
        admin = sample_broadcast_data['admin']
        
        broadcast = await broadcast_service.create_broadcast(
            admin_id=admin.user_id,
            text="Рассылка для отмены"
        )
        
        success = await broadcast_service.cancel_broadcast(broadcast.id)
        
        assert success is True
        
        # Проверяем изменение статуса
        cancelled_broadcast = await broadcast_service.get_broadcast_by_id(broadcast.id)
        assert cancelled_broadcast.status == "cancelled"

    async def test_cancel_already_sent_broadcast(self, broadcast_service: BroadcastService, sample_broadcast_data):
        """Тест отмены уже отправленной рассылки"""
        admin = sample_broadcast_data['admin']
        
        broadcast = await broadcast_service.create_broadcast(
            admin_id=admin.user_id,
            text="Уже отправленная рассылка"
        )
        
        # Имитируем отправленную рассылку
        broadcast.status = "completed"
        await broadcast_service.session.commit()
        
        success = await broadcast_service.cancel_broadcast(broadcast.id)
        
        assert success is False  # Нельзя отменить уже отправленную

    async def test_get_active_broadcasts(self, broadcast_service: BroadcastService, sample_broadcast_data):
        """Тест получения активных рассылок"""
        admin = sample_broadcast_data['admin']
        
        # Создаем рассылки с разными статусами
        pending_broadcast = await broadcast_service.create_broadcast(
            admin_id=admin.user_id,
            text="Ожидающая рассылка"
        )
        
        sending_broadcast = await broadcast_service.create_broadcast(
            admin_id=admin.user_id,
            text="Отправляющаяся рассылка"
        )
        sending_broadcast.status = "sending"
        
        completed_broadcast = await broadcast_service.create_broadcast(
            admin_id=admin.user_id,
            text="Завершенная рассылка"
        )
        completed_broadcast.status = "completed"
        
        await broadcast_service.session.commit()
        
        active_broadcasts = await broadcast_service.get_active_broadcasts()
        
        # Активными считаются pending и sending
        assert len(active_broadcasts) == 2
        active_ids = [b.id for b in active_broadcasts]
        assert pending_broadcast.id in active_ids
        assert sending_broadcast.id in active_ids
        assert completed_broadcast.id not in active_ids

    async def test_delete_broadcast(self, broadcast_service: BroadcastService, sample_broadcast_data):
        """Тест удаления рассылки"""
        admin = sample_broadcast_data['admin']
        
        broadcast = await broadcast_service.create_broadcast(
            admin_id=admin.user_id,
            text="Рассылка для удаления"
        )
        
        success = await broadcast_service.delete_broadcast(broadcast.id)
        
        assert success is True
        
        # Проверяем, что рассылка удалена
        deleted_broadcast = await broadcast_service.get_broadcast_by_id(broadcast.id)
        assert deleted_broadcast is None

    async def test_delete_broadcast_with_deliveries(self, broadcast_service: BroadcastService, sample_broadcast_data):
        """Тест удаления рассылки вместе с записями о доставке"""
        admin = sample_broadcast_data['admin']
        users = sample_broadcast_data['users']
        
        broadcast = await broadcast_service.create_broadcast(
            admin_id=admin.user_id,
            text="Рассылка с доставками"
        )
        
        # Создаем записи о доставке
        for user in users:
            delivery = BroadcastDelivery(
                broadcast_id=broadcast.id,
                user_id=user.user_id,
                status="sent"
            )
            broadcast_service.session.add(delivery)
        
        await broadcast_service.session.commit()
        
        success = await broadcast_service.delete_broadcast(broadcast.id)
        
        assert success is True
        
        # Проверяем, что записи о доставке тоже удалены
        deliveries = await broadcast_service.get_broadcast_deliveries(broadcast.id)
        assert len(deliveries) == 0

    async def test_get_broadcast_by_id_not_found(self, broadcast_service: BroadcastService):
        """Тест получения несуществующей рассылки"""
        broadcast = await broadcast_service.get_broadcast_by_id(99999)
        assert broadcast is None

    async def test_get_delivery_statistics(self, broadcast_service: BroadcastService, sample_broadcast_data):
        """Тест получения детальной статистики доставки"""
        admin = sample_broadcast_data['admin']
        users = sample_broadcast_data['users']
        
        broadcast = await broadcast_service.create_broadcast(
            admin_id=admin.user_id,
            text="Рассылка для статистики доставки"
        )
        
        # Создаем записи о доставке с разными статусами
        delivery1 = BroadcastDelivery(
            broadcast_id=broadcast.id,
            user_id=users[0].user_id,
            status="sent"
        )
        delivery2 = BroadcastDelivery(
            broadcast_id=broadcast.id,
            user_id=users[1].user_id,
            status="failed",
            error_message="User blocked bot"
        )
        delivery3 = BroadcastDelivery(
            broadcast_id=broadcast.id,
            user_id=users[2].user_id,
            status="pending"
        )
        
        broadcast_service.session.add_all([delivery1, delivery2, delivery3])
        await broadcast_service.session.commit()
        
        stats = await broadcast_service.get_delivery_statistics(broadcast.id)
        
        assert stats['sent'] == 1
        assert stats['failed'] == 1
        assert stats['pending'] == 1
        assert stats['total'] == 3