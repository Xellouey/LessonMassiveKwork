"""
Сервис для работы с тикетами поддержки
"""
import logging
import random
import string
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import SupportTicket, SupportResponse, User, Admin

logger = logging.getLogger(__name__)


class SupportService:
    """Сервис для управления тикетами поддержки и ответами"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def _generate_ticket_number(self) -> str:
        """Генерирует уникальный номер тикета"""
        # Формат: TK + 6 случайных цифр и букв
        chars = string.ascii_uppercase + string.digits
        return "TK" + ''.join(random.choices(chars, k=6))
    
    async def create_support_ticket(
        self, 
        user_id: int, 
        message: str, 
        priority: str = "normal",
        subject: str = "Support Request"
    ) -> Optional[SupportTicket]:
        """Создает новый тикет поддержки"""
        try:
            # Генерируем уникальный номер тикета
            ticket_number = self._generate_ticket_number()
            
            # Проверяем уникальность номера тикета
            existing = await self.session.execute(
                select(SupportTicket).where(SupportTicket.ticket_number == ticket_number)
            )
            if existing.scalar_one_or_none():
                # Если номер уже существует, генерируем новый
                ticket_number = self._generate_ticket_number()
            
            # Создаем тикет
            ticket = SupportTicket(
                user_id=user_id,
                ticket_number=ticket_number,
                subject=subject,
                initial_message=message,
                priority=priority,
                status="open",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            self.session.add(ticket)
            await self.session.commit()
            await self.session.refresh(ticket)
            
            # Принудительно загружаем связанные данные для использования в уведомлениях
            loaded_ticket = await self.get_ticket_by_id(ticket.id)
            if not loaded_ticket:
                logger.error(f"Не удалось загрузить созданный тикет {ticket.id}")
                return ticket  # Возвращаем оригинальный тикет
            
            logger.info(f"Создан тикет поддержки #{ticket.ticket_number} для пользователя {user_id}")
            
            return loaded_ticket
            
        except Exception as e:
            logger.error(f"Ошибка при создании тикета поддержки: {e}")
            await self.session.rollback()
            return None
    
    async def get_user_tickets(
        self, 
        user_id: int, 
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[SupportTicket]:
        """Получает все тикеты для конкретного пользователя"""
        try:
            query = select(SupportTicket).where(SupportTicket.user_id == user_id)
            
            if status:
                query = query.where(SupportTicket.status == status)
            
            query = query.order_by(SupportTicket.created_at.desc()).limit(limit)
            
            result = await self.session.execute(query)
            tickets = result.scalars().all()
            
            return list(tickets)
            
        except Exception as e:
            logger.error(f"Ошибка при получении тикетов пользователя {user_id}: {e}")
            return []
    
    async def get_admin_tickets(
        self, 
        admin_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[SupportTicket]:
        """Получает тикеты для админской панели"""
        try:
            query = select(SupportTicket).options(
                selectinload(SupportTicket.user),
                selectinload(SupportTicket.assigned_admin)
            )
            
            if admin_id:
                query = query.where(SupportTicket.assigned_admin_id == admin_id)
            
            if status:
                query = query.where(SupportTicket.status == status)
            
            query = query.order_by(SupportTicket.created_at.desc()).limit(limit)
            
            result = await self.session.execute(query)
            tickets = result.scalars().all()
            
            return list(tickets)
            
        except Exception as e:
            logger.error(f"Ошибка при получении тикетов для админа: {e}")
            return []
    
    async def get_ticket_by_id(self, ticket_id: int) -> Optional[SupportTicket]:
        """Получает тикет по ID с загрузкой связанных данных"""
        try:
            query = select(SupportTicket).options(
                selectinload(SupportTicket.user),
                selectinload(SupportTicket.assigned_admin),
                selectinload(SupportTicket.responses)
            ).where(SupportTicket.id == ticket_id)
            
            result = await self.session.execute(query)
            ticket = result.scalar_one_or_none()
            
            # Если тикет найден, принудительно обновляем связи
            if ticket:
                await self.session.refresh(ticket, ['responses'])
            
            return ticket
            
        except Exception as e:
            logger.error(f"Ошибка при получении тикета {ticket_id}: {e}")
            return None
    
    async def get_ticket_by_number(self, ticket_number: str) -> Optional[SupportTicket]:
        """Получает тикет по номеру"""
        try:
            query = select(SupportTicket).options(
                selectinload(SupportTicket.user),
                selectinload(SupportTicket.assigned_admin),
                selectinload(SupportTicket.responses)
            ).where(SupportTicket.ticket_number == ticket_number)
            
            result = await self.session.execute(query)
            ticket = result.scalar_one_or_none()
            
            return ticket
            
        except Exception as e:
            logger.error(f"Ошибка при получении тикета {ticket_number}: {e}")
            return None
    
    async def add_response(
        self,
        ticket_id: int,
        sender_id: int,
        message: str,
        sender_type: str = "admin",
        is_internal: bool = False
    ) -> Optional[SupportResponse]:
        """Добавляет ответ к существующему тикету"""
        try:
            # Проверяем, что тикет существует
            ticket = await self.get_ticket_by_id(ticket_id)
            if not ticket:
                logger.error(f"Тикет {ticket_id} не найден")
                return None
            
            # Создаем ответ
            response = SupportResponse(
                ticket_id=ticket_id,
                sender_type=sender_type,
                sender_id=sender_id,
                message=message,
                is_internal=is_internal,
                created_at=datetime.now(timezone.utc)
            )
            
            self.session.add(response)
            
            # Обновляем время последнего обновления тикета
            await self.session.execute(
                update(SupportTicket)
                .where(SupportTicket.id == ticket_id)
                .values(updated_at=datetime.now(timezone.utc))
            )
            
            await self.session.commit()
            await self.session.refresh(response)
            
            logger.info(f"Добавлен ответ к тикету #{ticket.ticket_number} от {sender_type} {sender_id}")
            
            return response
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении ответа к тикету {ticket_id}: {e}")
            await self.session.rollback()
            return None
    
    async def update_ticket_status(
        self,
        ticket_id: int,
        status: str,
        admin_id: Optional[int] = None
    ) -> bool:
        """Обновляет статус тикета и назначение"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.now(timezone.utc)
            }
            
            if admin_id is not None:
                update_data["assigned_admin_id"] = admin_id
            
            if status == "closed":
                update_data["closed_at"] = datetime.now(timezone.utc)
            
            await self.session.execute(
                update(SupportTicket)
                .where(SupportTicket.id == ticket_id)
                .values(**update_data)
            )
            
            await self.session.commit()
            
            logger.info(f"Обновлен статус тикета {ticket_id} на {status}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса тикета {ticket_id}: {e}")
            await self.session.rollback()
            return False
    
    async def get_open_tickets_count(self) -> int:
        """Получает количество открытых тикетов"""
        try:
            result = await self.session.execute(
                select(SupportTicket).where(SupportTicket.status.in_(["open", "in_progress"]))
            )
            tickets = result.scalars().all()
            return len(tickets)
            
        except Exception as e:
            logger.error(f"Ошибка при подсчете открытых тикетов: {e}")
            return 0
    
    async def get_tickets_by_status(self, status: str, limit: int = 20) -> List[SupportTicket]:
        """Получает тикеты по статусу"""
        try:
            query = (
                select(SupportTicket)
                .options(selectinload(SupportTicket.user))
                .where(SupportTicket.status == status)
                .order_by(SupportTicket.created_at.desc())
                .limit(limit)
            )
            
            result = await self.session.execute(query)
            tickets = result.scalars().all()
            
            return list(tickets)
            
        except Exception as e:
            logger.error(f"Ошибка при получении тикетов со статусом {status}: {e}")
            return []
    
    async def close_ticket(self, ticket_id: int, admin_id: int) -> bool:
        """Закрывает тикет"""
        return await self.update_ticket_status(ticket_id, "closed", admin_id)
    
    async def assign_ticket(self, ticket_id: int, admin_id: int) -> bool:
        """Назначает тикет админу"""
        return await self.update_ticket_status(ticket_id, "in_progress", admin_id)
    
    async def reopen_ticket(self, ticket_id: int) -> bool:
        """Переоткрывает тикет"""
        return await self.update_ticket_status(ticket_id, "open")