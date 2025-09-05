"""
Тесты для StatisticsService
"""
import pytest
from datetime import datetime, timedelta
import json
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Lesson, Purchase, Admin
# from database.models import UserActivity  # ❌ Закомментировано для MVP
from services.statistics import StatisticsService


class TestStatisticsService:
    """Тесты для сервиса статистики"""

    @pytest.fixture
    async def statistics_service(self, db_session: AsyncSession):
        """Фикстура для создания StatisticsService"""
        return StatisticsService(db_session)

    @pytest.fixture
    async def sample_data(self, db_session: AsyncSession):
        """Создание тестовых данных"""
        # Создаем пользователей
        user1 = User(
            user_id=11111,
            full_name="John Doe",
            username="john_doe",
            language="ru",
            registration_date=datetime.utcnow() - timedelta(days=30),
            last_activity=datetime.utcnow() - timedelta(days=1)
        )
        user2 = User(
            user_id=22222,
            full_name="Jane Smith", 
            username="jane_smith",
            language="en",
            registration_date=datetime.utcnow() - timedelta(days=60),
            last_activity=datetime.utcnow() - timedelta(days=40)  # Неактивный пользователь
        )
        
        # Создаем уроки по ИИ и нейросетям
        lesson1 = Lesson(
            title="Основы нейронных сетей",
            description="Изучение принципов работы нейронных сетей",
            price_stars=100,
            is_active=True,
            is_free=False,
            file_id="test_file_1",
            content_type="video"
        )
        lesson2 = Lesson(
            title="Продвинутые техники машинного обучения",
            description="Глубокое обучение и современные алгоритмы", 
            price_stars=200,
            is_active=True,
            is_free=False,
            file_id="test_file_2",
            content_type="video"
        )
        lesson3 = Lesson(
            title="Бесплатное введение в ИИ",
            description="Краткий обзор современных технологий ИИ",
            price_stars=0,
            is_active=True,
            is_free=True,
            file_id="test_file_3",
            content_type="video"
        )
        
        db_session.add_all([user1, user2, lesson1, lesson2, lesson3])
        await db_session.flush()  # Получаем ID
        
        # Создаем покупки
        purchase1 = Purchase(
            user_id=user1.id,
            lesson_id=lesson1.id,
            payment_charge_id="test_charge_1",
            amount_stars=100,
            status="completed",
            purchase_date=datetime.utcnow() - timedelta(days=5)
        )
        purchase2 = Purchase(
            user_id=user1.id,
            lesson_id=lesson2.id,
            payment_charge_id="test_charge_2",
            amount_stars=200,
            status="completed",
            purchase_date=datetime.utcnow() - timedelta(days=2)
        )
        
        # Создаем активность пользователей - ❌ Закомментировано для MVP
        # activity1 = UserActivity(
        #     user_id=user1.id,
        #     action="lesson_view",
        #     timestamp=datetime.utcnow() - timedelta(days=1),
        #     extra_data=json.dumps({"lesson_id": lesson1.id})
        # )
        # activity2 = UserActivity(
        #     user_id=user1.id,
        #     action="catalog_view",
        #     timestamp=datetime.utcnow() - timedelta(hours=6),
        #     extra_data=json.dumps({})
        # )
        
        # db_session.add_all([purchase1, purchase2, activity1, activity2])  # ❌ Активности закомментированы для MVP
        db_session.add_all([purchase1, purchase2])
        await db_session.commit()
        
        return {
            'users': [user1, user2],
            'lessons': [lesson1, lesson2, lesson3],
            'purchases': [purchase1, purchase2],
            # 'activities': [activity1, activity2]  # ❌ Закомментировано для MVP
        }

    async def test_get_general_stats(self, statistics_service: StatisticsService, sample_data):
        """Тест получения общей статистики"""
        stats = await statistics_service.get_general_stats()
        
        assert stats is not None
        assert stats['total_users'] == 2
        assert stats['active_users'] == 1  # Только user1 активен в последние 30 дней
        assert stats['total_lessons'] == 3
        assert stats['active_lessons'] == 3
        assert stats['total_purchases'] == 2
        assert stats['total_revenue'] == 300  # 100 + 200
        assert stats['revenue_per_user'] == 150.0  # 300 / 2

    async def test_get_revenue_stats(self, statistics_service: StatisticsService, sample_data):
        """Тест получения статистики доходов"""
        stats = await statistics_service.get_revenue_stats(30)  # За последние 30 дней
        
        assert stats is not None
        assert stats['period_days'] == 30
        assert stats['period_revenue'] == 300  # Обе покупки в пределах 30 дней
        assert stats['period_purchases'] == 2
        assert stats['avg_purchase'] == 150.0  # 300 / 2
        assert len(stats['daily_revenue']) == 7  # Статистика по 7 дням

    async def test_get_top_lessons(self, statistics_service: StatisticsService, sample_data):
        """Тест получения топ уроков"""
        top_lessons = await statistics_service.get_top_lessons(10)
        
        assert len(top_lessons) == 2  # 2 урока с продажами
        
        # Проверяем первый урок (может быть любой из двух)
        first_lesson = top_lessons[0]
        assert first_lesson['title'] in ['Python Basics', 'Advanced Python']
        assert first_lesson['sales'] == 1
        assert first_lesson['revenue'] in [100, 200]

    async def test_get_user_activity_stats(self, statistics_service: StatisticsService, sample_data):
        """Тест получения статистики активности пользователей"""
        activity_stats = await statistics_service.get_user_activity_stats(7)
        
        assert len(activity_stats) == 7  # 7 дней
        
        # Проверяем структуру данных
        for day_stat in activity_stats:
            assert 'date' in day_stat
            assert 'unique_users' in day_stat
            assert 'total_actions' in day_stat

    async def test_get_conversion_stats(self, statistics_service: StatisticsService, sample_data):
        """Тест получения статистики конверсии"""
        conversion_stats = await statistics_service.get_conversion_stats()
        
        assert conversion_stats is not None
        assert conversion_stats['total_users'] == 2
        assert conversion_stats['buyers'] == 1  # Только user1 купил уроки
        assert conversion_stats['conversion_rate'] == 50.0  # 1/2 * 100%
        assert conversion_stats['avg_purchases_per_buyer'] == 2.0  # user1 купил 2 урока

    async def test_empty_stats(self, statistics_service: StatisticsService):
        """Тест статистики при отсутствии данных"""
        stats = await statistics_service.get_general_stats()
        
        assert stats is not None
        assert stats['total_users'] == 0
        assert stats['active_users'] == 0
        assert stats['total_lessons'] == 0
        assert stats['active_lessons'] == 0
        assert stats['total_purchases'] == 0
        assert stats['total_revenue'] == 0
        assert stats['revenue_per_user'] == 0

    async def test_revenue_stats_empty(self, statistics_service: StatisticsService):
        """Тест статистики доходов при отсутствии данных"""
        stats = await statistics_service.get_revenue_stats(30)
        
        assert stats is not None
        assert stats['period_revenue'] == 0
        assert stats['period_purchases'] == 0
        assert stats['avg_purchase'] == 0
        assert len(stats['daily_revenue']) == 7

    async def test_top_lessons_empty(self, statistics_service: StatisticsService):
        """Тест топ уроков при отсутствии продаж"""
        top_lessons = await statistics_service.get_top_lessons(10)
        
        assert len(top_lessons) == 0