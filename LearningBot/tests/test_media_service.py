"""
Тесты для сервиса управления медиа-контентом
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO

from database.models import Lesson
from services.media import MediaService


class TestMediaService:
    """Тесты для MediaService"""

    @pytest.fixture
    async def media_service(self, db_session):
        """Фикстура для создания MediaService"""
        return MediaService(db_session)

    @pytest.fixture
    async def sample_lessons(self):
        """Создание тестовых уроков по ИИ с разными типами медиа"""
        return [
            Lesson(
                id=1,
                title="Нейронные сети на практике",
                description="Видео-урок о практическом применении нейронных сетей",
                price_stars=75,
                content_type="video",
                file_id="BAACAgIAAxkDAAIBYGI4",
                duration=300,
                is_active=True,
                category="Нейронные сети"
            ),
            Lesson(
                id=2,
                title="Архитектуры CNN",
                description="Инфографика с описанием сверточных нейронных сетей",
                price_stars=50,
                content_type="photo",
                file_id="AgACAgIAAxkBAAIBYWI4",
                is_active=True,
                category="Computer Vision"
            ),
            Lesson(
                id=3,
                title="Конспект: Машинное обучение",
                description="PDF-конспект по основам машинного обучения",
                price_stars=40,
                content_type="document",
                file_id="BQACAgIAAxkCAAIBYmI4",
                is_active=True,
                category="Машинное обучение"
            )
        ]

    async def test_get_media_by_type(self, media_service, db_session, sample_lessons):
        """Тест получения медиа по типу"""
        # Мокируем результат выполнения запроса
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all.return_value = [sample_lessons[0]]  # Только видео
        mock_result.scalars.return_value = mock_scalars
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            videos = await media_service.get_media_by_type("video")
            
            assert len(videos) == 1
            assert videos[0].content_type == "video"
            assert videos[0].title == "Видео урок"

    async def test_get_media_by_category(self, media_service, db_session, sample_lessons):
        """Тест получения медиа по категории"""
        video_lessons = [sample_lessons[0]]
        
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all.return_value = video_lessons
        mock_result.scalars.return_value = mock_scalars
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            media = await media_service.get_media_by_category("video_lessons")
            
            assert len(media) == 1
            assert media[0].category == "video_lessons"

    async def test_validate_media_file(self, media_service):
        """Тест валидации медиа файла"""
        # Валидные типы
        assert media_service.validate_media_file("video", 5 * 1024 * 1024) is True  # 5MB видео
        assert media_service.validate_media_file("photo", 10 * 1024 * 1024) is True  # 10MB фото
        assert media_service.validate_media_file("document", 20 * 1024 * 1024) is True  # 20MB документ
        assert media_service.validate_media_file("audio", 50 * 1024 * 1024) is True  # 50MB аудио
        
        # Невалидные типы
        assert media_service.validate_media_file("unknown", 1024) is False
        assert media_service.validate_media_file("", 1024) is False
        
        # Превышение размера
        assert media_service.validate_media_file("video", 51 * 1024 * 1024) is False  # Слишком большой видео
        assert media_service.validate_media_file("photo", 21 * 1024 * 1024) is False  # Слишком большое фото

    async def test_get_media_size_limits(self, media_service):
        """Тест получения ограничений размера для разных типов медиа"""
        limits = media_service.get_media_size_limits()
        
        assert limits['video'] == 50 * 1024 * 1024  # 50MB
        assert limits['photo'] == 20 * 1024 * 1024  # 20MB
        assert limits['document'] == 20 * 1024 * 1024  # 20MB
        assert limits['audio'] == 50 * 1024 * 1024  # 50MB

    async def test_get_supported_media_types(self, media_service):
        """Тест получения поддерживаемых типов медиа"""
        types = media_service.get_supported_media_types()
        
        expected_types = ['video', 'photo', 'document', 'audio']
        assert set(types) == set(expected_types)

    async def test_update_lesson_media(self, media_service, db_session, sample_lessons):
        """Тест обновления медиа урока"""
        lesson = sample_lessons[0]
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = lesson
        
        db_session.commit = AsyncMock()
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            result = await media_service.update_lesson_media(
                lesson_id=1,
                content_type="video",
                file_id="NEW_FILE_ID",
                duration=450
            )
            
            assert result is not None
            assert result.file_id == "NEW_FILE_ID"
            assert result.content_type == "video"
            assert result.duration == 450
            db_session.commit.assert_called_once()

    async def test_update_lesson_media_not_found(self, media_service, db_session):
        """Тест обновления медиа несуществующего урока"""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            result = await media_service.update_lesson_media(
                lesson_id=999,
                content_type="video",
                file_id="FILE_ID"
            )
            
            assert result is None

    async def test_delete_lesson_media(self, media_service, db_session, sample_lessons):
        """Тест удаления медиа урока"""
        lesson = sample_lessons[0]
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = lesson
        
        db_session.commit = AsyncMock()
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            success = await media_service.delete_lesson_media(lesson_id=1)
            
            assert success is True
            assert lesson.file_id is None
            assert lesson.content_type == "text"  # Дефолтный тип
            assert lesson.duration is None
            db_session.commit.assert_called_once()

    async def test_get_media_statistics(self, media_service, db_session, sample_lessons):
        """Тест получения статистики медиа"""
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all.return_value = sample_lessons
        mock_result.scalars.return_value = mock_scalars
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            stats = await media_service.get_media_statistics()
            
            assert stats['total_media'] == 3
            assert stats['video_count'] == 1
            assert stats['photo_count'] == 1
            assert stats['document_count'] == 1
            assert stats['audio_count'] == 0
            assert 'categories' in stats
            assert 'video_lessons' in stats['categories']

    async def test_search_media(self, media_service, db_session, sample_lessons):
        """Тест поиска медиа контента"""
        search_results = [sample_lessons[0]]  # Только видео урок
        
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all.return_value = search_results
        mock_result.scalars.return_value = mock_scalars
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            results = await media_service.search_media("видео")
            
            assert len(results) == 1
            assert results[0].title == "Видео урок"

    async def test_get_media_by_lesson_id(self, media_service, db_session, sample_lessons):
        """Тест получения медиа по ID урока"""
        lesson = sample_lessons[0]
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = lesson
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            media = await media_service.get_media_by_lesson_id(1)
            
            assert media is not None
            assert media.id == 1
            assert media.content_type == "video"

    async def test_get_media_by_lesson_id_not_found(self, media_service, db_session):
        """Тест получения медиа несуществующего урока"""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            media = await media_service.get_media_by_lesson_id(999)
            
            assert media is None

    async def test_check_media_file_exists(self, media_service, db_session, sample_lessons):
        """Тест проверки существования медиа файла"""
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 1  # Файл существует
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            exists = await media_service.check_media_file_exists("BAACAgIAAxkDAAIBYGI4")
            
            assert exists is True

    async def test_check_media_file_not_exists(self, media_service, db_session):
        """Тест проверки несуществующего медиа файла"""
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 0  # Файл не существует
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            exists = await media_service.check_media_file_exists("NONEXISTENT_FILE_ID")
            
            assert exists is False

    async def test_get_duplicate_media_files(self, media_service, db_session, sample_lessons):
        """Тест поиска дублирующихся медиа файлов"""
        # Создаем урок с дублирующимся file_id
        duplicate_lesson = Lesson(
            id=4,
            title="Дублирующий урок",
            description="Урок с тем же file_id",
            price_stars=25,
            content_type="video",
            file_id="BAACAgIAAxkDAAIBYGI4",  # Тот же file_id как у первого урока
            is_active=True
        )
        
        # Мокируем первый запрос - получение дублирующихся file_id
        mock_result_1 = AsyncMock()
        mock_result_1.fetchall.return_value = [("BAACAgIAAxkDAAIBYGI4", 2)]
        
        # Мокируем второй запрос - получение уроков с дублирующимся file_id
        mock_result_2 = AsyncMock()
        mock_scalars_2 = AsyncMock()
        mock_scalars_2.all.return_value = [sample_lessons[0], duplicate_lesson]
        mock_result_2.scalars.return_value = mock_scalars_2
        
        with patch.object(db_session, 'execute', side_effect=[mock_result_1, mock_result_2]):
            duplicate_files = await media_service.get_duplicate_media_files()
            
            assert len(duplicate_files) > 0
            # Проверяем структуру ответа
            file_id = list(duplicate_files.keys())[0]
            assert file_id == "BAACAgIAAxkDAAIBYGI4"
            assert len(duplicate_files[file_id]) == 2

    async def test_cleanup_unused_media(self, media_service, db_session):
        """Тест очистки неиспользуемых медиа"""
        # Мокируем удаление неактивных уроков
        mock_result = AsyncMock()
        mock_result.rowcount = 5  # Удалено 5 записей
        
        db_session.commit = AsyncMock()
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            deleted_count = await media_service.cleanup_unused_media()
            
            assert deleted_count == 5
            db_session.commit.assert_called_once()

    async def test_optimize_media_storage(self, media_service, db_session, sample_lessons):
        """Тест оптимизации медиа хранилища"""
        # Мокируем получение дубликатов
        duplicates = {
            "BAACAgIAAxkDAAIBYGI4": [sample_lessons[0], sample_lessons[1]]
        }
        
        with patch.object(media_service, 'get_duplicate_media_files', return_value=duplicates):
            with patch.object(media_service, 'cleanup_unused_media', return_value=3):
                result = await media_service.optimize_media_storage()
                
                assert result['duplicates_found'] > 0
                assert result['unused_cleaned'] == 3

    async def test_generate_media_report(self, media_service, db_session, sample_lessons):
        """Тест генерации отчета по медиа"""
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all.return_value = sample_lessons
        mock_result.scalars.return_value = mock_scalars
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            report = await media_service.generate_media_report()
            
            assert 'total_lessons' in report
            assert 'media_distribution' in report
            assert 'storage_info' in report
            assert report['total_lessons'] == 3

    async def test_validate_telegram_file_id(self, media_service):
        """Тест валидации Telegram file_id"""
        # Валидные file_id
        valid_ids = [
            "BAACAgIAAxkDAAIBYGI4",
            "AgACAgIAAxkBAAIBYWI4", 
            "BQACAgIAAxkCAAIBYmI4"
        ]
        
        for file_id in valid_ids:
            assert media_service.validate_telegram_file_id(file_id) is True
        
        # Невалидные file_id
        invalid_ids = [
            "",
            "short",
            "invalid@id",
            None
        ]
        
        for file_id in invalid_ids:
            assert media_service.validate_telegram_file_id(file_id) is False

    async def test_error_handling_in_update_media(self, media_service, db_session):
        """Тест обработки ошибок при обновлении медиа"""
        db_session.execute = AsyncMock(side_effect=Exception("Database error"))
        db_session.rollback = AsyncMock()
        
        result = await media_service.update_lesson_media(
            lesson_id=1,
            content_type="video",
            file_id="FILE_ID"
        )
        
        assert result is None
        db_session.rollback.assert_called_once()

    async def test_error_handling_in_delete_media(self, media_service, db_session):
        """Тест обработки ошибок при удалении медиа"""
        db_session.execute = AsyncMock(side_effect=Exception("Database error"))
        db_session.rollback = AsyncMock()
        
        success = await media_service.delete_lesson_media(lesson_id=1)
        
        assert success is False
        db_session.rollback.assert_called_once()

    async def test_get_media_categories(self, media_service, db_session):
        """Тест получения списка категорий медиа"""
        categories_result = [("video_lessons",), ("photo_lessons",), ("doc_lessons",)]
        
        mock_result = AsyncMock()
        mock_result.fetchall.return_value = categories_result
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            categories = await media_service.get_media_categories()
            
            assert len(categories) == 3
            assert "video_lessons" in categories
            assert "photo_lessons" in categories
            assert "doc_lessons" in categories

    async def test_backup_media_metadata(self, media_service, db_session, sample_lessons):
        """Тест создания бэкапа метаданных медиа"""
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all.return_value = sample_lessons
        mock_result.scalars.return_value = mock_scalars
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            backup_data = await media_service.backup_media_metadata()
            
            assert len(backup_data) == 3
            assert backup_data[0]['title'] == "Видео урок"
            assert backup_data[0]['content_type'] == "video"
            assert 'created_at' in backup_data[0]

    async def test_restore_media_metadata(self, media_service, db_session):
        """Тест восстановления метаданных медиа из бэкапа"""
        backup_data = [
            {
                'id': 1,
                'title': 'Восстановленный урок',
                'content_type': 'video',
                'file_id': 'BACKUP_FILE_ID'
            }
        ]
        
        db_session.merge = AsyncMock()
        db_session.commit = AsyncMock()
        
        success = await media_service.restore_media_metadata(backup_data)
        
        assert success is True
        db_session.merge.assert_called()
        db_session.commit.assert_called_once()

    async def test_get_media_usage_analytics(self, media_service, db_session, sample_lessons):
        """Тест получения аналитики использования медиа"""
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all.return_value = sample_lessons
        mock_result.scalars.return_value = mock_scalars
        
        with patch.object(db_session, 'execute', return_value=mock_result):
            analytics = await media_service.get_media_usage_analytics()
            
            assert 'most_viewed' in analytics
            assert 'least_viewed' in analytics
            assert 'average_views' in analytics
            assert 'total_views' in analytics