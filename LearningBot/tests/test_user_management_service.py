"""
Тесты для UserManagementService
"""
import pytest
from datetime import datetime, timedelta, timezone
import json
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Lesson, Purchase, Admin
# from database.models import UserActivity  # ❌ Закомментировано для MVP
from services.user_management import UserManagementService


class TestUserManagementService:
    """Тесты для сервиса управления пользователями"""

    @pytest.fixture
    async def user_management_service(self, db_session: AsyncSession):
        """Фикстура для создания UserManagementService"""
        return UserManagementService(db_session)

    @pytest.fixture
    async def sample_users_data(self, db_session: AsyncSession):
        """Создание тестовых данных пользователей"""
        # Создаем пользователей
        user1 = User(
            user_id=11111,
            full_name="Иван Иванов",
            username="ivan_ivanov", 
            language="ru",
            registration_date=datetime.now(timezone.utc) - timedelta(days=30),
            last_activity=datetime.now(timezone.utc) - timedelta(days=1),
            is_active=True,
            total_spent=300
        )
        user2 = User(
            user_id=22222,
            full_name="Мария Петрова",
            username="maria_petrova",
            language="ru", 
            registration_date=datetime.now(timezone.utc) - timedelta(days=60),
            last_activity=datetime.now(timezone.utc) - timedelta(days=40),
            is_active=False,  # Заблокированный пользователь
            total_spent=0
        )
        user3 = User(
            user_id=33333,
            full_name="John Smith",
            username="john_smith",
            language="en",
            registration_date=datetime.now(timezone.utc) - timedelta(days=10),
            last_activity=datetime.now(timezone.utc) - timedelta(hours=2),
            is_active=True,
            total_spent=150
        )
        
        # Создаем урок по ИИ для тестирования покупок
        lesson1 = Lesson(
            title="Машинное обучение для начинающих",
            description="Изучение основ машинного обучения и нейронных сетей",
            price_stars=100,
            is_active=True,
            is_free=False,
            file_id="test_file_1",
            content_type="video"
        )
        
        db_session.add_all([user1, user2, user3, lesson1])
        await db_session.flush()
        
        # Создаем покупки
        purchase1 = Purchase(
            user_id=user1.user_id,  # Используем Telegram user_id
            lesson_id=lesson1.id,
            payment_charge_id="test_charge_1",
            amount_stars=100,
            status="completed",
            purchase_date=datetime.now(timezone.utc) - timedelta(days=5)
        )
        purchase2 = Purchase(
            user_id=user3.user_id,  # Используем Telegram user_id
            lesson_id=lesson1.id,
            payment_charge_id="test_charge_2", 
            amount_stars=100,
            status="completed",
            purchase_date=datetime.now(timezone.utc) - timedelta(days=2)
        )
        
        # Создаем активность пользователей - ❌ Закомментировано для MVP
        # activity1 = UserActivity(
        #     user_id=user1.user_id,  # Используем Telegram user_id
        #     action="lesson_view",
        #     timestamp=datetime.now(timezone.utc) - timedelta(days=1),
        #     extra_data=json.dumps({"lesson_id": lesson1.id})
        # )
        # activity2 = UserActivity(
        #     user_id=user3.user_id,  # Используем Telegram user_id
        #     action="catalog_view", 
        #     timestamp=datetime.now(timezone.utc) - timedelta(hours=6),
        #     extra_data=json.dumps({})
        # )
        
        # db_session.add_all([purchase1, purchase2, activity1, activity2])  # ❌ Активности закомментированы для MVP
        db_session.add_all([purchase1, purchase2])
        await db_session.commit()
        
        return {
            'users': [user1, user2, user3],
            'lesson': lesson1,
            'purchases': [purchase1, purchase2],
            # 'activities': [activity1, activity2]  # ❌ Закомментировано для MVP
        }

    async def test_get_all_users(self, user_management_service: UserManagementService, sample_users_data):
        """Тест получения всех пользователей"""
        users = await user_management_service.get_all_users()
        
        assert len(users) == 3
        
        # Проверяем, что пользователи отсортированы по дате регистрации (новые первые)
        user_ids = [user.user_id for user in users]
        assert 33333 in user_ids  # John Smith (самый новый)
        assert 11111 in user_ids  # Иван Иванов 
        assert 22222 in user_ids  # Мария Петрова (самый старый)

    async def test_get_users_with_pagination(self, user_management_service: UserManagementService, sample_users_data):
        """Тест получения пользователей с пагинацией"""
        # Первая страница (2 пользователя)
        users_page1 = await user_management_service.get_all_users(limit=2, offset=0)
        assert len(users_page1) == 2
        
        # Вторая страница (1 пользователь)
        users_page2 = await user_management_service.get_all_users(limit=2, offset=2)
        assert len(users_page2) == 1

    async def test_get_user_by_id(self, user_management_service: UserManagementService, sample_users_data):
        """Тест получения пользователя по ID"""
        user = await user_management_service.get_user_by_id(11111)
        
        assert user is not None
        assert user.user_id == 11111
        assert user.full_name == "Иван Иванов"
        assert user.username == "ivan_ivanov"

    async def test_get_user_by_id_not_found(self, user_management_service: UserManagementService):
        """Тест получения несуществующего пользователя"""
        user = await user_management_service.get_user_by_id(99999)
        assert user is None

    async def test_search_users_by_username(self, user_management_service: UserManagementService, sample_users_data):
        """Тест поиска пользователей по username"""
        users = await user_management_service.search_users("ivan")
        
        assert len(users) == 1
        assert users[0].username == "ivan_ivanov"

    async def test_search_users_by_full_name(self, user_management_service: UserManagementService, sample_users_data):
        """Тест поиска пользователей по полному имени"""
        users = await user_management_service.search_users("Мария")  # Точное соответствие регистра
        
        assert len(users) == 1
        assert users[0].full_name == "Мария Петрова"

    async def test_search_users_by_user_id(self, user_management_service: UserManagementService, sample_users_data):
        """Тест поиска пользователей по user_id"""
        users = await user_management_service.search_users("33333")
        
        assert len(users) == 1
        assert users[0].user_id == 33333

    async def test_block_user(self, user_management_service: UserManagementService, sample_users_data):
        """Тест блокировки пользователя"""
        success = await user_management_service.block_user(11111)
        
        assert success is True
        
        # Проверяем, что пользователь заблокирован
        user = await user_management_service.get_user_by_id(11111)
        assert user.is_active is False

    async def test_unblock_user(self, user_management_service: UserManagementService, sample_users_data):
        """Тест разблокировки пользователя"""
        success = await user_management_service.unblock_user(22222)
        
        assert success is True
        
        # Проверяем, что пользователь разблокирован
        user = await user_management_service.get_user_by_id(22222)
        assert user.is_active is True

    async def test_block_nonexistent_user(self, user_management_service: UserManagementService):
        """Тест блокировки несуществующего пользователя"""
        success = await user_management_service.block_user(99999)
        assert success is False

    async def test_get_user_statistics(self, user_management_service: UserManagementService, sample_users_data):
        """Тест получения статистики пользователя"""
        stats = await user_management_service.get_user_statistics(11111)
        
        assert stats is not None
        assert stats['user_id'] == 11111
        assert stats['total_purchases'] == 1
        assert stats['total_spent'] == 100
        assert stats['total_activities'] == 1
        assert stats['registration_date'] is not None
        assert stats['last_activity'] is not None

    async def test_get_user_statistics_no_purchases(self, user_management_service: UserManagementService, sample_users_data):
        """Тест получения статистики пользователя без покупок"""
        stats = await user_management_service.get_user_statistics(22222)
        
        assert stats is not None
        assert stats['user_id'] == 22222
        assert stats['total_purchases'] == 0
        assert stats['total_spent'] == 0
        assert stats['total_activities'] == 0

    async def test_get_user_purchases(self, user_management_service: UserManagementService, sample_users_data):
        """Тест получения покупок пользователя"""
        purchases = await user_management_service.get_user_purchases(11111)
        
        assert len(purchases) == 1
        assert purchases[0].amount_stars == 100
        assert purchases[0].status == "completed"

    async def test_get_active_users(self, user_management_service: UserManagementService, sample_users_data):
        """Тест получения активных пользователей"""
        active_users = await user_management_service.get_active_users()
        
        # Должно быть 2 активных пользователя (user1 и user3)
        assert len(active_users) == 2
        
        active_user_ids = [user.user_id for user in active_users]
        assert 11111 in active_user_ids
        assert 33333 in active_user_ids
        assert 22222 not in active_user_ids  # Заблокированный

    async def test_get_blocked_users(self, user_management_service: UserManagementService, sample_users_data):
        """Тест получения заблокированных пользователей"""
        blocked_users = await user_management_service.get_blocked_users()
        
        # Должен быть 1 заблокированный пользователь (user2)
        assert len(blocked_users) == 1
        assert blocked_users[0].user_id == 22222

    async def test_get_recent_users(self, user_management_service: UserManagementService, sample_users_data):
        """Тест получения недавно зарегистрированных пользователей"""
        recent_users = await user_management_service.get_recent_users(days=15)
        
        # За последние 15 дней должен быть 1 пользователь (John Smith)
        assert len(recent_users) == 1
        assert recent_users[0].user_id == 33333

    async def test_get_top_buyers(self, user_management_service: UserManagementService, sample_users_data):
        """Тест получения топ покупателей"""
        top_buyers = await user_management_service.get_top_buyers(limit=5)
        
        # Должно быть 2 покупателя
        assert len(top_buyers) == 2
        
        # Проверяем сортировку по общей сумме трат
        buyer_data = [(buyer['user_id'], buyer['total_spent']) for buyer in top_buyers]
        
        # user1 потратил больше чем user3
        user1_data = next((data for data in buyer_data if data[0] == 11111), None)
        user3_data = next((data for data in buyer_data if data[0] == 33333), None)
        
        assert user1_data is not None
        assert user3_data is not None

    async def test_delete_user(self, user_management_service: UserManagementService, sample_users_data):
        """Тест удаления пользователя"""
        success = await user_management_service.delete_user(22222)
        
        assert success is True
        
        # Проверяем, что пользователь удален
        user = await user_management_service.get_user_by_id(22222)
        assert user is None

    async def test_delete_nonexistent_user(self, user_management_service: UserManagementService):
        """Тест удаления несуществующего пользователя"""
        success = await user_management_service.delete_user(99999)
        assert success is False