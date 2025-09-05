"""
Сервис для работы с категориями уроков
"""
import logging
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Category, Lesson

logger = logging.getLogger(__name__)


class CategoryService:
    """Сервис для управления категориями"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_category(
        self,
        name: str,
        description: Optional[str] = None,
        is_active: bool = True
    ) -> Category:
        """Создать новую категорию"""
        try:
            category = Category(
                name=name.strip(),
                description=description.strip() if description else None,
                is_active=is_active,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            self.session.add(category)
            await self.session.commit()
            await self.session.refresh(category)
            
            logger.info(f"Создана категория: {category.name} (ID: {category.id})")
            return category
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка при создании категории {name}: {e}")
            raise
    
    async def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Получить категорию по ID"""
        try:
            stmt = select(Category).where(Category.id == category_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка при получении категории {category_id}: {e}")
            return None
    
    async def get_category_by_name(self, name: str) -> Optional[Category]:
        """Получить категорию по имени"""
        try:
            stmt = select(Category).where(Category.name == name.strip())
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка при получении категории {name}: {e}")
            return None
    
    async def get_all_categories(
        self, 
        only_active: bool = True,
        include_lesson_count: bool = False
    ) -> List[Category]:
        """Получить все категории"""
        try:
            stmt = select(Category)
            
            if only_active:
                stmt = stmt.where(Category.is_active == True)
            
            if include_lesson_count:
                stmt = stmt.options(selectinload(Category.lessons))
            
            stmt = stmt.order_by(Category.name)
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Ошибка при получении списка категорий: {e}")
            return []
    
    async def update_category(
        self,
        category_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Category]:
        """Обновить категорию"""
        try:
            category = await self.get_category_by_id(category_id)
            if not category:
                return None
            
            update_data = {"updated_at": datetime.now(timezone.utc)}
            
            if name is not None:
                update_data["name"] = name.strip()
            if description is not None:
                update_data["description"] = description.strip() if description else None
            if is_active is not None:
                update_data["is_active"] = is_active
            
            stmt = update(Category).where(Category.id == category_id).values(**update_data)
            await self.session.execute(stmt)
            await self.session.commit()
            
            # Получаем обновленную категорию
            updated_category = await self.get_category_by_id(category_id)
            
            logger.info(f"Обновлена категория: {updated_category.name} (ID: {category_id})")
            return updated_category
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка при обновлении категории {category_id}: {e}")
            raise
    
    async def delete_category(self, category_id: int, force: bool = False) -> bool:
        """
        Удалить категорию
        
        Args:
            category_id: ID категории
            force: Если True, удаляет категорию даже если есть связанные уроки
                  Если False, только деактивирует категорию
        """
        try:
            category = await self.get_category_by_id(category_id)
            if not category:
                return False
            
            # Проверяем, есть ли уроки в этой категории
            stmt = select(Lesson).where(Lesson.category_id == category_id)
            result = await self.session.execute(stmt)
            lessons = list(result.scalars().all())
            
            if lessons and not force:
                # Если есть уроки, просто деактивируем категорию
                await self.update_category(category_id, is_active=False)
                logger.info(f"Деактивирована категория: {category.name} (ID: {category_id})")
                return True
            
            if lessons and force:
                # Если force=True, сначала обнуляем category_id у всех уроков
                stmt = update(Lesson).where(Lesson.category_id == category_id).values(category_id=None)
                await self.session.execute(stmt)
            
            # Удаляем категорию
            stmt = delete(Category).where(Category.id == category_id)
            await self.session.execute(stmt)
            await self.session.commit()
            
            logger.info(f"Удалена категория: {category.name} (ID: {category_id})")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка при удалении категории {category_id}: {e}")
            raise
    
    async def get_categories_with_lesson_count(self) -> List[dict]:
        """Получить категории с количеством уроков"""
        try:
            categories = await self.get_all_categories(only_active=True)
            
            result = []
            for category in categories:
                # Подсчитываем активные уроки в категории
                # Учитываем как category_id (новое поле), так и category (старое поле)
                stmt = select(func.count(Lesson.id)).where(
                    and_(
                        Lesson.is_active == True,
                        or_(
                            Lesson.category_id == category.id,  # Новые уроки
                            Lesson.category == category.name    # Старые уроки
                        )
                    )
                )
                
                count_result = await self.session.execute(stmt)
                lesson_count = count_result.scalar() or 0
                
                result.append({
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "is_active": category.is_active,
                    "lesson_count": lesson_count,
                    "created_at": category.created_at
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при получении категорий с количеством уроков: {e}")
            return []
    
    async def find_or_create_category(
        self, 
        name: str, 
        description: Optional[str] = None
    ) -> tuple[Category, bool]:
        """
        Найти существующую категорию или создать новую
        
        Returns:
            tuple: (category, created) где created указывает, была ли создана новая категория
        """
        try:
            # Сначала ищем существующую
            existing_category = await self.get_category_by_name(name)
            
            if existing_category:
                # Если категория найдена, но неактивна - активируем её
                if not existing_category.is_active:
                    await self.update_category(existing_category.id, is_active=True)
                    existing_category.is_active = True
                    
                logger.info(f"Найдена существующая категория: {name}")
                return existing_category, False
            
            # Если не найдена - создаем новую
            new_category = await self.create_category(name, description)
            logger.info(f"Создана новая категория: {name}")
            return new_category, True
            
        except Exception as e:
            logger.error(f"Ошибка при поиске/создании категории {name}: {e}")
            raise
    
    async def get_category_stats(self, category_id: int) -> Optional[dict]:
        """Получить статистику по категории"""
        try:
            category = await self.get_category_by_id(category_id)
            if not category:
                return None
            
            # Получаем уроки категории (как по category_id, так и по category строке)
            stmt = select(Lesson).where(
                or_(
                    Lesson.category_id == category_id,  # Новые уроки
                    Lesson.category == category.name    # Старые уроки
                )
            )
            result = await self.session.execute(stmt)
            lessons = list(result.scalars().all())
            
            total_lessons = len(lessons)
            active_lessons = len([l for l in lessons if l.is_active])
            free_lessons = len([l for l in lessons if l.is_free])
            paid_lessons = total_lessons - free_lessons
            total_views = sum(l.views_count for l in lessons)
            
            return {
                "category_id": category_id,
                "category_name": category.name,
                "total_lessons": total_lessons,
                "active_lessons": active_lessons,
                "free_lessons": free_lessons,
                "paid_lessons": paid_lessons,
                "total_views": total_views,
                "created_at": category.created_at
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики категории {category_id}: {e}")
            return None