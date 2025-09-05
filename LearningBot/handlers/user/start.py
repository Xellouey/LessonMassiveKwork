"""
Обработчики команд для пользователей - старт и регистрация
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.user import UserService
from keyboards.user import main_menu_keyboard, settings_keyboard, language_keyboard, InlineKeyboardMarkup, InlineKeyboardButton
from states.user import UserStates

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext):
    """
    Обработчик команды /start
    Регистрирует нового пользователя или приветствует существующего
    """
    try:
        # Очистка состояния
        await state.clear()
        
        # Получение данных пользователя из Telegram
        if not message.from_user:
            await message.answer("⚠️ Не удалось получить данные пользователя")
            return
            
        user_id = message.from_user.id
        username = message.from_user.username
        full_name = message.from_user.full_name or "Пользователь"
        
        # Создание сервиса для работы с пользователями
        user_service = UserService(session)
        
        # Получение или создание пользователя
        user = await user_service.get_or_create_user(
            user_id=user_id,
            username=username,
            full_name=full_name
        )
        
        # Логирование активности
        await user_service.log_user_activity(user_id, "start_command")
        
        # Проверка, новый ли это пользователь
        is_new_user = user.registration_date.date() == user.last_activity.date()
        
        if is_new_user:
            # Приветствие для нового пользователя
            welcome_text = f"""
🤖 <b>Добро пожаловать в мир ИИ, {full_name}!</b>

Это образовательная платформа по искусственному интеллекту, где вы можете:
🧠 Освоить нейронные сети и машинное обучение
🎁 Получить бесплатные уроки по основам ИИ  
✨ Покупать премиум AI-курсы за звезды Telegram
📊 Отслеживать свой прогресс в изучении ИИ

<i>Выберите действие в меню ниже:</i>
"""
            
            # Отправка приветственного сообщения новому пользователю
            await message.answer(
                welcome_text,
                reply_markup=main_menu_keyboard()
            )
            
        else:
            # Приветствие для существующего пользователя
            welcome_back_text = f"""
👋 <b>Привет, {full_name}!</b>

Рад видеть вас снова в нашем AI-боте! 

📈 <b>Ваша статистика:</b>
💰 Потрачено на AI-образование: {user.total_spent} ⭐
📅 Последний визит: {user.last_activity.strftime('%d.%m.%Y %H:%M')}

<i>Какие новые технологии ИИ будем изучать сегодня?</i>
"""
            
            await message.answer(
                welcome_back_text,
                reply_markup=main_menu_keyboard()
            )
        
        logger.info(f"Пользователь {user_id} ({username}) {'зарегистрирован' if is_new_user else 'вошел в систему'}")
        
    except Exception as e:
        logger.error(f"Ошибка в команде /start для пользователя {message.from_user.id if message.from_user else 'Unknown'}: {e}")
        await message.answer(
            "😔 Произошла ошибка при запуске бота. Попробуйте позже или обратитесь в поддержку.",
            reply_markup=main_menu_keyboard()
        )


async def show_free_lesson_info(message: Message, user_service: UserService):
    """Показать информацию о бесплатном уроке"""
    free_lesson_text = """
🎁 <b>Ваш бесплатный AI-урок ждет!</b>

🎯 <b>Урок:</b> "Введение в искусственный интеллект"
⏱️ <b>Длительность:</b> 5 минут
📝 <b>Описание:</b> Узнайте, что такое ИИ, как он работает и какие возможности открывает для вашей карьеры

<i>Получите урок прямо сейчас!</i>
"""
    
    from keyboards.user import lesson_detail_keyboard
    
    # В реальном проекте здесь будет запрос к БД для получения бесплатного урока
    await message.answer(
        free_lesson_text,
        reply_markup=lesson_detail_keyboard(lesson_id=1, is_free=True)
    )


@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery, session: AsyncSession):
    """Показать главное меню"""
    try:
        user_service = UserService(session)
        await user_service.update_user_activity(callback.from_user.id)
        await user_service.log_user_activity(callback.from_user.id, "main_menu")
        
        main_menu_text = """
🏠 <b>Главное меню</b>

Выберите нужный раздел:
"""
        
        if callback.message:
            await callback.message.edit_text(
                main_menu_text,
                reply_markup=main_menu_keyboard()
            )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе главного меню: {e}")
        await callback.answer("Произошла ошибка")


@router.callback_query(F.data == "settings")
async def show_settings(callback: CallbackQuery, session: AsyncSession):
    """Показать настройки пользователя"""
    try:
        user_service = UserService(session)
        user = await user_service.get_user_by_telegram_id(callback.from_user.id)
        
        if not user:
            await callback.answer("Пользователь не найден")
            return
        
        await user_service.log_user_activity(callback.from_user.id, "settings")
        
        settings_text = f"""
⚙️ <b>Настройки</b>

👤 <b>Профиль:</b>
├ Имя: {user.full_name}
├ Username: @{user.username or 'не указан'}
├ Язык: {'🇷🇺 Русский' if user.language == 'ru' else '🇺🇸 English'}
└ Регистрация: {user.registration_date.strftime('%d.%m.%Y')}

