"""
Сервис для отправки уведомлений
"""
import logging
from typing import List, Optional
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from services.admin import AdminService
from database.models import SupportTicket, Admin

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для отправки уведомлений администраторам"""
    
    def __init__(self, bot: Bot, session: AsyncSession):
        self.bot = bot
        self.session = session
        self.admin_service = AdminService(session)
    
    async def notify_admins_of_support_request(self, ticket: SupportTicket) -> bool:
        """Отправляет уведомление всем активным администраторам о новом тикете поддержки"""
        try:
            # Получаем всех активных администраторов
            admins = await self.admin_service.get_all_admins()
            active_admins = [admin for admin in admins if admin.is_active]
            
            if not active_admins:
                logger.warning("Нет активных администраторов для уведомления о поддержке")
                return False
            
            # Формируем сообщение уведомления
            notification_message = f"""
🆘 <b>Новое обращение в поддержку #{ticket.ticket_number}</b>

👤 <b>Пользователь:</b> {ticket.user.full_name}
🆔 <b>ID:</b> <code>{ticket.user_id}</code>
📱 <b>Username:</b> @{ticket.user.username or 'не указан'}

💬 <b>Сообщение:</b>
{ticket.initial_message}

🔥 <b>Приоритет:</b> {ticket.priority.upper()}
🕒 <b>Время:</b> {ticket.created_at.strftime('%d.%m.%Y %H:%M')}

Используйте /admin для управления тикетами поддержки.
"""
            
            # Отправляем уведомления всем активным администраторам
            success_count = 0
            failed_admins = []
            
            for admin in active_admins:
                try:
                    await self.bot.send_message(
                        chat_id=admin.user_id,
                        text=notification_message,
                        parse_mode="HTML"
                    )
                    success_count += 1
                    logger.info(f"Уведомление о тикете #{ticket.ticket_number} отправлено админу {admin.user_id}")
                    
                except Exception as e:
                    logger.error(f"Не удалось отправить уведомление админу {admin.user_id}: {e}")
                    failed_admins.append(admin.user_id)
            
            # Логируем результаты
            if success_count > 0:
                logger.info(f"Уведомления о тикете #{ticket.ticket_number} отправлены {success_count} администраторам")
            
            if failed_admins:
                logger.warning(f"Не удалось отправить уведомления администраторам: {failed_admins}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений о тикете #{ticket.ticket_number}: {e}")
            return False
    
    async def notify_user_of_response(self, ticket: SupportTicket, response_message: str, admin_name: str = "Support") -> bool:
        """Отправляет уведомление пользователю о новом ответе от поддержки"""
        try:
            notification_message = f"""
💬 <b>Новый ответ по тикету #{ticket.ticket_number}</b>

👨‍💼 <b>Ответ от:</b> {admin_name}

📝 <b>Сообщение:</b>
{response_message}

——————————————————
Если у вас есть дополнительные вопросы, просто ответьте на это сообщение.
"""
            
            await self.bot.send_message(
                chat_id=ticket.user_id,
                text=notification_message,
                parse_mode="HTML"
            )
            
            logger.info(f"Уведомление о ответе отправлено пользователю {ticket.user_id} по тикету #{ticket.ticket_number}")
            return True
            
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление пользователю {ticket.user_id}: {e}")
            return False
    
    async def notify_admin_of_status_change(self, ticket: SupportTicket, old_status: str, new_status: str, admin_id: int) -> bool:
        """Уведомляет назначенного администратора об изменении статуса тикета"""
        try:
            if not ticket.assigned_admin_id or ticket.assigned_admin_id == admin_id:
                return True  # Не отправляем уведомление самому себе или если админ не назначен
            
            status_text = {
                "open": "🟡 Открыт",
                "in_progress": "🔵 В работе", 
                "closed": "🟢 Закрыт"
            }
            
            notification_message = f"""
🔄 <b>Изменение статуса тикета #{ticket.ticket_number}</b>

📊 <b>Статус изменен:</b> {status_text.get(old_status, old_status)} → {status_text.get(new_status, new_status)}

👤 <b>Пользователь:</b> {ticket.user.full_name}
💬 <b>Проблема:</b> {ticket.initial_message[:100]}{'...' if len(ticket.initial_message) > 100 else ''}

Используйте /admin для просмотра деталей.
"""
            
            await self.bot.send_message(
                chat_id=ticket.assigned_admin_id,
                text=notification_message,
                parse_mode="HTML"
            )
            
            logger.info(f"Уведомление об изменении статуса отправлено админу {ticket.assigned_admin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление об изменении статуса: {e}")
            return False
    
    async def notify_admin_of_new_message(self, ticket: SupportTicket, message: str) -> bool:
        """Уведомляет назначенного администратора о новом сообщении от пользователя"""
        try:
            if not ticket.assigned_admin_id:
                # Если админ не назначен, уведомляем всех активных админов
                return await self.notify_admins_of_support_request(ticket)
            
            notification_message = f"""
💬 <b>Новое сообщение по тикету #{ticket.ticket_number}</b>

👤 <b>От пользователя:</b> {ticket.user.full_name}
📝 <b>Сообщение:</b>
{message}

🕒 <b>Время:</b> {ticket.updated_at.strftime('%d.%m.%Y %H:%M')}

Используйте /admin для ответа.
"""
            
            await self.bot.send_message(
                chat_id=ticket.assigned_admin_id,
                text=notification_message,
                parse_mode="HTML"
            )
            
            logger.info(f"Уведомление о новом сообщении отправлено админу {ticket.assigned_admin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление о новом сообщении: {e}")
            return False
    
    async def send_broadcast_notification(self, message: str, admin_ids: Optional[List[int]] = None) -> int:
        """Отправляет массовое уведомление администраторам"""
        try:
            if admin_ids is None:
                # Получаем всех активных администраторов
                admins = await self.admin_service.get_all_admins()
                admin_ids = [admin.user_id for admin in admins if admin.is_active]
            
            success_count = 0
            
            for admin_id in admin_ids:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=message,
                        parse_mode="HTML"
                    )
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Не удалось отправить broadcast админу {admin_id}: {e}")
            
            logger.info(f"Broadcast отправлен {success_count} администраторам")
            return success_count
            
        except Exception as e:
            logger.error(f"Ошибка при отправке broadcast: {e}")
            return 0