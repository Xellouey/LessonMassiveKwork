"""
Обработчики системы оплаты через Telegram Stars
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, PreCheckoutQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.payment import PaymentService
from services.lesson import LessonService
from services.user import UserService
from keyboards.user import lesson_detail_keyboard, main_menu_keyboard, InlineKeyboardMarkup, InlineKeyboardButton
from states.user import PaymentStates

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data.startswith("buy_lesson:"))
async def initiate_lesson_purchase(callback: CallbackQuery, session: AsyncSession):
    """Инициация покупки урока с выбором способа оплаты"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        
        lesson_service = LessonService(session)
        lesson = await lesson_service.get_lesson_by_id(lesson_id)
        
        if not lesson:
            await callback.answer("❌ Урок не найден")
            return
        
        if lesson.is_free:
            await callback.answer("❌ Этот урок бесплатный")
            return
        
        # Проверяем, не купил ли уже пользователь этот урок
        has_access = await lesson_service.check_user_has_lesson(
            callback.from_user.id, 
            lesson_id
        )
        
        if has_access:
            await callback.answer("✅ Урок уже приобретен")
            return
        
        from services.currency import CurrencyService
        usd_price = CurrencyService.format_usd_price(lesson.price_usd)
        
        # Показываем окно выбора способа оплаты
        payment_selection_text = f"""
💳 <b>Оплата урока</b>

📚 <b>Урок:</b> {lesson.title}
💰 <b>Цена:</b> {usd_price}

🔄 <b>Выберите способ оплаты:</b>

<i>После выбора способа оплаты будет создан инвойс с автоматической конвертацией в соответствующую валюту.</i>
"""
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        payment_methods_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="⭐ Telegram Stars", 
                callback_data=f"pay_stars:{lesson_id}"
            )],
            [InlineKeyboardButton(
                text="🔙 Назад к уроку", 
                callback_data=f"lesson:{lesson_id}"
            )],
            [InlineKeyboardButton(
                text="📚 К каталогу", 
                callback_data="catalog"
            )]
        ])
        
        await callback.message.edit_text(
            payment_selection_text,
            reply_markup=payment_methods_keyboard
        )
        await callback.answer()
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID урока")
    except Exception as e:
        logger.error(f"Ошибка при инициации покупки: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("pay_stars:"))
async def process_stars_payment(callback: CallbackQuery, session: AsyncSession):
    """Обработка оплаты через Telegram Stars"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        
        lesson_service = LessonService(session)
        lesson = await lesson_service.get_lesson_by_id(lesson_id)
        
        if not lesson:
            await callback.answer("❌ Урок не найден")
            return
        
        from services.currency import CurrencyService
        usd_price = CurrencyService.format_usd_price(lesson.price_usd)
        
        # Создаем инвойс
        payment_service = PaymentService(session, callback.bot)
        
        invoice_created = await payment_service.create_invoice(
            user_id=callback.from_user.id,
            lesson_id=lesson_id,
            lesson_title=lesson.title,
            lesson_description=f"Доступ к уроку: {lesson.description[:100]}...",
            price_stars=lesson.price_stars,
            price_usd=lesson.price_usd
        )
        
        if invoice_created:
            await callback.answer("💳 Инвойс отправлен!")
            
            payment_info_text = f"""
💳 <b>Инвойс создан</b>

📚 <b>Урок:</b> {lesson.title}
💰 <b>Цена:</b> {usd_price}
⭐ <b>К оплате:</b> {lesson.price_stars} Telegram Stars

🔄 <b>Статус:</b> Ожидание оплаты...

<i>Telegram автоматически конвертирует {usd_price} в {lesson.price_stars} звезд. Следуйте инструкциям в чате для завершения оплаты.</i>
"""
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            payment_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👤 Мои покупки", callback_data="my_purchases")],
                [InlineKeyboardButton(text="📚 К каталогу", callback_data="catalog")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
            ])
            
            await callback.message.edit_text(
                payment_info_text,
                reply_markup=payment_keyboard
            )
        else:
            await callback.answer("❌ Ошибка при создании инвойса")
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректные данные")
    except Exception as e:
        logger.error(f"Ошибка при оплате через Stars: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery, session: AsyncSession):
    """Обработка pre-checkout query (валидация перед платежом)"""
    try:
        payment_service = PaymentService(session, pre_checkout_query.bot)
        
        # Валидация платежа
        is_valid, error_message = await payment_service.process_pre_checkout(
            pre_checkout_query_id=pre_checkout_query.id,
            user_id=pre_checkout_query.from_user.id,
            total_amount=pre_checkout_query.total_amount,
            invoice_payload=pre_checkout_query.invoice_payload
        )
        
        if is_valid:
            # Подтверждение платежа
            await pre_checkout_query.answer(ok=True)
            logger.info(f"Pre-checkout подтвержден для пользователя {pre_checkout_query.from_user.id}")
        else:
            # Отклонение платежа
            await pre_checkout_query.answer(
                ok=False, 
                error_message=error_message or "Ошибка при проверке платежа"
            )
            logger.warning(f"Pre-checkout отклонен: {error_message}")
            
    except Exception as e:
        logger.error(f"Ошибка в pre-checkout query: {e}")
        await pre_checkout_query.answer(
            ok=False, 
            error_message="Внутренняя ошибка сервера"
        )


@router.message(F.successful_payment)
async def process_successful_payment(message: Message, session: AsyncSession):
    """Обработка успешного платежа"""
    try:
        payment = message.successful_payment
        payment_service = PaymentService(session, message.bot)
        
        # Обработка успешного платежа
        purchase = await payment_service.process_successful_payment(
            user_id=message.from_user.id,
            payment_charge_id=payment.telegram_payment_charge_id,
            total_amount=payment.total_amount,
            invoice_payload=payment.invoice_payload
        )
        
        if purchase:
            # Получение информации об уроке
            lesson_service = LessonService(session)
            lesson = await lesson_service.get_lesson_by_id(purchase.lesson_id)
            
            if lesson:
                from services.currency import CurrencyService
                usd_price = CurrencyService.format_usd_price(lesson.price_usd)
                
                # Уведомление об успешной покупке
                success_text = f"""
🎉 <b>Платеж успешно завершен!</b>

✅ <b>Урок приобретен:</b> {lesson.title}
💰 <b>Оплачено:</b> {usd_price}
📅 <b>Дата покупки:</b> {purchase.purchase_date.strftime('%d.%m.%Y %H:%M')}

🚀 <b>Урок уже доступен!</b>
Вы можете начать изучение прямо сейчас или найти урок в разделе "Мои покупки".

<i>Спасибо за покупку! Желаем продуктивного обучения! 🎓</i>
"""
                
                success_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="▶️ Открыть урок", callback_data=f"open_lesson:{lesson.id}")],
                    [InlineKeyboardButton(text="👤 Мои покупки", callback_data="my_purchases")],
                    [InlineKeyboardButton(text="📚 Больше уроков", callback_data="catalog")],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                ])
                
                await message.answer(
                    success_text,
                    reply_markup=success_keyboard
                )
                
                # Дополнительно можно отправить сам контент урока
                if lesson.content_type and lesson.file_id:
                    content_text = f"📚 <b>Ваш урок готов к изучению:</b>\n\n{lesson.title}"
                    
                    if lesson.content_type == "video":
                        await message.answer_video(
                            video=lesson.file_id,
                            caption=content_text
                        )
                    elif lesson.content_type == "photo":
                        await message.answer_photo(
                            photo=lesson.file_id,
                            caption=content_text
                        )
                    elif lesson.content_type == "document":
                        await message.answer_document(
                            document=lesson.file_id,
                            caption=content_text
                        )
                    elif lesson.content_type == "audio":
                        await message.answer_audio(
                            audio=lesson.file_id,
                            caption=content_text
                        )
                
                logger.info(f"Платеж успешно обработан: пользователь {message.from_user.id}, урок {lesson.id}")
                
            else:
                await message.answer(
                    "✅ Платеж завершен, но возникла ошибка при получении урока. Обратитесь в поддержку.",
                    reply_markup=main_menu_keyboard()
                )
        else:
            await message.answer(
                "❌ Ошибка при обработке платежа. Если средства были списаны, обратитесь в поддержку.",
                reply_markup=main_menu_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Ошибка при обработке успешного платежа: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке платежа. Обратитесь в поддержку, если средства были списаны.",
            reply_markup=main_menu_keyboard()
        )


@router.callback_query(F.data == "payment_help")
async def show_payment_help(callback: CallbackQuery):
    """Показать справку по оплате"""
    try:
        help_text = """
💡 <b>Справка по оплате</b>

🌟 <b>Telegram Stars - что это?</b>
Telegram Stars - это внутренняя валюта Telegram для покупок в ботах и каналах.

💳 <b>Как купить Stars:</b>
1. Откройте настройки Telegram
2. Перейдите в "Telegram Stars" 
3. Выберите количество для покупки
4. Оплатите удобным способом

💰 <b>Как оплатить урок:</b>
1. Выберите урок в каталоге
2. Нажмите "Купить урок"
3. Подтвердите платеж в появившемся окне
4. Получите мгновенный доступ к уроку

🔒 <b>Безопасность:</b>
• Все платежи защищены Telegram
• Средства списываются только после подтверждения
• Возможен возврат в течение 48 часов

❓ <b>Проблемы с оплатой?</b>
• Проверьте баланс Stars в Telegram
• Убедитесь в стабильном интернете
• Обратитесь в поддержку: @support_bot
"""
        
        help_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Купить Stars", url="https://t.me/BotFather")],  # Ссылка на покупку Stars
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ])
        
        await callback.message.edit_text(
            help_text,
            reply_markup=help_keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе справки по оплате: {e}")
        await callback.answer("❌ Ошибка при загрузке справки")


@router.callback_query(F.data == "payment_status")
async def check_payment_status(callback: CallbackQuery, session: AsyncSession):
    """Проверить статус платежей пользователя"""
    try:
        user_service = UserService(session)
        user = await user_service.get_user_by_telegram_id(callback.from_user.id)
        
        if not user:
            await callback.answer("❌ Пользователь не найден")
            return
        
        # Получение статистики покупок
        lesson_service = LessonService(session)
        purchases, total_purchases = await lesson_service.get_user_purchases(
            callback.from_user.id, 
            page=0, 
            per_page=5
        )
        
        status_text = f"""
💳 <b>Статус ваших платежей</b>

👤 <b>Пользователь:</b> {user.full_name}
💰 <b>Всего потрачено:</b> ⭐ {user.total_spent} звезд
📊 <b>Всего покупок:</b> {total_purchases}

📅 <b>Последние покупки:</b>
"""
        
        if purchases:
            for i, purchase_data in enumerate(purchases[:3], 1):
                purchase = purchase_data['purchase']
                lesson = purchase_data['lesson']
                
                status_text += f"""
{i}. 📚 <b>{lesson.title}</b>
   💰 {purchase.amount_stars} ⭐ • {purchase.purchase_date.strftime('%d.%m.%Y')}
"""
        else:
            status_text += "\n<i>Пока нет покупок</i>"
        
        status_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 Все покупки", callback_data="my_purchases")],
            [InlineKeyboardButton(text="📚 Купить урок", callback_data="catalog")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await callback.message.edit_text(
            status_text,
            reply_markup=status_keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса платежей: {e}")
        await callback.answer("❌ Ошибка при получении статуса")