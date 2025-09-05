"""
Тесты для сервиса управления текстами интерфейса
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import TextSetting
from services.text import TextService


class TestTextService:
    """Тесты для TextService"""

    @pytest.fixture
    async def text_service(self, db_session):
        """Фикстура для создания TextService"""
        return TextService(db_session)

    @pytest.fixture
    async def sample_text_settings(self):
        """Создание тестовых настроек текстов"""
        return [
            TextSetting(
                id=1,
                key="welcome_message",
                value_ru="🤖 Добро пожаловать в мир ИИ!",
                value_en="🤖 Welcome to the AI world!",
                category="messages",
                description="Приветственное сообщение",
                updated_at=datetime.now(timezone.utc)
            ),
            TextSetting(
                id=2,
                key="button_catalog",
                value_ru="🧠 AI-курсы",
                value_en="🧠 AI Courses",
                category="buttons",
                description="Кнопка каталога",
                updated_at=datetime.now(timezone.utc)
            ),
            TextSetting(
                id=3,
                key="error_payment",
                value_ru="❌ Ошибка при оплате курса",
                value_en="❌ Course payment error",
                category="errors",
                description="Сообщение об ошибке оплаты",
                updated_at=datetime.now(timezone.utc)
            )
        ]

    async def test_get_all_text_settings(self, text_service, db_session, sample_text_settings):
        """Тест получения всех настроек текстов"""
        # Мокируем результат выполнения запроса
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = sample_text_settings
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            texts = await text_service.get_all_text_settings()
            
            assert len(texts) == 3
            assert texts[0].key == "welcome_message"
            assert texts[1].category == "buttons"
            assert texts[2].value_ru == "❌ Ошибка при оплате"

    async def test_get_text_settings_by_category(self, text_service, db_session, sample_text_settings):
        """Тест получения настроек текстов по категории"""
        button_settings = [sample_text_settings[1]]  # Только кнопки
        
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = button_settings
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            texts = await text_service.get_text_settings_by_category("buttons")
            
            assert len(texts) == 1
            assert texts[0].category == "buttons"
            assert texts[0].key == "button_catalog"

    async def test_get_text_setting_by_key(self, text_service, db_session, sample_text_settings):
        """Тест получения настройки по ключу"""
        welcome_setting = sample_text_settings[0]
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = welcome_setting
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            text = await text_service.get_text_setting_by_key("welcome_message")
            
            assert text is not None
            assert text.key == "welcome_message"
            assert text.value_ru == "Добро пожаловать в наш бот!"

    async def test_get_text_setting_by_key_not_found(self, text_service, db_session):
        """Тест получения несуществующей настройки"""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            text = await text_service.get_text_setting_by_key("nonexistent_key")
            
            assert text is None

    async def test_create_text_setting(self, text_service, db_session):
        """Тест создания новой настройки текста"""
        new_text = TextSetting(
            key="new_message",
            value_ru="Новое сообщение",
            value_en="New message",
            category="messages",
            description="Тестовое сообщение"
        )
        
        db_session.add = AsyncMock()
        db_session.commit = AsyncMock()
        db_session.refresh = AsyncMock()
        
        result = await text_service.create_text_setting(
            key="new_message",
            value_ru="Новое сообщение",
            value_en="New message",
            category="messages",
            description="Тестовое сообщение"
        )
        
        # Проверяем, что объект был добавлен в сессию
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()
        
        # Проверяем возвращаемый объект
        assert result.key == "new_message"
        assert result.value_ru == "Новое сообщение"
        assert result.category == "messages"

    async def test_update_text_setting(self, text_service, db_session, sample_text_settings):
        """Тест обновления настройки текста"""
        existing_text = sample_text_settings[0]
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = existing_text
        
        db_session.commit = AsyncMock()
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            updated_text = await text_service.update_text_setting(
                key="welcome_message",
                value_ru="Обновленное приветствие",
                value_en="Updated welcome"
            )
            
            assert updated_text is not None
            assert updated_text.value_ru == "Обновленное приветствие"
            assert updated_text.value_en == "Updated welcome"
            db_session.commit.assert_called_once()

    async def test_update_text_setting_not_found(self, text_service, db_session):
        """Тест обновления несуществующей настройки"""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            result = await text_service.update_text_setting(
                key="nonexistent_key",
                value_ru="Новый текст"
            )
            
            assert result is None

    async def test_delete_text_setting(self, text_service, db_session, sample_text_settings):
        """Тест удаления настройки текста"""
        existing_text = sample_text_settings[0]
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = existing_text
        
        db_session.delete = AsyncMock()
        db_session.commit = AsyncMock()
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            success = await text_service.delete_text_setting("welcome_message")
            
            assert success is True
            db_session.delete.assert_called_once_with(existing_text)
            db_session.commit.assert_called_once()

    async def test_delete_text_setting_not_found(self, text_service, db_session):
        """Тест удаления несуществующей настройки"""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            success = await text_service.delete_text_setting("nonexistent_key")
            
            assert success is False

    async def test_get_text_value(self, text_service, db_session, sample_text_settings):
        """Тест получения значения текста по ключу и языку"""
        welcome_setting = sample_text_settings[0]
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = welcome_setting
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            # Тест для русского языка
            value_ru = await text_service.get_text_value("welcome_message", "ru")
            assert value_ru == "Добро пожаловать в наш бот!"
            
            # Тест для английского языка
            value_en = await text_service.get_text_value("welcome_message", "en")
            assert value_en == "Welcome to our bot!"

    async def test_get_text_value_fallback_to_russian(self, text_service, db_session):
        """Тест fallback на русский язык если английский отсутствует"""
        text_setting = TextSetting(
            key="test_message",
            value_ru="Русский текст",
            value_en=None,
            category="messages"
        )
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = text_setting
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            value = await text_service.get_text_value("test_message", "en")
            assert value == "Русский текст"  # Fallback к русскому

    async def test_get_text_value_not_found(self, text_service, db_session):
        """Тест получения значения несуществующего текста"""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            value = await text_service.get_text_value("nonexistent_key", "ru")
            assert value is None

    async def test_get_categories_list(self, text_service, db_session):
        """Тест получения списка категорий"""
        categories_result = [("messages",), ("buttons",), ("errors",)]
        
        mock_result = AsyncMock()
        mock_result.fetchall.return_value = categories_result
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            categories = await text_service.get_categories_list()
            
            assert len(categories) == 3
            assert "messages" in categories
            assert "buttons" in categories
            assert "errors" in categories

    async def test_bulk_update_texts(self, text_service, db_session, sample_text_settings):
        """Тест массового обновления текстов"""
        updates = [
            {"key": "welcome_message", "value_ru": "Новое приветствие", "value_en": "New welcome"},
            {"key": "button_catalog", "value_ru": "📖 Уроки", "value_en": "📖 Lessons"}
        ]
        
        # Мокируем получение существующих настроек
        mock_results = [
            AsyncMock(scalar_one_or_none=AsyncMock(return_value=sample_text_settings[0])),
            AsyncMock(scalar_one_or_none=AsyncMock(return_value=sample_text_settings[1]))
        ]
        
        db_session.commit = AsyncMock()
        
        with patch.object(db_session, 'execute', side_effect=mock_results):
            success_count = await text_service.bulk_update_texts(updates)
            
            assert success_count == 2
            db_session.commit.assert_called()

    async def test_search_text_settings(self, text_service, db_session, sample_text_settings):
        """Тест поиска настроек текстов"""
        search_results = [sample_text_settings[0]]  # Только приветствие
        
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = search_results
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            results = await text_service.search_text_settings("приветствие")
            
            assert len(results) == 1
            assert results[0].key == "welcome_message"

    async def test_get_text_statistics(self, text_service, db_session, sample_text_settings):
        """Тест получения статистики по текстам"""
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = sample_text_settings
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            stats = await text_service.get_text_statistics()
            
            assert stats['total_texts'] == 3
            assert stats['categories_count'] == 3
            assert 'messages' in stats['category_distribution']
            assert 'buttons' in stats['category_distribution']
            assert 'errors' in stats['category_distribution']
            assert stats['texts_with_translation'] == 3  # Все тексты имеют перевод

    async def test_error_handling_in_create(self, text_service, db_session):
        """Тест обработки ошибок при создании"""
        db_session.add = AsyncMock()
        db_session.commit = AsyncMock(side_effect=Exception("Database error"))
        db_session.rollback = AsyncMock()
        
        result = await text_service.create_text_setting(
            key="test_key",
            value_ru="Тест",
            category="messages"
        )
        
        assert result is None
        db_session.rollback.assert_called_once()

    async def test_error_handling_in_update(self, text_service, db_session, sample_text_settings):
        """Тест обработки ошибок при обновлении"""
        existing_text = sample_text_settings[0]
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = existing_text
        
        db_session.commit = AsyncMock(side_effect=Exception("Database error"))
        db_session.rollback = AsyncMock()
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            result = await text_service.update_text_setting(
                key="welcome_message",
                value_ru="Новый текст"
            )
            
            assert result is None
            db_session.rollback.assert_called_once()

    async def test_validate_text_key_format(self, text_service):
        """Тест валидации формата ключа"""
        # Валидные ключи
        assert text_service.validate_key_format("welcome_message") is True
        assert text_service.validate_key_format("button_catalog") is True
        assert text_service.validate_key_format("error_payment_failed") is True
        
        # Невалидные ключи
        assert text_service.validate_key_format("Welcome Message") is False  # Пробелы
        assert text_service.validate_key_format("button-catalog") is False   # Дефисы
        assert text_service.validate_key_format("123_start") is False        # Начинается с цифры
        assert text_service.validate_key_format("") is False                 # Пустая строка

    async def test_export_texts_for_translation(self, text_service, db_session, sample_text_settings):
        """Тест экспорта текстов для перевода"""
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = sample_text_settings
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            export_data = await text_service.export_texts_for_translation()
            
            assert len(export_data) == 3
            assert export_data[0]['key'] == 'welcome_message'
            assert export_data[0]['value_ru'] == 'Добро пожаловать в наш бот!'
            assert export_data[0]['value_en'] == 'Welcome to our bot!'
            assert export_data[0]['category'] == 'messages'