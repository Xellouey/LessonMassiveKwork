"""
Сервис для работы с администраторами
"""
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from database.models import Admin

logger = logging.getLogger(__name__)


class AdminService:
    """Сервис для управления администраторами"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_admin_by_user_id(self, user_id: int) -> Optional[Admin]:
        """Получить администратора по Telegram ID"""
        try:
            result = await self.session.execute(
                select(Admin).where(Admin.user_id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка при получении администратора {user_id}: {e}")
            return None
    
    async def create_admin(
        self, 
        user_id: int, 
        username: Optional[str] = None,
        permissions: str = 'all'
    ) -> Optional[Admin]:
        """Создать нового администратора"""
        try:
            # Проверяем, существует ли уже администратор
            existing_admin = await self.get_admin_by_user_id(user_id)
            if existing_admin:
                logger.warning(f"Администратор с ID {user_id} уже существует")
                return existing_admin
            
            # Создаем нового администратора
            admin = Admin(
                user_id=user_id,
                username=username,
                permissions=permissions,
                created_at=datetime.now(timezone.utc),
                is_active=True
            )
            
            self.session.add(admin)
            await self.session.commit()
            await self.session.refresh(admin)
            
            logger.info(f"Создан новый администратор: {user_id}")
            return admin
            
        except Exception as e:
            logger.error(f"Ошибка при создании администратора {user_id}: {e}")
            await self.session.rollback()
            return None
    
    async def update_admin_permissions(self, user_id: int, permissions: str) -> bool:
        """Обновить права администратора"""
        try:
            await self.session.execute(
                update(Admin)
                .where(Admin.user_id == user_id)
                .values(permissions=permissions)
            )
            await self.session.commit()
            
            logger.info(f"Обновлены права администратора {user_id}: {permissions}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении прав администратора {user_id}: {e}")
            await self.session.rollback()
            return False
    
    async def set_admin_active(self, user_id: int, is_active: bool) -> bool:
        """Активировать/деактивировать администратора"""
        try:
            await self.session.execute(
                update(Admin)
                .where(Admin.user_id == user_id)
                .values(is_active=is_active)
            )
            await self.session.commit()
            
            status = "активирован" if is_active else "деактивирован"
            logger.info(f"Администратор {user_id} {status}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при изменении статуса администратора {user_id}: {e}")
            await self.session.rollback()
            return False
    
    async def delete_admin(self, user_id: int) -> bool:
        """Удалить администратора"""
        try:
            await self.session.execute(
                delete(Admin).where(Admin.user_id == user_id)
            )
            await self.session.commit()
            
            logger.info(f"Администратор {user_id} удален")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при удалении администратора {user_id}: {e}")
            await self.session.rollback()
            return False
    
    async def get_all_admins(self) -> List[Admin]:
        """Получить всех администраторов"""
        try:
            result = await self.session.execute(
                select(Admin).order_by(Admin.created_at.desc())
            )
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Ошибка при получении списка администраторов: {e}")
            return []
    
    async def check_permission(self, user_id: int, permission: str) -> bool:
        """Проверить конкретное разрешение администратора"""
        try:
            admin = await self.get_admin_by_user_id(user_id)
            if not admin or not admin.is_active:
                return False
            
            # Если у администратора права 'all', разрешаем все
            if admin.permissions == 'all':
                return True
            
            # Проверяем конкретное разрешение в JSON
            try:
                permissions_list = json.loads(admin.permissions)
                return permission in permissions_list
            except (json.JSONDecodeError, TypeError):
                # Если permissions не JSON, считаем что это старый формат 'all'
                return admin.permissions == 'all'
            
        except Exception as e:
            logger.error(f"Ошибка при проверке разрешения {permission} для {user_id}: {e}")
            return False
    
    async def update_last_login(self, user_id: int) -> bool:
        """Обновить время последнего входа"""
        try:
            await self.session.execute(
                update(Admin)
                .where(Admin.user_id == user_id)
                .values(last_login=datetime.now(timezone.utc))
            )
            await self.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении времени входа для {user_id}: {e}")
            await self.session.rollback()
            return False