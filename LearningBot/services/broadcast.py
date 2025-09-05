"""
Сервис для управления массовыми рассылками
"""
import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, desc, and_
from sqlalchemy.orm import selectinload
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from database.models import User, Admin, Broadcast
# from database.models import BroadcastDelivery  # ❌ Закомментировано для MVP

logger = logging.getLogger(__name__)


class BroadcastService:
    """Сервис для управления массовыми рассылками"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_broadcast(
        self,
        admin_id: int,
        text: str,
        media_type: Optional[str] = None,
        file_id: Optional[str] = None
    ) -> Optional[Broadcast]:
        """Создать новую рассылку"""
        try:
            broadcast = Broadcast(
                admin_id=admin_id,
                text=text,
                media_type=media_type,
                file_id=file_id,
                status="pending"
            )
            
            self.session.add(broadcast)
            await self.session.commit()
            await self.session.refresh(broadcast)
            
            logger.info(f"Создана новая рассылка ID {broadcast.id} от админа {admin_id}")
            return broadcast
            
        except Exception as e:
            logger.error(f"Ошибка при создании рассылки: {e}")
            await self.session.rollback()
            return None
    
    async def send_broadcast(
        self,
        broadcast_id: int,
        target_audience: str = "all",  # all, active, buyers
        bot_token: Optional[str] = None
    ) -> bool:
        """Отправить рассылку выбранной аудитории"""
        try:
            # Получаем рассылку
            broadcast = await self.get_broadcast_by_id(broadcast_id)
            if not broadcast or broadcast.status != "pending":
                logger.error(f"Рассылка {broadcast_id} не найдена или уже отправлена")
                return False
            
            # Обновляем статус на "sending"
            broadcast.status = "sending"
            await self.session.commit()
            
            # Получаем целевую аудиторию
            target_users = await self._get_target_users(target_audience)
            
            if not target_users:
                logger.warning("Нет пользователей для рассылки")
                broadcast.status = "completed"
                broadcast.total_users = 0
                broadcast.success_count = 0
                await self.session.commit()
                return True
            
            # ❌ УПРОЩЕНО ДЛЯ MVP - без детального трекинга доставки
            # Просто отправляем сообщения без сохранения детальной статистики
            # deliveries = []
            # for user in target_users:
            #     delivery = BroadcastDelivery(
            #         broadcast_id=broadcast_id,
            #         user_id=user.user_id,
            #         status="pending"
            #     )
            #     deliveries.append(delivery)
            # 
            # self.session.add_all(deliveries)
            # await self.session.commit()
            
            # Отправляем сообщения
            if bot_token:
                success_count = await self._send_messages_to_users(
                    broadcast, target_users, bot_token
                )
            else:
                success_count = 0
                logger.warning("Bot token не предоставлен, рассылка создана но не отправлена")
            
            # Обновляем статистику рассылки
            broadcast.status = "completed"
            broadcast.total_users = len(target_users)
            broadcast.success_count = success_count
            broadcast.sent_at = datetime.now(timezone.utc)
            await self.session.commit()
            
            logger.info(f"Рассылка {broadcast_id} отправлена: {success_count}/{len(target_users)} успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке рассылки {broadcast_id}: {e}")
            # Устанавливаем статус failed
            if 'broadcast' in locals():
                broadcast.status = "failed"
                await self.session.commit()
            return False
    
    async def _get_target_users(self, target_audience: str) -> List[User]:
        """Получить целевую аудиторию для рассылки"""
        try:
            if target_audience == "all":
                result = await self.session.execute(
                    select(User).order_by(User.id)
                )
            elif target_audience == "active":
                result = await self.session.execute(
                    select(User).where(User.is_active == True).order_by(User.id)
                )
            elif target_audience == "buyers":
                # Пользователи с покупками
                from database.models import Purchase
                result = await self.session.execute(
                    select(User).join(Purchase, User.user_id == Purchase.user_id)
                    .where(
                        and_(
                            User.is_active == True,
                            Purchase.status == "completed"
                        )
                    ).distinct().order_by(User.id)
                )
            else:
                logger.error(f"Неизвестная целевая аудитория: {target_audience}")
                return []
            
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Ошибка при получении целевой аудитории '{target_audience}': {e}")
            return []
    
    async def _send_messages_to_users(
        self,
        broadcast: Broadcast,
        users: List[User],
        bot_token: str
    ) -> int:
        """Отправить сообщения пользователям"""
        try:
            bot = Bot(token=bot_token)
            success_count = 0
            
            for user in users:
                try:
                    # Отправляем сообщение в зависимости от типа контента
                    if broadcast.media_type and broadcast.file_id:
                        if broadcast.media_type == "photo":
                            await bot.send_photo(
                                chat_id=user.user_id,
                                photo=broadcast.file_id,
                                caption=broadcast.text
                            )
                        elif broadcast.media_type == "video":
                            await bot.send_video(
                                chat_id=user.user_id,
                                video=broadcast.file_id,
                                caption=broadcast.text
                            )
                        elif broadcast.media_type == "document":
                            await bot.send_document(
                                chat_id=user.user_id,
                                document=broadcast.file_id,
                                caption=broadcast.text
                            )
                        else:
                            # Если неизвестный тип медиа, отправляем просто текст
                            await bot.send_message(
                                chat_id=user.user_id,
                                text=broadcast.text
                            )
                    else:
                        # Текстовое сообщение
                        await bot.send_message(
                            chat_id=user.user_id,
                            text=broadcast.text
                        )
                    
                    # ❌ УПРОЩЕНО ДЛЯ MVP - без детального трекинга
                    # await self._update_delivery_status(
                    #     broadcast.id, user.user_id, "sent", None
                    # )
                    success_count += 1
                    
                    # Небольшая задержка для избежания лимитов
                    await asyncio.sleep(0.05)
                    
                except (TelegramBadRequest, TelegramForbiddenError) as e:
                    # ❌ УПРОЩЕНО ДЛЯ MVP - без детального трекинга
                    # await self._update_delivery_status(
                    #     broadcast.id, user.user_id, "failed", str(e)
                    # )
                    logger.warning(f"Не удалось отправить сообщение пользователю {user.user_id}: {e}")
                    
                except Exception as e:
                    # ❌ УПРОЩЕНО ДЛЯ MVP - без детального трекинга
                    # await self._update_delivery_status(
                    #     broadcast.id, user.user_id, "failed", str(e)
                    # )
                    logger.error(f"Ошибка при отправке пользователю {user.user_id}: {e}")
            
            await bot.session.close()
            return success_count
            
        except Exception as e:
            logger.error(f"Критическая ошибка при отправке сообщений: {e}")
            return 0
    
    # ❌ ЗАКОММЕНТИРОВАНО ДЛЯ MVP - детальный трекинг доставки не нужен
    # async def _update_delivery_status(
    #     self,
    #     broadcast_id: int,
    #     user_id: int,
    #     status: str,
    #     error_message: Optional[str] = None
    # ):
    #     """Обновить статус доставки"""
    #     try:
    #         await self.session.execute(
    #             update(BroadcastDelivery)
    #             .where(
    #                 and_(
    #                     BroadcastDelivery.broadcast_id == broadcast_id,
    #                     BroadcastDelivery.user_id == user_id
    #                 )
    #             )
    #             .values(
    #                 status=status,
    #                 sent_at=datetime.now(timezone.utc) if status == "sent" else None,
    #                 error_message=error_message,
    #                 delivery_attempts=BroadcastDelivery.delivery_attempts + 1
    #             )
    #         )
    #         await self.session.commit()
    #         
    #     except Exception as e:
    #         logger.error(f"Ошибка при обновлении статуса доставки: {e}")
    
    async def get_broadcast_by_id(self, broadcast_id: int) -> Optional[Broadcast]:
        """Получить рассылку по ID"""
        try:
            result = await self.session.execute(
                select(Broadcast).where(Broadcast.id == broadcast_id)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Ошибка при получении рассылки {broadcast_id}: {e}")
            return None
    
    async def get_broadcasts_history(
        self,
        admin_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Broadcast]:
        """Получить историю рассылок"""
        try:
            query = select(Broadcast).order_by(desc(Broadcast.sent_at))
            
            if admin_id:
                query = query.where(Broadcast.admin_id == admin_id)
            
            query = query.limit(limit).offset(offset)
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Ошибка при получении истории рассылок: {e}")
            return []
    
    async def get_broadcast_statistics(self, broadcast_id: int) -> Optional[Dict[str, Any]]:
        """Получить статистику рассылки"""
        try:
            broadcast = await self.get_broadcast_by_id(broadcast_id)
            if not broadcast:
                return None
            
            # Получаем детальную статистику доставки
            delivery_stats = await self.get_delivery_statistics(broadcast_id)
            
            success_rate = 0
            if broadcast.total_users > 0:
                success_rate = round((broadcast.success_count / broadcast.total_users) * 100, 2)
            
            return {
                'broadcast_id': broadcast.id,
                'text': broadcast.text,
                'media_type': broadcast.media_type,
                'status': broadcast.status,
                'sent_at': broadcast.sent_at,
                'total_users': broadcast.total_users,
                'success_count': broadcast.success_count,
                'failed_count': broadcast.total_users - broadcast.success_count,
                'success_rate': success_rate,
                'delivery_details': delivery_stats
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики рассылки {broadcast_id}: {e}")
            return None
    
    # ❌ ЗАКОММЕНТИРОВАНО ДЛЯ MVP - детальная статистика доставки не нужна
    # async def get_delivery_statistics(self, broadcast_id: int) -> Dict[str, int]:
    #     """Получить детальную статистику доставки"""
    #     # Использует BroadcastDelivery
    #     return {"sent": 0, "failed": 0, "pending": 0, "total": 0}
    
    # ❌ ЗАКОММЕНТИРОВАНО ДЛЯ MVP - детальные записи доставки не нужны
    # async def get_broadcast_deliveries(
    #     self,
    #     broadcast_id: int,
    #     status: Optional[str] = None
    # ) -> List[BroadcastDelivery]:
    #     """Получить записи о доставке рассылки"""
    #     return []
    
    async def cancel_broadcast(self, broadcast_id: int) -> bool:
        """Отменить рассылку"""
        try:
            broadcast = await self.get_broadcast_by_id(broadcast_id)
            if not broadcast:
                return False
            
            # Можно отменить только pending рассылки
            if broadcast.status != "pending":
                return False
            
            broadcast.status = "cancelled"
            await self.session.commit()
            
            logger.info(f"Рассылка {broadcast_id} отменена")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отмене рассылки {broadcast_id}: {e}")
            return False
    
    async def delete_broadcast(self, broadcast_id: int) -> bool:
        """Удалить рассылку (упрощено для MVP)"""
        try:
            # ❌ УПРОЩЕНО ДЛЯ MVP - удаляем только саму рассылку
            # await self.session.execute(
            #     delete(BroadcastDelivery).where(
            #         BroadcastDelivery.broadcast_id == broadcast_id
            #     )
            # )
            
            # Удаляем саму рассылку
            result = await self.session.execute(
                delete(Broadcast).where(Broadcast.id == broadcast_id)
            )
            
            await self.session.commit()
            
            if result.rowcount > 0:
                logger.info(f"Рассылка {broadcast_id} удалена")
                return True
            else:
                return False
            
        except Exception as e:
            logger.error(f"Ошибка при удалении рассылки {broadcast_id}: {e}")
            await self.session.rollback()
            return False
    
    async def get_active_broadcasts(self) -> List[Broadcast]:
        """Получить активные рассылки (pending и sending)"""
        try:
            result = await self.session.execute(
                select(Broadcast).where(
                    Broadcast.status.in_(["pending", "sending"])
                ).order_by(desc(Broadcast.sent_at))
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Ошибка при получении активных рассылок: {e}")
            return []