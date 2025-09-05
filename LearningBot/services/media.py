"""
Сервис управления медиа-контентом

⚠️ ЗАКОММЕНТИРОВАН - НЕ ИСПОЛЬЗУЕТСЯ В УПРОЩЕННОЙ ВЕРСИИ БОТА
Данный сервис содержит сложные функции управления медиа:
- Валидация размеров файлов
- Поиск по медиа-контенту
- Статистика медиа
- Отдельное управление медиа файлами

Для простого бота медиа управляется напрямую через LessonService
"""
import logging
import re
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Lesson

logger = logging.getLogger(__name__)


class MediaService:
    """Сервис для управления медиа-контентом уроков"""

    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Ограничения размера файлов (в байтах)
        self.size_limits = {
            'video': 50 * 1024 * 1024,  # 50MB
            'photo': 20 * 1024 * 1024,  # 20MB
            'document': 20 * 1024 * 1024,  # 20MB
            'audio': 50 * 1024 * 1024,  # 50MB
        }
        
        # Поддерживаемые типы медиа
        self.supported_types = ['video', 'photo', 'document', 'audio']

    async def get_media_by_type(self, content_type: str) -> List[Lesson]:
        """Получить все медиа файлы определенного типа"""
        try:
            query = select(Lesson).where(
                Lesson.content_type == content_type,
                Lesson.file_id.isnot(None)
            ).order_by(Lesson.created_at.desc())
            
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка при получении медиа по типу {content_type}: {e}")
            return []

    async def get_media_by_category(self, category: str) -> List[Lesson]:
        """Получить медиа файлы по категории"""
        try:
            query = select(Lesson).where(
                Lesson.category == category,
                Lesson.file_id.isnot(None)
            ).order_by(Lesson.created_at.desc())
            
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка при получении медиа по категории {category}: {e}")
            return []

    def validate_media_file(self, content_type: str, file_size: int) -> bool:
        """Валидация медиа файла"""
        if content_type not in self.supported_types:
            return False
        
        if file_size > self.size_limits.get(content_type, 0):
            return False
        
        return True

    def get_media_size_limits(self) -> Dict[str, int]:
        """Получить ограничения размера для разных типов медиа"""
        return self.size_limits.copy()

    def get_supported_media_types(self) -> List[str]:
        """Получить список поддерживаемых типов медиа"""
        return self.supported_types.copy()

    async def update_lesson_media(
        self,
        lesson_id: int,
        content_type: str,
        file_id: str,
        duration: Optional[int] = None
    ) -> Optional[Lesson]:
        """Обновить медиа контент урока"""
        try:
            # Получаем урок
            query = select(Lesson).where(Lesson.id == lesson_id)
            result = await self.session.execute(query)
            lesson = result.scalar_one_or_none()
            
            if not lesson:
                logger.error(f"Урок с ID {lesson_id} не найден")
                return None
            
            # Обновляем медиа данные
            lesson.content_type = content_type
            lesson.file_id = file_id
            lesson.duration = duration
            lesson.updated_at = datetime.now(timezone.utc)
            
            await self.session.commit()
            logger.info(f"Медиа урока {lesson_id} успешно обновлено")
            return lesson
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении медиа урока {lesson_id}: {e}")
            await self.session.rollback()
            return None

    async def delete_lesson_media(self, lesson_id: int) -> bool:
        """Удалить медиа контент урока"""
        try:
            # Получаем урок
            query = select(Lesson).where(Lesson.id == lesson_id)
            result = await self.session.execute(query)
            lesson = result.scalar_one_or_none()
            
            if not lesson:
                logger.error(f"Урок с ID {lesson_id} не найден")
                return False
            
            # Удаляем медиа данные
            lesson.file_id = None
            lesson.content_type = "text"  # Устанавливаем дефолтный тип
            lesson.duration = None
            lesson.updated_at = datetime.now(timezone.utc)
            
            await self.session.commit()
            logger.info(f"Медиа урока {lesson_id} успешно удалено")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при удалении медиа урока {lesson_id}: {e}")
            await self.session.rollback()
            return False

    async def get_media_statistics(self) -> Dict[str, Any]:
        """Получить статистику по медиа контенту"""
        try:
            # Получаем все уроки с медиа
            query = select(Lesson).where(Lesson.file_id.isnot(None))
            result = await self.session.execute(query)
            lessons = result.scalars().all()
            
            # Считаем статистику
            stats = {
                'total_media': len(lessons),
                'video_count': 0,
                'photo_count': 0,
                'document_count': 0,
                'audio_count': 0,
                'categories': {},
                'total_duration': 0
            }
            
            for lesson in lessons:
                # Подсчет по типам
                if lesson.content_type in stats:
                    stats[f'{lesson.content_type}_count'] += 1
                
                # Подсчет по категориям
                if lesson.category:
                    stats['categories'][lesson.category] = stats['categories'].get(lesson.category, 0) + 1
                
                # Общая длительность
                if lesson.duration:
                    stats['total_duration'] += lesson.duration
            
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики медиа: {e}")
            return {}

    async def search_media(self, search_term: str) -> List[Lesson]:
        """Поиск медиа контента"""
        try:
            search_pattern = f"%{search_term.lower()}%"
            
            query = select(Lesson).where(
                Lesson.file_id.isnot(None),
                (func.lower(Lesson.title).like(search_pattern)) |
                (func.lower(Lesson.description).like(search_pattern)) |
                (func.lower(Lesson.category).like(search_pattern))
            ).order_by(Lesson.created_at.desc())
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Ошибка при поиске медиа: {e}")
            return []

    async def get_media_by_lesson_id(self, lesson_id: int) -> Optional[Lesson]:
        """Получить медиа по ID урока"""
        try:
            query = select(Lesson).where(
                Lesson.id == lesson_id,
                Lesson.file_id.isnot(None)
            )
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка при получении медиа урока {lesson_id}: {e}")
            return None

    async def check_media_file_exists(self, file_id: str) -> bool:
        """Проверить существование медиа файла"""
        try:
            query = select(func.count(Lesson.id)).where(Lesson.file_id == file_id)
            result = await self.session.execute(query)
            count = result.scalar()
            return count > 0
        except Exception as e:
            logger.error(f"Ошибка при проверке существования файла {file_id}: {e}")
            return False

    async def get_duplicate_media_files(self) -> Dict[str, List[Lesson]]:
        """Найти дублирующиеся медиа файлы"""
        try:
            # Получаем file_id, которые встречаются более одного раза
            query = select(Lesson.file_id, func.count(Lesson.id)).where(
                Lesson.file_id.isnot(None)
            ).group_by(Lesson.file_id).having(func.count(Lesson.id) > 1)
            
            result = await self.session.execute(query)
            duplicate_file_ids = [row[0] for row in result.fetchall()]
            
            # Получаем все уроки с дублирующимися file_id
            duplicates = {}
            for file_id in duplicate_file_ids:
                query = select(Lesson).where(Lesson.file_id == file_id)
                result = await self.session.execute(query)
                lessons = result.scalars().all()
                duplicates[file_id] = lessons
            
            return duplicates
            
        except Exception as e:
            logger.error(f"Ошибка при поиске дубликатов: {e}")
            return {}

    async def cleanup_unused_media(self) -> int:
        """Очистка неиспользуемых медиа файлов"""
        try:
            # Удаляем медиа данные у неактивных уроков
            query = update(Lesson).where(
                Lesson.is_active == False,
                Lesson.file_id.isnot(None)
            ).values(
                file_id=None,
                content_type="text",
                duration=None
            )
            
            result = await self.session.execute(query)
            deleted_count = result.rowcount
            
            await self.session.commit()
            logger.info(f"Очищено {deleted_count} неиспользуемых медиа файлов")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Ошибка при очистке неиспользуемых медиа: {e}")
            await self.session.rollback()
            return 0

    async def optimize_media_storage(self) -> Dict[str, Any]:
        """Оптимизация медиа хранилища"""
        try:
            # Находим дубликаты
            duplicates = await self.get_duplicate_media_files()
            
            # Очищаем неиспользуемые файлы
            unused_cleaned = await self.cleanup_unused_media()
            
            return {
                'duplicates_found': len(duplicates),
                'unused_cleaned': unused_cleaned,
                'duplicate_files': duplicates
            }
            
        except Exception as e:
            logger.error(f"Ошибка при оптимизации хранилища: {e}")
            return {'duplicates_found': 0, 'unused_cleaned': 0}

    async def generate_media_report(self) -> Dict[str, Any]:
        """Генерация отчета по медиа"""
        try:
            # Получаем все уроки
            query = select(Lesson)
            result = await self.session.execute(query)
            all_lessons = result.scalars().all()
            
            # Базовая статистика
            media_lessons = [l for l in all_lessons if l.file_id]
            
            # Распределение по типам
            media_distribution = {}
            for lesson in media_lessons:
                media_distribution[lesson.content_type] = media_distribution.get(lesson.content_type, 0) + 1
            
            # Информация о хранилище
            total_duration = sum(l.duration for l in media_lessons if l.duration)
            
            return {
                'total_lessons': len(all_lessons),
                'lessons_with_media': len(media_lessons),
                'media_distribution': media_distribution,
                'storage_info': {
                    'total_duration_seconds': total_duration,
                    'total_duration_hours': round(total_duration / 3600, 2) if total_duration else 0
                },
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка при генерации отчета: {e}")
            return {}

    def validate_telegram_file_id(self, file_id: str) -> bool:
        """Валидация Telegram file_id"""
        if not file_id or not isinstance(file_id, str):
            return False
        
        # Telegram file_id обычно длинные строки без спецсимволов
        if len(file_id) < 10:
            return False
        
        # Проверяем на недопустимые символы
        pattern = r'^[A-Za-z0-9_-]+$'
        return bool(re.match(pattern, file_id))

    async def get_media_categories(self) -> List[str]:
        """Получить список категорий медиа"""
        try:
            query = select(Lesson.category).where(
                Lesson.file_id.isnot(None),
                Lesson.category.isnot(None)
            ).distinct()
            result = await self.session.execute(query)
            categories = [row[0] for row in result.fetchall()]
            return categories
        except Exception as e:
            logger.error(f"Ошибка при получении категорий медиа: {e}")
            return []

    async def backup_media_metadata(self) -> List[Dict[str, Any]]:
        """Создание бэкапа метаданных медиа"""
        try:
            query = select(Lesson).where(Lesson.file_id.isnot(None))
            result = await self.session.execute(query)
            lessons = result.scalars().all()
            
            backup_data = []
            for lesson in lessons:
                backup_data.append({
                    'id': lesson.id,
                    'title': lesson.title,
                    'description': lesson.description,
                    'content_type': lesson.content_type,
                    'file_id': lesson.file_id,
                    'duration': lesson.duration,
                    'category': lesson.category,
                    'created_at': lesson.created_at.isoformat() if lesson.created_at else None,
                    'updated_at': lesson.updated_at.isoformat() if lesson.updated_at else None
                })
            
            logger.info(f"Создан бэкап метаданных для {len(backup_data)} медиа файлов")
            return backup_data
            
        except Exception as e:
            logger.error(f"Ошибка при создании бэкапа: {e}")
            return []

    async def restore_media_metadata(self, backup_data: List[Dict[str, Any]]) -> bool:
        """Восстановление метаданных медиа из бэкапа"""
        try:
            for data in backup_data:
                # Создаем или обновляем урок
                lesson = Lesson(
                    id=data.get('id'),
                    title=data.get('title', ''),
                    description=data.get('description', ''),
                    content_type=data.get('content_type', 'text'),
                    file_id=data.get('file_id'),
                    duration=data.get('duration'),
                    category=data.get('category'),
                    price_stars=0,  # Дефолтное значение
                    is_active=True,
                    is_free=False
                )
                
                self.session.merge(lesson)
            
            await self.session.commit()
            logger.info(f"Восстановлено {len(backup_data)} медиа файлов из бэкапа")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при восстановлении из бэкапа: {e}")
            await self.session.rollback()
            return False

    async def get_media_usage_analytics(self) -> Dict[str, Any]:
        """Получение аналитики использования медиа"""
        try:
            query = select(Lesson).where(Lesson.file_id.isnot(None))
            result = await self.session.execute(query)
            lessons = result.scalars().all()
            
            if not lessons:
                return {
                    'most_viewed': None,
                    'least_viewed': None,
                    'average_views': 0,
                    'total_views': 0
                }
            
            # Сортируем по просмотрам
            sorted_lessons = sorted(lessons, key=lambda x: x.views_count, reverse=True)
            
            total_views = sum(l.views_count for l in lessons)
            average_views = total_views / len(lessons) if lessons else 0
            
            return {
                'most_viewed': {
                    'id': sorted_lessons[0].id,
                    'title': sorted_lessons[0].title,
                    'views': sorted_lessons[0].views_count
                } if sorted_lessons else None,
                'least_viewed': {
                    'id': sorted_lessons[-1].id,
                    'title': sorted_lessons[-1].title,
                    'views': sorted_lessons[-1].views_count
                } if sorted_lessons else None,
                'average_views': round(average_views, 2),
                'total_views': total_views
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении аналитики использования: {e}")
            return {}