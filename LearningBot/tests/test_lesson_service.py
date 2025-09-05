"""
Тесты для сервиса управления уроками
"""
import pytest
from datetime import datetime

from services.lesson import LessonService
from database.models import Lesson, Purchase


class TestLessonService:
    """Тесты для LessonService"""

    @pytest.mark.asyncio
    async def test_get_lesson_by_id_existing(self, lesson_service, sample_lesson):
        """Тест получения существующего урока по ID"""
        lesson = await lesson_service.get_lesson_by_id(sample_lesson.id)
        
        assert lesson is not None
        assert lesson.id == sample_lesson.id
        assert lesson.title == sample_lesson.title
        assert lesson.price_stars == sample_lesson.price_stars

    @pytest.mark.asyncio
    async def test_get_lesson_by_id_not_existing(self, lesson_service):
        """Тест получения несуществующего урока"""
        lesson = await lesson_service.get_lesson_by_id(999999)
        
        assert lesson is None

    @pytest.mark.asyncio
    async def test_get_lesson_by_id_inactive(self, lesson_service, db_session):
        """Тест получения неактивного урока (должен вернуть None)"""
        # Создаем неактивный урок
        inactive_lesson = Lesson(
            title="Неактивный урок",
            description="Этот урок отключен",
            price_stars=50,
            content_type="text",
            is_active=False,  # Неактивный
            is_free=False,
            category="Тест"
        )
        
        db_session.add(inactive_lesson)
        await db_session.commit()
        await db_session.refresh(inactive_lesson)
        
        # Попытка получить неактивный урок
        result = await lesson_service.get_lesson_by_id(inactive_lesson.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_free_lessons(self, lesson_service, sample_free_lesson):
        """Тест получения бесплатных уроков"""
        lessons = await lesson_service.get_free_lessons()
        
        assert len(lessons) >= 1
        # Проверяем, что все уроки бесплатные
        for lesson in lessons:
            assert lesson.is_free is True
            assert lesson.is_active is True

    @pytest.mark.asyncio
    async def test_get_lessons_paginated_default(self, lesson_service, sample_lesson):
        """Тест получения уроков с пагинацией (по умолчанию)"""
        lessons, total_count = await lesson_service.get_lessons_paginated()
        
        assert isinstance(lessons, list)
        assert isinstance(total_count, int)
        assert total_count >= 1
        assert len(lessons) <= 10  # Лимит по умолчанию

    @pytest.mark.asyncio
    async def test_get_lessons_paginated_with_category(self, lesson_service, sample_lesson):
        """Тест получения уроков с фильтром по категории"""
        lessons, total_count = await lesson_service.get_lessons_paginated(
            category=sample_lesson.category
        )
        
        assert isinstance(lessons, list) 
        assert total_count >= 1
        # Проверяем, что все уроки из нужной категории
        for lesson in lessons:
            assert lesson.category == sample_lesson.category

    @pytest.mark.asyncio
    async def test_get_lessons_paginated_with_search(self, lesson_service, sample_lesson):
        """Тест поиска уроков по запросу"""
        search_query = sample_lesson.title[:5]  # Первые 5 символов названия
        
        lessons, total_count = await lesson_service.get_lessons_paginated(
            search_query=search_query
        )
        
        assert isinstance(lessons, list)
        # Должен найти как минимум наш тестовый урок
        found_lesson = any(lesson.id == sample_lesson.id for lesson in lessons)
        assert found_lesson is True

    @pytest.mark.asyncio
    async def test_check_user_has_lesson_with_purchase(self, lesson_service, sample_user, sample_lesson, sample_purchase):
        """Тест проверки доступа к уроку у пользователя с покупкой"""
        has_access = await lesson_service.check_user_has_lesson(
            sample_user.user_id, 
            sample_lesson.id
        )
        
        assert has_access is True

    @pytest.mark.asyncio
    async def test_check_user_has_lesson_without_purchase(self, lesson_service, sample_user, sample_lesson):
        """Тест проверки доступа к уроку у пользователя без покупки"""
        has_access = await lesson_service.check_user_has_lesson(
            sample_user.user_id, 
            sample_lesson.id
        )
        
        assert has_access is False

    @pytest.mark.asyncio
    async def test_check_user_has_lesson_free_lesson(self, lesson_service, sample_user, sample_free_lesson):
        """Тест проверки доступа к бесплатному уроку"""
        has_access = await lesson_service.check_user_has_lesson(
            sample_user.user_id, 
            sample_free_lesson.id
        )
        
        assert has_access is True  # Бесплатные уроки доступны всем

    @pytest.mark.asyncio
    async def test_get_user_purchases(self, lesson_service, sample_user, sample_purchase):
        """Тест получения покупок пользователя"""
        purchases, total_count = await lesson_service.get_user_purchases(
            sample_user.user_id
        )
        
        assert isinstance(purchases, list)
        assert isinstance(total_count, int)
        assert total_count >= 1
        assert len(purchases) >= 1
        
        # Проверяем структуру данных
        purchase_data = purchases[0]
        assert 'purchase' in purchase_data
        assert 'lesson' in purchase_data
        assert purchase_data['purchase'].user_id == sample_user.user_id

    @pytest.mark.asyncio
    async def test_get_user_purchases_pagination(self, lesson_service, sample_user, sample_purchase):
        """Тест пагинации покупок пользователя"""
        purchases, total_count = await lesson_service.get_user_purchases(
            sample_user.user_id,
            page=0,
            per_page=1
        )
        
        assert len(purchases) <= 1
        assert total_count >= 1

    @pytest.mark.asyncio
    async def test_increment_lesson_views(self, lesson_service, sample_lesson):
        """Тест увеличения счетчика просмотров урока"""
        initial_views = sample_lesson.views_count
        
        success = await lesson_service.increment_lesson_views(sample_lesson.id)
        
        assert success is True
        
        # Получаем обновленный урок
        updated_lesson = await lesson_service.get_lesson_by_id(sample_lesson.id)
        assert updated_lesson.views_count == initial_views + 1

    @pytest.mark.asyncio
    async def test_increment_lesson_views_multiple(self, lesson_service, sample_lesson):
        """Тест множественного увеличения счетчика просмотров"""
        initial_views = sample_lesson.views_count
        increment_count = 5
        
        for _ in range(increment_count):
            success = await lesson_service.increment_lesson_views(sample_lesson.id)
            assert success is True
        
        # Проверяем финальный счетчик
        updated_lesson = await lesson_service.get_lesson_by_id(sample_lesson.id)
        assert updated_lesson.views_count == initial_views + increment_count

    @pytest.mark.asyncio
    async def test_search_lessons(self, lesson_service, sample_lesson):
        """Тест поиска уроков"""
        search_query = "Тестовый"
        
        lessons, total_count = await lesson_service.search_lessons(search_query)
        
        assert isinstance(lessons, list)
        assert total_count >= 1
        
        # Проверяем, что найденные уроки содержат поисковый запрос
        found_lesson = any(
            search_query.lower() in lesson.title.lower() or 
            search_query.lower() in lesson.description.lower()
            for lesson in lessons
        )
        assert found_lesson is True

    @pytest.mark.asyncio
    async def test_get_popular_lessons(self, lesson_service, sample_lesson):
        """Тест получения популярных уроков"""
        # Увеличиваем просмотры для создания популярности
        await lesson_service.increment_lesson_views(sample_lesson.id)
        await lesson_service.increment_lesson_views(sample_lesson.id)
        
        popular_lessons = await lesson_service.get_popular_lessons(limit=5)
        
        assert isinstance(popular_lessons, list)
        assert len(popular_lessons) <= 5
        
        # Проверяем, что уроки отсортированы по убыванию просмотров
        if len(popular_lessons) > 1:
            for i in range(len(popular_lessons) - 1):
                assert popular_lessons[i].views_count >= popular_lessons[i + 1].views_count

    @pytest.mark.asyncio
    async def test_get_lesson_categories(self, lesson_service, sample_lesson):
        """Тест получения списка категорий уроков"""
        categories = await lesson_service.get_lesson_categories()
        
        assert isinstance(categories, list)
        assert len(categories) >= 1
        assert sample_lesson.category in categories
    
    # ========== ТЕСТЫ CRUD ОПЕРАЦИЙ ==========
    
    @pytest.mark.asyncio
    async def test_create_lesson_success(self, lesson_service):
        """Тест успешного создания урока"""
        lesson_data = {
            'title': 'Новый тестовый урок',
            'description': 'Описание нового урока',
            'price_stars': 100,
            'category': 'Программирование',
            'content_type': 'video',
            'file_id': 'test_file_id_123',
            'duration': 300
        }
        
        new_lesson = await lesson_service.create_lesson(lesson_data)
        
        assert new_lesson is not None
        assert new_lesson.title == lesson_data['title']
        assert new_lesson.description == lesson_data['description']
        assert new_lesson.price_stars == lesson_data['price_stars']
        assert new_lesson.category == lesson_data['category']
        assert new_lesson.content_type == lesson_data['content_type']
        assert new_lesson.file_id == lesson_data['file_id']
        assert new_lesson.duration == lesson_data['duration']
        assert new_lesson.is_free is False
        assert new_lesson.is_active is True
        assert new_lesson.views_count == 0
        assert new_lesson.id is not None
    
    @pytest.mark.asyncio
    async def test_create_lesson_free(self, lesson_service):
        """Тест создания бесплатного урока"""
        lesson_data = {
            'title': 'Бесплатный урок',
            'description': 'Описание бесплатного урока',
            'price_stars': 0,  # Бесплатно
            'category': 'Обучение',
            'content_type': 'text'
        }
        
        new_lesson = await lesson_service.create_lesson(lesson_data)
        
        assert new_lesson is not None
        assert new_lesson.price_stars == 0
        assert new_lesson.is_free is True
    
    @pytest.mark.asyncio
    async def test_create_lesson_missing_fields(self, lesson_service):
        """Тест создания урока с недостающими полями"""
        lesson_data = {
            'title': 'Неполный урок',
            # Отсутствуют обязательные поля
        }
        
        new_lesson = await lesson_service.create_lesson(lesson_data)
        
        assert new_lesson is None
    
    # ========== ТЕСТЫ УПДЕЙТ ОПЕРАЦИЙ ==========
    
    @pytest.mark.asyncio
    async def test_update_lesson_title(self, lesson_service, sample_lesson):
        """Тест обновления названия урока"""
        new_title = 'Обновленное название урока'
        
        success = await lesson_service.update_lesson_title(sample_lesson.id, new_title)
        
        assert success is True
        
        # Проверяем, что название обновлено
        updated_lesson = await lesson_service.get_lesson_by_id(sample_lesson.id)
        assert updated_lesson.title == new_title
    
    @pytest.mark.asyncio
    async def test_update_lesson_description(self, lesson_service, sample_lesson):
        """Тест обновления описания урока"""
        new_description = 'Обновленное описание урока с подробностями'
        
        success = await lesson_service.update_lesson_description(sample_lesson.id, new_description)
        
        assert success is True
        
        # Проверяем, что описание обновлено
        updated_lesson = await lesson_service.get_lesson_by_id(sample_lesson.id)
        assert updated_lesson.description == new_description
    
    @pytest.mark.asyncio
    async def test_update_lesson_price(self, lesson_service, sample_lesson):
        """Тест обновления цены урока"""
        new_price = 250
        
        success = await lesson_service.update_lesson_price(sample_lesson.id, new_price)
        
        assert success is True
        
        # Проверяем, что цена обновлена
        updated_lesson = await lesson_service.get_lesson_by_id(sample_lesson.id)
        assert updated_lesson.price_stars == new_price
        assert updated_lesson.is_free is False
    
    @pytest.mark.asyncio
    async def test_update_lesson_price_to_free(self, lesson_service, sample_lesson):
        """Тест обновления цены урока до бесплатного"""
        new_price = 0
        
        success = await lesson_service.update_lesson_price(sample_lesson.id, new_price)
        
        assert success is True
        
        # Проверяем, что урок стал бесплатным
        updated_lesson = await lesson_service.get_lesson_by_id(sample_lesson.id)
        assert updated_lesson.price_stars == 0
        assert updated_lesson.is_free is True
    
    @pytest.mark.asyncio
    async def test_update_lesson_status(self, lesson_service, sample_lesson):
        """Тест обновления статуса активности урока"""
        # Деактивируем урок
        success = await lesson_service.update_lesson_status(sample_lesson.id, False)
        
        assert success is True
        
        # Проверяем, что урок деактивирован
        updated_lesson = await lesson_service.get_lesson_by_id(sample_lesson.id, include_inactive=True)
        assert updated_lesson.is_active is False
        
        # Активируем обратно
        success = await lesson_service.update_lesson_status(sample_lesson.id, True)
        assert success is True
        
        updated_lesson = await lesson_service.get_lesson_by_id(sample_lesson.id)
        assert updated_lesson.is_active is True
    
    # ========== DELETE TESTS ==========
    
    @pytest.mark.asyncio
    async def test_can_delete_lesson_without_purchases(self, lesson_service, db_session):
        lesson = Lesson(
            title="Урок для удаления",
            description="Описание",
            price_stars=100,
            content_type="text",
            is_active=True,
            is_free=False,
            category="Тест"
        )
        db_session.add(lesson)
        await db_session.commit()
        await db_session.refresh(lesson)
        
        can_delete, reason = await lesson_service.can_delete_lesson(lesson.id)
        assert can_delete is True
        assert "безопасно" in reason
    
    @pytest.mark.asyncio
    async def test_can_delete_lesson_with_purchases(self, lesson_service, sample_lesson, sample_purchase):
        can_delete, reason = await lesson_service.can_delete_lesson(sample_lesson.id)
        assert can_delete is False
        assert "покупки" in reason
    
    @pytest.mark.asyncio
    async def test_soft_delete_lesson_success(self, lesson_service, db_session):
        lesson = Lesson(
            title="Мягкое удаление",
            description="Тест",
            price_stars=100,
            content_type="text",
            is_active=True,
            is_free=False,
            category="Тест"
        )
        db_session.add(lesson)
        await db_session.commit()
        await db_session.refresh(lesson)
        
        success = await lesson_service.soft_delete_lesson(lesson.id)
        assert success is True
        
        updated_lesson = await lesson_service.get_lesson_by_id(lesson.id, include_inactive=True)
        assert updated_lesson.is_active is False
    
    @pytest.mark.asyncio
    async def test_hard_delete_lesson_success(self, lesson_service, db_session):
        lesson = Lesson(
            title="Жесткое удаление",
            description="Тест",
            price_stars=100,
            content_type="text",
            is_active=True,
            is_free=False,
            category="Тест"
        )
        db_session.add(lesson)
        await db_session.commit()
        await db_session.refresh(lesson)
        lesson_id = lesson.id
        
        success = await lesson_service.delete_lesson(lesson_id, force=False)
        assert success is True
        
        deleted_lesson = await lesson_service.get_lesson_by_id(lesson_id, include_inactive=True)
        assert deleted_lesson is None
    
    @pytest.mark.asyncio
    async def test_hard_delete_lesson_with_purchases_fails(self, lesson_service, sample_lesson):
        success = await lesson_service.delete_lesson(sample_lesson.id, force=False)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_bulk_update_status(self, lesson_service, db_session):
        lessons = []
        for i in range(2):
            lesson = Lesson(
                title=f"Массовый тест {i}",
                description="Тест",
                price_stars=50,
                content_type="text",
                is_active=False,
                is_free=False,
                category="Тест"
            )
            lessons.append(lesson)
            db_session.add(lesson)
        
        await db_session.commit()
        for lesson in lessons:
            await db_session.refresh(lesson)
        
        lesson_ids = [lesson.id for lesson in lessons]
        result = await lesson_service.bulk_update_status(lesson_ids, True)
        
        assert result['success'] is True
        assert result['updated_count'] == 2