💰 <b>Статистика:</b>
├ Потрачено звезд: {user.total_spent} ⭐
└ Последняя активность: {user.last_activity.strftime('%d.%m.%Y %H:%M')}
"""
        
        if callback.message:
            await callback.message.edit_text(
                settings_text,
                reply_markup=settings_keyboard(user.language)
            )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе настроек: {e}")
        await callback.answer("Произошла ошибка")


@router.callback_query(F.data == "support")
async def show_support(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Показать связь с поддержкой"""
    try:
        user_service = UserService(session)
        await user_service.update_user_activity(callback.from_user.id)
        
        await state.set_state(UserStates.contacting_support)
        
        support_text = """
📞 <b>Поддержка</b>

Опишите вашу проблему или вопрос, и мы постараемся помочь вам как можно скорее!

📝 <b>Напишите сообщение:</b>
<i>Опишите что произошло, какой у вас вопрос или проблема...</i>
"""
        
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Отмена", callback_data="main_menu")]
        ])
        
        if callback.message:
            await callback.message.edit_text(
                support_text,
                reply_markup=back_keyboard
            )
        await callback.answer("📞 Отправьте сообщение с вопросом")
        
    except Exception as e:
        logger.error(f"Ошибка при показе поддержки: {e}")
        await callback.answer("Произошла ошибка")


@router.message(UserStates.contacting_support)
async def handle_support_message(message: Message, session: AsyncSession, state: FSMContext, bot: Bot):
    """Обработка сообщения от пользователя в поддержку"""
    try:
        if not message.from_user:
            await message.answer("⚠️ Не удалось получить данные пользователя")
            return
            
        if not message.text:
            await message.answer("❗ Пожалуйста, отправьте текстовое сообщение")
            return
        
        # Получаем информацию о пользователе
        user_service = UserService(session)
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        
        # Создаем тикет поддержки
        from services.support import SupportService
        from services.notification import NotificationService
        
        support_service = SupportService(session)
        notification_service = NotificationService(bot, session)
        
        # Создаем тикет
        ticket = await support_service.create_support_ticket(
            user_id=message.from_user.id,
            message=message.text,
            priority="normal"
        )
        
        if not ticket:
            await message.answer(
                "❌ Произошла ошибка при создании обращения. Попробуйте позже.",
                reply_markup=main_menu_keyboard()
            )
            await state.clear()
            return
        
        # Отправляем уведомления админам
        try:
            await notification_service.notify_admins_of_support_request(ticket)
        except Exception as notify_error:
            logger.error(f"Ошибка при отправке уведомлений о тикете: {notify_error}")
            # Продолжаем выполнение, даже если уведомления не отправились
        
        # Отвечаем пользователю
        await message.answer(
            f"✅ <b>Ваше обращение принято!</b>\n\n"
            f"🎫 <b>Номер тикета:</b> #{ticket.ticket_number}\n"
            f"🔍 Мы рассмотрим ваш вопрос и обязательно свяжемся с вами!\n\n"
            f"🕰 Обычно мы отвечаем в течение нескольких часов.",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
        
        await state.clear()
        
        logger.info(f"Создан тикет поддержки #{ticket.ticket_number} от пользователя {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке обращения в поддержку: {e}")
        await message.answer(
            "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=main_menu_keyboard()
        )
        await state.clear()


@router.callback_query(F.data == "change_language")
async def show_language_selection(callback: CallbackQuery):
    """Показать выбор языка"""
    try:
        language_text = """
🌍 <b>Выбор языка</b>

Выберите предпочтительный язык интерфейса:
"""
        
        if callback.message:
            await callback.message.edit_text(
                language_text,
                reply_markup=language_keyboard()
            )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при выборе языка: {e}")
        await callback.answer("Произошла ошибка")


@router.callback_query(F.data.startswith("lang:"))
async def change_language(callback: CallbackQuery, session: AsyncSession):
    """Изменить язык пользователя"""
    try:
        if not callback.data:
            await callback.answer("Ошибка данных")
            return
            
        language = callback.data.split(":")[1]
        user_service = UserService(session)
        
        success = await user_service.update_user_language(callback.from_user.id, language)
        
        if success:
            # await user_service.log_user_activity(
            #     callback.from_user.id, 
            #     "language_changed", 
            #     extra_data=language
            # )  # ❌ Закомментировано для MVP - UserActivity не используется
            
            lang_name = "🇷🇺 Русский" if language == "ru" else "🇺🇸 English"
            success_text = f"✅ Язык изменен на {lang_name}"
            
            await callback.answer(success_text)
            
            # Показать обновленные настройки
            await show_settings(callback, session)
        else:
            await callback.answer("❌ Ошибка при изменении языка")
            
    except Exception as e:
        logger.error(f"Ошибка при изменении языка: {e}")
        await callback.answer("Произошла ошибка")



@router.message()
async def handle_unknown_message(message: Message, session: AsyncSession, state: FSMContext):
    """Обработчик неизвестных сообщений"""
    print(f"\n\n==== UNKNOWN MESSAGE HANDLER ====")
    print(f"message.content_type: {message.content_type}")
    print(f"message.from_user.id: {message.from_user.id if message.from_user else 'None'}")
    
    try:
        if not message.from_user:
            return
        
        # Проверяем, нет ли активного состояния FSM
        current_state = await state.get_state()
        print(f"Current FSM state: {current_state}")
        print(f"==================================\n")
        
        if current_state:
            # Если есть состояние, не обрабатываем сообщение
            logger.info(f"UNKNOWN MESSAGE HANDLER: Пропускаем сообщение в состоянии {current_state}")
            print(f"SKIPPING message due to FSM state: {current_state}")
            return
            
        user_service = UserService(session)
        await user_service.update_user_activity(message.from_user.id)
        
        unknown_text = """
🤔 Извините, я не понимаю это сообщение.

Используйте меню ниже для навигации по боту, или введите команду /start для перезапуска.
"""
        
        await message.answer(
            unknown_text,
            reply_markup=main_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке неизвестного сообщения: {e}")
        await message.answer("Произошла ошибка. Попробуйте /start")