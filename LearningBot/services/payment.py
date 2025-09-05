"""
Сервис для работы с оплатой через Telegram Stars
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram import Bot
from aiogram.types import LabeledPrice

from database.models import Purchase, User, Lesson
from services.user import UserService

logger = logging.getLogger(__name__)


class PaymentService:
    """Сервис для обработки платежей через Telegram Stars"""
    
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
    
    async def create_invoice(
        self, 
        user_id: int, 
        lesson_id: int, 
        lesson_title: str, 
        lesson_description: str,
        price_stars: int
    ) -> bool:
        """
        Создание инвойса для оплаты урока через Telegram Stars
        """
        try:
            # Проверка валидности данных
            if price_stars <= 0:
                logger.error(f"Некорректная цена: {price_stars} звезд")
                return False
            
            # Формирование payload для отслеживания платежа
            payload = f"lesson_{lesson_id}_{user_id}_{int(datetime.now(timezone.utc).timestamp())}"
            
            # Создание инвойса
            await self.bot.send_invoice(
                chat_id=user_id,
                title=lesson_title,
                description=lesson_description,
                payload=payload,
                provider_token="",  # Пустой для Telegram Stars
                currency="XTR",  # Telegram Stars
                prices=[
                    LabeledPrice(
                        label=f"Урок: {lesson_title}",
                        amount=price_stars
                    )
                ],
                max_tip_amount=0,  # Без чаевых
                suggested_tip_amounts=[],
                photo_url=None,  # Можно добавить изображение урока
                photo_size=None,
                photo_width=None,
                photo_height=None,
                need_name=False,
                need_phone_number=False,
                need_email=False,
                need_shipping_address=False,
                send_phone_number_to_provider=False,
                send_email_to_provider=False,
                is_flexible=False
            )
            
            logger.info(f"Инвойс создан для пользователя {user_id}, урок {lesson_id}, цена {price_stars} звезд")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при создании инвойса: {e}")
            return False
    
    async def process_pre_checkout(
        self, 
        pre_checkout_query_id: str, 
        user_id: int, 
        total_amount: int, 
        invoice_payload: str
    ) -> tuple[bool, Optional[str]]:
        """
        Обработка pre-checkout query (валидация перед оплатой)
        Возвращает (успех, сообщение об ошибке)
        """
        try:
            # Парсинг payload
            payload_parts = invoice_payload.split("_")
            if len(payload_parts) < 3 or payload_parts[0] != "lesson":
                return False, "Некорректные данные платежа"
            
            lesson_id = int(payload_parts[1])
            expected_user_id = int(payload_parts[2])
            
            # Проверка соответствия пользователя
            if user_id != expected_user_id:
                return False, "Несоответствие пользователя"
            
            # Получение урока
            lesson_result = await self.session.execute(
                select(Lesson).where(Lesson.id == lesson_id)
            )
            lesson = lesson_result.scalar_one_or_none()
            
            if not lesson:
                return False, "Урок не найден"
            
            if not lesson.is_active:
                return False, "Урок недоступен"
            
            if lesson.is_free:
                return False, "Этот урок бесплатный"
            
            # Проверка цены
            if total_amount != lesson.price_stars:
                return False, f"Некорректная сумма. Ожидается {lesson.price_stars} звезд"
            
            # Проверка, не купил ли пользователь уже этот урок
            existing_purchase = await self.session.execute(
                select(Purchase).where(
                    Purchase.user_id == user_id,
                    Purchase.lesson_id == lesson_id,
                    Purchase.status == "completed"
                )
            )
            
            if existing_purchase.scalar_one_or_none():
                return False, "Урок уже приобретен"
            
            logger.info(f"Pre-checkout валидация пройдена для пользователя {user_id}, урок {lesson_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"Ошибка при обработке pre-checkout: {e}")
            return False, "Внутренняя ошибка сервера"
    
    async def process_successful_payment(
        self, 
        user_id: int, 
        payment_charge_id: str, 
        total_amount: int, 
        invoice_payload: str
    ) -> Optional[Purchase]:
        """
        Обработка успешного платежа
        Возвращает объект Purchase или None при ошибке
        """
        try:
            # Парсинг payload
            payload_parts = invoice_payload.split("_")
            if len(payload_parts) < 3 or payload_parts[0] != "lesson":
                logger.error(f"Некорректный payload: {invoice_payload}")
                return None
            
            lesson_id = int(payload_parts[1])
            
            # Получение урока
            lesson_result = await self.session.execute(
                select(Lesson).where(Lesson.id == lesson_id)
            )
            lesson = lesson_result.scalar_one_or_none()
            
            if not lesson:
                logger.error(f"Урок не найден: {lesson_id}")
                return None
            
            # Проверка на дублирующий платеж
            existing_purchase = await self.session.execute(
                select(Purchase).where(
                    Purchase.payment_charge_id == payment_charge_id
                )
            )
            
            if existing_purchase.scalar_one_or_none():
                logger.warning(f"Попытка дублирующего платежа: {payment_charge_id}")
                return None
            
            # Создание записи о покупке
            purchase = Purchase(
                user_id=user_id,
                lesson_id=lesson_id,
                payment_charge_id=payment_charge_id,
                purchase_date=datetime.now(timezone.utc),
                status="completed",
                amount_stars=total_amount
            )
            
            self.session.add(purchase)
            
            # Обновление статистики пользователя
            user_service = UserService(self.session)
            user = await user_service.get_user_by_telegram_id(user_id)
            
            if user:
                user.total_spent += total_amount
                await self.session.commit()
                await self.session.refresh(purchase)
            
            # Логирование успешной покупки
            await user_service.log_user_activity(
                user_id, 
                "purchase_completed", 
                lesson_id=lesson_id,
                extra_data=f"stars:{total_amount}"
            )
            
            logger.info(f"Платеж обработан успешно: пользователь {user_id}, урок {lesson_id}, сумма {total_amount}")
            return purchase
            
        except Exception as e:
            logger.error(f"Ошибка при обработке успешного платежа: {e}")
            await self.session.rollback()
            return None
    
    async def refund_payment(
        self, 
        user_id: int, 
        payment_charge_id: str
    ) -> bool:
        """
        Возврат платежа
        """
        try:
            # Поиск покупки
            purchase_result = await self.session.execute(
                select(Purchase).where(
                    Purchase.user_id == user_id,
                    Purchase.payment_charge_id == payment_charge_id,
                    Purchase.status == "completed"
                )
            )
            
            purchase = purchase_result.scalar_one_or_none()
            
            if not purchase:
                logger.error(f"Покупка не найдена для возврата: {payment_charge_id}")
                return False
            
            # Выполнение возврата через Telegram API
            refund_result = await self.bot.refund_star_payment(
                user_id=user_id,
                telegram_payment_charge_id=payment_charge_id
            )
            
            if refund_result:
                # Обновление статуса покупки
                purchase.status = "refunded"
                purchase.refunded_at = datetime.now(timezone.utc)
                
                # Обновление статистики пользователя
                user_result = await self.session.execute(
                    select(User).where(User.user_id == user_id)
                )
                user = user_result.scalar_one_or_none()
                
                if user and user.total_spent >= purchase.amount_stars:
                    user.total_spent -= purchase.amount_stars
                
                await self.session.commit()
                
                # Логирование возврата
                user_service = UserService(self.session)
                await user_service.log_user_activity(
                    user_id, 
                    "payment_refunded", 
                    lesson_id=purchase.lesson_id,
                    extra_data=f"stars:{purchase.amount_stars}"
                )
                
                logger.info(f"Возврат выполнен успешно: {payment_charge_id}")
                return True
            else:
                logger.error(f"Telegram API отклонил возврат: {payment_charge_id}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при возврате платежа: {e}")
            await self.session.rollback()
            return False
    
    async def get_bot_balance(self) -> Optional[int]:
        """
        Получение баланса бота в звездах
        """
        try:
            balance_result = await self.bot.get_my_star_balance()
            return balance_result.star_count if balance_result else None
            
        except Exception as e:
            logger.error(f"Ошибка при получении баланса: {e}")
            return None
    
    async def get_star_balance(self) -> Optional[int]:
        """
        Псевдоним для get_bot_balance для совместимости с тестами
        """
        return await self.get_bot_balance()
    
    async def get_star_transactions(
        self, 
        offset: int = 0, 
        limit: int = 100
    ) -> Optional[list]:
        """
        Получение списка транзакций звезд
        """
        try:
            transactions_result = await self.bot.get_star_transactions(
                offset=offset,
                limit=limit
            )
            
            return transactions_result.transactions if transactions_result else None
            
        except Exception as e:
            logger.error(f"Ошибка при получении транзакций: {e}")
            return None
    
    async def validate_payment_data(
        self, 
        user_id: int, 
        lesson_id: int
    ) -> tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Валидация данных перед созданием платежа
        Возвращает (успех, сообщение об ошибке, данные урока)
        """
        try:
            # Получение урока
            lesson_result = await self.session.execute(
                select(Lesson).where(Lesson.id == lesson_id)
            )
            lesson = lesson_result.scalar_one_or_none()
            
            if not lesson:
                return False, "Урок не найден", None
            
            if not lesson.is_active:
                return False, "Урок недоступен", None
            
            if lesson.is_free:
                return False, "Этот урок бесплатный", None
            
            if lesson.price_stars <= 0:
                return False, "Некорректная цена урока", None
            
            # Проверка на существующую покупку
            existing_purchase = await self.session.execute(
                select(Purchase).where(
                    Purchase.user_id == user_id,
                    Purchase.lesson_id == lesson_id,
                    Purchase.status == "completed"
                )
            )
            
            if existing_purchase.scalar_one_or_none():
                return False, "Урок уже приобретен", None
            
            # Возврат данных урока
            lesson_data = {
                "id": lesson.id,
                "title": lesson.title,
                "description": lesson.description,
                "price_stars": lesson.price_stars,
                "content_type": lesson.content_type
            }
            
            return True, None, lesson_data
            
        except Exception as e:
            logger.error(f"Ошибка при валидации платежных данных: {e}")
            return False, "Внутренняя ошибка сервера", None