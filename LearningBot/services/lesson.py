"""
Сервис для работы с уроками
"""
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, desc, func
from database.models import Lesson, Purchase, User
import logging

logger = logging.getLogger(__name__)


class LessonService:
    """Сервис для управления уроками"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_lesson_by_id(self, lesson_id: int, include_inactive: bool = False) -> Optional[Lesson]:
        """Получить урок по ID
        
        Args:
            lesson_id: ID урока
            include_inactive: Включать неактивные уроки (для админа)
        """
        try:
            if include_inactive:
                # Для админа - любой урок
                result = await self.session.execute(
                    select(Lesson).where(Lesson.id == lesson_id)
                )
            else:
                # Для пользователей - только активные
                result = await self.session.execute(
                    select(Lesson).where(
                        and_(
                            Lesson.id == lesson_id,
                            Lesson.is_active == True
                        )
                    )
                )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка при получении урока {lesson_id}: {e}")
            return None
    
    async def get_free_lessons(self) -> List[Lesson]:
        """Получить все бесплатные уроки"""
        try:
            result = await self.session.execute(
                select(Lesson).where(
                    and_(
                        Lesson.is_free == True,
                        Lesson.is_active == True
                    )
                ).order_by(Lesson.created_at.desc())
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Ошибка при получении бесплатных уроков: {e}")
            return []
    
    async def get_lessons_paginated(
        self, 
        page: int = 0, 
        per_page: int = 10, 
        category: Optional[str] = None,
        search_query: Optional[str] = None,
        sort_by: str = "created_at",
        include_inactive: bool = False
    ) -> Tuple[List[Lesson], int]:
        """
        Получить уроки с пагинацией
        Возвращает tuple: (список уроков, общее количество)
        
        Args:
            page: Номер страницы (начиная с 0)
            per_page: Количество уроков на странице
            category: Фильтр по категории
            search_query: Поисковый запрос
            sort_by: Поле для сортировки
            include_inactive: Включать неактивные уроки (для админа)
        """
        try:
            # Базовый запрос
            if include_inactive:
                # Для администратора показываем все уроки
                query = select(Lesson)
                count_query = select(func.count(Lesson.id))
            else:
                # Для пользователей только активные
                query = select(Lesson).where(Lesson.is_active == True)
                count_query = select(func.count(Lesson.id)).where(Lesson.is_active == True)
            
            # Фильтр по категории
            if category and category != "all":
                query = query.where(Lesson.category == category)
                count_query = count_query.where(Lesson.category == category)
            
            # Поиск по тексту
            if search_query:
                search_filter = or_(
                    Lesson.title.ilike(f"%{search_query}%"),
                    Lesson.description.ilike(f"%{search_query}%")
                )
                query = query.where(search_filter)
                count_query = count_query.where(search_filter)
            
            # Сортировка
            if sort_by == "price":
                query = query.order_by(Lesson.price_stars.asc())
            elif sort_by == "popular":
                query = query.order_by(Lesson.views_count.desc())
            elif sort_by == "new":
                query = query.order_by(Lesson.created_at.desc())
            else:
                query = query.order_by(Lesson.created_at.desc())
            
            # Пагинация
            offset = page * per_page
            query = query.offset(offset).limit(per_page)
            
            # Выполнение запросов
            lessons_result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)
            
            lessons = list(lessons_result.scalars().all())
            total_count = count_result.scalar()
            
            return lessons, total_count
            
        except Exception as e:
            logger.error(f"Ошибка при получении уроков с пагинацией: {e}")
            return [], 0
    
    async def get_lessons_by_category(
        self,
        category_id: int,
        page: int = 0,
        per_page: int = 10,
        include_inactive: bool = False
    ) -> Tuple[List[Lesson], int]:
        """
        Получить уроки конкретной категории
        
        Args:
            category_id: ID категории
            page: Номер страницы
            per_page: Количество уроков на странице
            include_inactive: Включать неактивные уроки
        """
        try:
            # Базовые условия
            conditions = [Lesson.category_id == category_id]
            
            if not include_inactive:
                conditions.append(Lesson.is_active == True)
            
            # Запросы
            query = select(Lesson).where(and_(*conditions)).order_by(Lesson.created_at.desc())
            count_query = select(func.count(Lesson.id)).where(and_(*conditions))
            
            # Пагинация
            offset = page * per_page
            query = query.offset(offset).limit(per_page)
            
            # Выполнение
            lessons_result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)
            
            lessons = list(lessons_result.scalars().all())
            total_count = count_result.scalar()
            
            return lessons, total_count
            
        except Exception as e:
            logger.error(f"Ошибка при получении уроков категории {category_id}: {e}")
            return [], 0
    
    async def check_user_has_lesson(self, user_id: int, lesson_id: int) -> bool:
        """Проверить, есть ли у пользователя доступ к уроку"""
        try:
            # Проверяем бесплатный урок
            lesson = await self.get_lesson_by_id(lesson_id)
            if lesson and lesson.is_free:
                return True
            
            # Проверяем покупки
            result = await self.session.execute(
                select(Purchase).where(
                    and_(
                        Purchase.user_id == user_id,
                        Purchase.lesson_id == lesson_id,
                        Purchase.status == "completed"
                    )
                )
            )
            purchase = result.scalar_one_or_none()
            return purchase is not None
            
        except Exception as e:
            logger.error(f"Ошибка при проверке доступа пользователя {user_id} к уроку {lesson_id}: {e}")
            return False
    
    async def get_user_purchases(self, user_id: int, page: int = 0, per_page: int = 10) -> Tuple[List[dict], int]:
        """Получить покупки пользователя с информацией об уроках"""
        try:
            # Запрос покупок с join к урокам
            query = select(Purchase, Lesson).join(
                Lesson, Purchase.lesson_id == Lesson.id
            ).where(
                and_(
                    Purchase.user_id == user_id,
                    Purchase.status == "completed"
                )
            ).order_by(Purchase.purchase_date.desc())
            
            # Подсчет общего количества
            count_query = select(func.count(Purchase.id)).where(
                and_(
                    Purchase.user_id == user_id,
                    Purchase.status == "completed"
                )
            )
            
            # Пагинация
            offset = page * per_page
            query = query.offset(offset).limit(per_page)
            
            # Выполнение запросов
            purchases_result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)
            
            # Формирование результата
            purchases_data = []
            for purchase, lesson in purchases_result.all():
                purchases_data.append({
                    'purchase': purchase,
                    'lesson': lesson,
                    'purchase_date': purchase.purchase_date,
                    'amount_stars': purchase.amount_stars
                })
            
            total_count = count_result.scalar()
            
            return purchases_data, total_count
            
        except Exception as e:
            logger.error(f"Ошибка при получении покупок пользователя {user_id}: {e}")
            return [], 0
    
    async def increment_lesson_views(self, lesson_id: int) -> bool:
        """Увеличить счетчик просмотров урока"""
        try:
            await self.session.execute(
                update(Lesson)
                .where(Lesson.id == lesson_id)
                .values(views_count=Lesson.views_count + 1)
            )
            await self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка при увеличении счетчика просмотров урока {lesson_id}: {e}")
            return False
    
    async def create_lesson(self, lesson_data: dict) -> Optional[Lesson]:
        """Создать новый урок
        
        Args:
            lesson_data: Словарь с данными урока
            
        Returns:
            Optional[Lesson]: Созданный урок или None при ошибке
        """
        try:
            # Проверяем обязательные поля
            required_fields = ['title', 'description', 'price_stars', 'category', 'content_type']
            for field in required_fields:
                if field not in lesson_data:
                    logger.error(f"Отсутствует обязательное поле: {field}")
                    return None
            
            # Создаем объект урока
            new_lesson = Lesson(
                title=lesson_data['title'],
                description=lesson_data['description'],
                price_stars=lesson_data['price_stars'],
                category=lesson_data['category'],
                category_id=lesson_data.get('category_id'),  # Новое поле
                content_type=lesson_data['content_type'],
                file_id=lesson_data.get('file_id'),
                duration=lesson_data.get('duration'),
                is_free=lesson_data['price_stars'] == 0,
                is_active=lesson_data.get('is_active', True),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                views_count=0
            )
            
            self.session.add(new_lesson)
            await self.session.commit()
            await self.session.refresh(new_lesson)
            
            logger.info(f"Создан новый урок {new_lesson.id}: {new_lesson.title}")
            return new_lesson
            
        except Exception as e:
            logger.error(f"Ошибка при создании урока: {e}")
            await self.session.rollback()
            return None
    
    async def search_lessons(
        self, 
        query: str, 
        page: int = 0, 
        per_page: int = 10
    ) -> Tuple[List[Lesson], int]:
        """Поиск уроков по запросу"""
        return await self.get_lessons_paginated(
            page=page,
            per_page=per_page,
            search_query=query
        )
    

    async def get_popular_lessons(self, limit: int = 10) -> List[Lesson]:
        """Получить популярные уроки"""
        try:
            result = await self.session.execute(
                select(Lesson).where(
                    Lesson.is_active == True
                ).order_by(
                    Lesson.views_count.desc()
                ).limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Ошибка при получении популярных уроков: {e}")
            return []
    
    async def get_lesson_categories(self) -> List[str]:
        """Получить все категории уроков"""
        try:
            result = await self.session.execute(
                select(Lesson.category)
                .where(
                    and_(
                        Lesson.category.isnot(None),
                        Lesson.is_active == True
                    )
                )
                .distinct()
                .order_by(Lesson.category)
            )
            return [cat for cat in result.scalars().all() if cat]
        except Exception as e:
            logger.error(f"Ошибка при получении категорий: {e}")
            return []
    
    async def update_lesson_title(self, lesson_id: int, new_title: str) -> bool:
        """Обновить название урока"""
        try:
            await self.session.execute(
                update(Lesson)
                .where(Lesson.id == lesson_id)
                .values(title=new_title, updated_at=datetime.now(timezone.utc))
            )
            await self.session.commit()
            logger.info(f"Название урока {lesson_id} обновлено: {new_title}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении названия урока {lesson_id}: {e}")
            await self.session.rollback()
            return False
    
    async def update_lesson_description(self, lesson_id: int, new_description: str) -> bool:
        """Обновить описание урока"""
        try:
            await self.session.execute(
                update(Lesson)
                .where(Lesson.id == lesson_id)
                .values(description=new_description, updated_at=datetime.now(timezone.utc))
            )
            await self.session.commit()
            logger.info(f"Описание урока {lesson_id} обновлено")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении описания урока {lesson_id}: {e}")
            await self.session.rollback()
            return False
    
    async def update_lesson_price(self, lesson_id: int, new_price: int) -> bool:
        """Обновить цену урока"""
        try:
            is_free = new_price == 0
            await self.session.execute(
                update(Lesson)
                .where(Lesson.id == lesson_id)
                .values(price_stars=new_price, is_free=is_free, updated_at=datetime.now(timezone.utc))
            )
            await self.session.commit()
            logger.info(f"Цена урока {lesson_id} обновлена: {new_price}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении цены урока {lesson_id}: {e}")
            await self.session.rollback()
            return False
    
    async def update_lesson_category(self, lesson_id: int, new_category: str) -> bool:
        """Обновить категорию урока"""
        try:
            await self.session.execute(
                update(Lesson)
                .where(Lesson.id == lesson_id)
                .values(category=new_category, updated_at=datetime.now(timezone.utc))
            )
            await self.session.commit()
            logger.info(f"Категория урока {lesson_id} обновлена: {new_category}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении категории урока {lesson_id}: {e}")
            await self.session.rollback()
            return False
    
    async def update_lesson_status(self, lesson_id: int, is_active: bool) -> bool:
        """Обновить статус активности урока"""
        try:
            await self.session.execute(
                update(Lesson)
                .where(Lesson.id == lesson_id)
                .values(is_active=is_active, updated_at=datetime.now(timezone.utc))
            )
            await self.session.commit()
            status = "активирован" if is_active else "деактивирован"
            logger.info(f"Урок {lesson_id} {status}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при изменении статуса урока {lesson_id}: {e}")
            await self.session.rollback()
            return False
    
    async def update_lesson_media(self, lesson_id: int, content_type: str, file_id: str, duration: Optional[int] = None) -> bool:
        """Обновить медиа-контент урока"""
        try:
            values = {
                'content_type': content_type,
                'file_id': file_id,
                'updated_at': datetime.now(timezone.utc)
            }
            
            if duration is not None:
                values['duration'] = duration
            
            await self.session.execute(
                update(Lesson)
                .where(Lesson.id == lesson_id)
                .values(**values)
            )
            await self.session.commit()
            logger.info(f"Медиа урока {lesson_id} обновлено: {content_type}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении медиа урока {lesson_id}: {e}")
            await self.session.rollback()
            return False
    
    async def can_delete_lesson(self, lesson_id: int) -> Tuple[bool, str]:
        """Проверить, можно ли удалить урок
        
        Returns:
            Tuple[bool, str]: (можно_удалить, причина_если_нельзя)
        """
        try:
            # Проверяем существование урока
            lesson = await self.get_lesson_by_id(lesson_id, include_inactive=True)
            if not lesson:
                return False, "Урок не найден"
            
            # Проверяем наличие покупок
            purchase_result = await self.session.execute(
                select(func.count(Purchase.id))
                .where(
                    and_(
                        Purchase.lesson_id == lesson_id,
                        Purchase.status == "completed"
                    )
                )
            )
            purchase_count = purchase_result.scalar()
            
            if purchase_count > 0:
                return False, f"У урока есть покупки ({purchase_count} шт.). Рекомендуется деактивировать вместо удаления."
            
            return True, "Урок можно безопасно удалить"
            
        except Exception as e:
            logger.error(f"Ошибка при проверке возможности удаления урока {lesson_id}: {e}")
            return False, f"Ошибка при проверке: {str(e)}"
    
    async def get_lesson_dependencies(self, lesson_id: int) -> dict:
        """Получить информацию о зависимостях урока
        
        Returns:
            dict: Словарь с информацией о покупках, просмотрах и других зависимостях
        """
        try:
            # Получаем информацию о покупках
            purchase_result = await self.session.execute(
                select(
                    func.count(Purchase.id).label('total_purchases'),
                    func.sum(Purchase.amount_stars).label('total_revenue')
                )
                .where(
                    and_(
                        Purchase.lesson_id == lesson_id,
                        Purchase.status == "completed"
                    )
                )
            )
            purchase_data = purchase_result.first()
            
            # Получаем информацию об уроке
            lesson = await self.get_lesson_by_id(lesson_id, include_inactive=True)
            
            if not lesson:
                return {}
            
            return {
                'lesson_id': lesson_id,
                'title': lesson.title,
                'total_purchases': purchase_data.total_purchases or 0,
                'total_revenue': purchase_data.total_revenue or 0,
                'views_count': lesson.views_count or 0,
                'is_active': lesson.is_active,
                'is_free': lesson.is_free,
                'created_at': lesson.created_at,
                'has_media': bool(lesson.file_id)
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении зависимостей урока {lesson_id}: {e}")
            return {}
    
    async def soft_delete_lesson(self, lesson_id: int) -> bool:
        """Мягкое удаление урока (деактивация)
        
        Args:
            lesson_id: ID урока для мягкого удаления
            
        Returns:
            bool: Успешность операции
        """
        try:
            # Проверяем существование урока
            lesson = await self.get_lesson_by_id(lesson_id, include_inactive=True)
            if not lesson:
                logger.warning(f"Попытка мягкого удаления несуществующего урока {lesson_id}")
                return False
            
            # Деактивируем урок
            success = await self.update_lesson_status(lesson_id, False)
            
            if success:
                logger.info(f"Урок {lesson_id} мягко удален (деактивирован): {lesson.title}")
                return True
            else:
                logger.error(f"Ошибка при мягком удалении урока {lesson_id}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при мягком удалении урока {lesson_id}: {e}")
            await self.session.rollback()
            return False
    
    async def delete_lesson(self, lesson_id: int, force: bool = False) -> bool:
        """Жесткое удаление урока из базы данных
        
        Args:
            lesson_id: ID урока для удаления
            force: Принудительное удаление даже при наличии покупок
            
        Returns:
            bool: Успешность операции
        """
        try:
            # Проверяем возможность удаления, если не принудительное
            if not force:
                can_delete, reason = await self.can_delete_lesson(lesson_id)
                if not can_delete:
                    logger.warning(f"Отказ в удалении урока {lesson_id}: {reason}")
                    return False
            
            # Получаем урок для логирования
            lesson = await self.get_lesson_by_id(lesson_id, include_inactive=True)
            if not lesson:
                logger.warning(f"Попытка удаления несуществующего урока {lesson_id}")
                return False
            
            lesson_title = lesson.title
            
            # Удаляем связанные покупки (если force=True)
            if force:
                await self.session.execute(
                    update(Purchase)
                    .where(Purchase.lesson_id == lesson_id)
                    .values(status="cancelled")
                )
                logger.info(f"Отменены покупки для урока {lesson_id} при принудительном удалении")
            
            # Удаляем сам урок
            await self.session.execute(
                delete(Lesson).where(Lesson.id == lesson_id)
            )
            
            await self.session.commit()
            logger.info(f"Урок {lesson_id} жестко удален: {lesson_title}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при жестком удалении урока {lesson_id}: {e}")
            await self.session.rollback()
            return False
    
    async def bulk_update_status(self, lesson_ids: List[int], is_active: bool) -> dict:
        """Массовое изменение статуса уроков
        
        Args:
            lesson_ids: Список ID уроков
            is_active: Новый статус активности
            
        Returns:
            dict: Результат операции с количеством обновленных уроков
        """
        try:
            result = await self.session.execute(
                update(Lesson)
                .where(Lesson.id.in_(lesson_ids))
                .values(
                    is_active=is_active,
                    updated_at=datetime.now(timezone.utc)
                )
            )
            
            updated_count = result.rowcount
            await self.session.commit()
            
            status_text = "активированы" if is_active else "деактивированы"
            logger.info(f"Массово {status_text} {updated_count} уроков")
            
            return {
                'success': True,
                'updated_count': updated_count,
                'total_requested': len(lesson_ids),
                'status': status_text
            }
            
        except Exception as e:
            logger.error(f"Ошибка при массовом обновлении статуса уроков: {e}")
            await self.session.rollback()
            return {
                'success': False,
                'updated_count': 0,
                'total_requested': len(lesson_ids),
                'error': str(e)
            }