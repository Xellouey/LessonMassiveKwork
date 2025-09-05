"""
Обработчики личного кабинета пользователя
"""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.user import UserService
from services.lesson import LessonService
from keyboards.user import (
    profile_menu_keyboard, 
    lesson_controls_keyboard,
    main_menu_keyboard,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardBuilder
)
from states.user import UserStates

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "profile")
async def show_profile_menu(callback: CallbackQuery, session: AsyncSession):
    """Показать главное меню профиля"""
    try:
        user_service = UserService(session)
        user = await user_service.get_user_by_telegram_id(callback.from_user.id)
        
        if not user:
            await callback.answer("❌ Профиль пользователя не найден")
            return
        
        # Получение статистики пользователя
        lesson_service = LessonService(session)
        _, total_purchases = await lesson_service.get_user_purchases(
            callback.from_user.id, page=0, per_page=1
        )
        
        profile_text = f"""
👤 <b>Личный кабинет</b>

📋 <b>Информация о профиле:</b>
• Имя: {user.full_name}
• Username: @{user.username or 'не указан'}
• Дата регистрации: {user.registration_date.strftime('%d.%m.%Y')}
• Последняя активность: {user.last_activity.strftime('%d.%m.%Y %H:%M')}

📊 <b>Статистика:</b>
• Всего покупок: {total_purchases}
• Потрачено: ⭐ {user.total_spent} звезд
• Язык: {'🇷🇺 Русский' if user.language == 'ru' else '🇺🇸 English'}

Выберите раздел для управления:
"""
        
        await callback.message.edit_text(
            profile_text,
            reply_markup=profile_menu_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе профиля: {e}")
        await callback.answer("❌ Ошибка при загрузке профиля")


@router.callback_query(F.data == "my_purchases")
async def show_my_purchases(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Показать мои покупки с пагинацией"""
    try:
        await state.set_state(UserStates.viewing_purchases)
        await _show_purchases_page(callback, session, page=0)
        
    except Exception as e:
        logger.error(f"Ошибка при показе покупок: {e}")
        await callback.answer("❌ Ошибка при загрузке покупок")


@router.callback_query(F.data.startswith("my_purchases:"))
async def navigate_my_purchases(callback: CallbackQuery, session: AsyncSession):
    """Навигация по страницам покупок"""
    try:
        # Парсинг callback_data: my_purchases:page:number
        data_parts = callback.data.split(":")
        if len(data_parts) != 3 or data_parts[1] != "page":
            await callback.answer("❌ Некорректные данные навигации")
            return
        
        page = int(data_parts[2])
        await _show_purchases_page(callback, session, page)
        
    except ValueError:
        await callback.answer("❌ Некорректный номер страницы")
    except Exception as e:
        logger.error(f"Ошибка при навигации по покупкам: {e}")
        await callback.answer("❌ Ошибка при загрузке страницы")


async def _show_purchases_page(callback: CallbackQuery, session: AsyncSession, page: int):
    """Показать конкретную страницу покупок"""
    per_page = 5
    
    lesson_service = LessonService(session)
    purchases, total_purchases = await lesson_service.get_user_purchases(
        callback.from_user.id, 
        page=page, 
        per_page=per_page
    )
    
    if not purchases and page > 0:
        # Если страница пустая, показать первую
        purchases, total_purchases = await lesson_service.get_user_purchases(
            callback.from_user.id, 
            page=0, 
            per_page=per_page
        )
        page = 0
    
    # Вычисление общей информации
    total_pages = (total_purchases + per_page - 1) // per_page if total_purchases > 0 else 1
    
    if not purchases:
        purchases_text = """
👤 <b>Мои покупки</b>

📋 У вас пока нет покупок.

💡 <b>Рекомендуем:</b>
• Изучите наш каталог уроков
• Начните с бесплатного урока
• Выберите курс по вашим интересам
"""
        
        empty_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📚 Каталог уроков", callback_data="catalog")],
            [InlineKeyboardButton(text="🎁 Бесплатный урок", callback_data="get_free_lesson")],
            [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await callback.message.edit_text(
            purchases_text,
            reply_markup=empty_keyboard
        )
        return
    
    # Формирование текста со списком покупок
    purchases_text = f"""
👤 <b>Мои покупки</b>

📊 <b>Всего покупок:</b> {total_purchases}
📄 <b>Страница:</b> {page + 1} из {total_pages}

📚 <b>Ваши уроки:</b>
"""
    
    for i, purchase_data in enumerate(purchases, 1 + page * per_page):
        purchase = purchase_data['purchase']
        lesson = purchase_data['lesson']
        
        # Определение иконки по типу контента
        content_icons = {
            "video": "🎥",
            "photo": "📷", 
            "document": "📄",
            "audio": "🎵",
            "text": "📝"
        }
        content_icon = content_icons.get(lesson.content_type, "📚")
        
        # Статус возврата
        refund_status = ""
        if purchase.status == "refunded":
            refund_status = " ❌ <i>Возвращен</i>"
        
        purchases_text += f"""
{i}. {content_icon} <b>{lesson.title}</b>
   💰 {purchase.amount_stars} ⭐ • {purchase.purchase_date.strftime('%d.%m.%Y')}{refund_status}
   📝 {lesson.description[:50]}{'...' if len(lesson.description) > 50 else ''}
   
"""
    
    # Формирование клавиатуры с покупками и навигацией
    keyboard_builder = InlineKeyboardBuilder()
            
    # Добавляем кнопки для каждого урока
    for purchase_data in purchases:
        lesson = purchase_data['lesson']
        keyboard_builder.row(InlineKeyboardButton(
            text=f"▶️ {lesson.title[:30]}{'...' if len(lesson.title) > 30 else ''}",
            callback_data=f"open_lesson:{lesson.id}"
        ))
            
    # Навигация по страницам
    if total_pages > 1:
        nav_buttons = []
                
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"my_purchases:page:{page-1}"))
                
        nav_buttons.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="current_page"))
                
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"my_purchases:page:{page+1}"))
                
        keyboard_builder.row(*nav_buttons)
            
    keyboard_builder.row(
        InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
            
    keyboard = keyboard_builder.as_markup()
    
    await callback.message.edit_text(
        purchases_text,
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("open_lesson:"))
async def open_lesson_from_purchases(callback: CallbackQuery, session: AsyncSession):
    """Открыть урок из списка покупок"""
    try:
        # Парсинг callback_data: open_lesson:lesson_id
        lesson_id = int(callback.data.split(":")[1])
        
        # Проверка доступа к уроку
        lesson_service = LessonService(session)
        has_access = await lesson_service.check_user_has_lesson(callback.from_user.id, lesson_id)
        
        if not has_access:
            await callback.answer("❌ У вас нет доступа к этому уроку")
            return
        
        # Получение информации об уроке
        lesson = await lesson_service.get_lesson_by_id(lesson_id)
        if not lesson:
            await callback.answer("❌ Урок не найден")
            return
        
        # Показать детали урока с возможностью просмотра
        lesson_text = f"""
📚 <b>{lesson.title}</b>

📝 <b>Описание:</b>
{lesson.description}

📊 <b>Информация:</b>
• Тип контента: {lesson.content_type.upper()}
• Категория: {lesson.category or 'Общие'}
• Просмотры: {lesson.views_count}
"""
        
        if lesson.duration:
            minutes = lesson.duration // 60
            seconds = lesson.duration % 60
            lesson_text += f"• Длительность: {minutes:02d}:{seconds:02d}\n"
        
        lesson_text += f"\n✅ <b>У вас есть доступ к этому уроку!</b>"
        
        keyboard = lesson_controls_keyboard(lesson_id, has_access=True)
        
        await callback.message.edit_text(
            lesson_text,
            reply_markup=keyboard
        )
        await callback.answer("📚 Урок загружен")
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID урока")
    except Exception as e:
        logger.error(f"Ошибка при открытии урока: {e}")
        await callback.answer("❌ Ошибка при загрузке урока")


@router.callback_query(F.data.startswith("watch_lesson:"))
async def watch_lesson(callback: CallbackQuery, session: AsyncSession):
    """Просмотр урока (отправка медиа-контента)"""
    try:
        # Парсинг callback_data: watch_lesson:lesson_id
        lesson_id = int(callback.data.split(":")[1])
        
        lesson_service = LessonService(session)
        
        # Проверка доступа
        has_access = await lesson_service.check_user_has_lesson(callback.from_user.id, lesson_id)
        if not has_access:
            await callback.answer("❌ У вас нет доступа к этому уроку")
            return
        
        # Получение урока
        lesson = await lesson_service.get_lesson_by_id(lesson_id)
        if not lesson or not lesson.file_id:
            await callback.answer("❌ Контент урока недоступен")
            return
        
        # Увеличение счетчика просмотров и логирование
        await lesson_service.increment_lesson_views(lesson_id)
        
        user_service = UserService(session)
        await user_service.log_user_activity(
            callback.from_user.id,
            "lesson_viewed",
            lesson_id=lesson_id
        )
        
        # Отправка контента урока
        lesson_caption = f"""
📚 <b>{lesson.title}</b>

{lesson.description}

<i>Изучайте в своем темпе! Урок всегда доступен в разделе "Мои покупки".</i>
"""
        
        # Отправка медиа в зависимости от типа
        if lesson.content_type == "video":
            await callback.message.answer_video(
                video=lesson.file_id,
                caption=lesson_caption
            )
        elif lesson.content_type == "photo":
            await callback.message.answer_photo(
                photo=lesson.file_id,
                caption=lesson_caption
            )
        elif lesson.content_type == "document":
            await callback.message.answer_document(
                document=lesson.file_id,
                caption=lesson_caption
            )
        elif lesson.content_type == "audio":
            await callback.message.answer_audio(
                audio=lesson.file_id,
                caption=lesson_caption
            )
        else:
            # Для текстовых уроков или неизвестных типов
            await callback.message.answer(lesson_caption)
        
        await callback.answer("▶️ Урок воспроизводится")
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID урока")
    except Exception as e:
        logger.error(f"Ошибка при просмотре урока: {e}")
        await callback.answer("❌ Ошибка при воспроизведении урока")


@router.callback_query(F.data == "profile_settings")
async def show_profile_settings(callback: CallbackQuery, session: AsyncSession):
    """Показать настройки профиля"""
    try:
        user_service = UserService(session)
        user = await user_service.get_user_by_telegram_id(callback.from_user.id)
        
        if not user:
            await callback.answer("❌ Профиль не найден")
            return
        
        settings_text = f"""
⚙️ <b>Настройки профиля</b>

👤 <b>Текущие настройки:</b>
• Имя: {user.full_name}
• Username: @{user.username or 'не указан'}
• Язык: {'🇷🇺 Русский' if user.language == 'ru' else '🇺🇸 English'}
• Уведомления: {'✅ Включены' if user.is_active else '❌ Отключены'}

<i>Выберите настройку для изменения:</i>
"""
        
        settings_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌍 Изменить язык", callback_data="change_language")],
            [InlineKeyboardButton(text="🔔 Уведомления", callback_data="toggle_notifications")],
            [InlineKeyboardButton(text="🔙 Назад к профилю", callback_data="profile")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await callback.message.edit_text(
            settings_text,
            reply_markup=settings_keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе настроек профиля: {e}")
        await callback.answer("❌ Ошибка при загрузке настроек")


@router.callback_query(F.data == "change_language")
async def change_language(callback: CallbackQuery, session: AsyncSession):
    """Изменить язык интерфейса"""
    try:
        user_service = UserService(session)
        user = await user_service.get_user_by_telegram_id(callback.from_user.id)
        
        if not user:
            await callback.answer("❌ Профиль не найден")
            return
        
        current_lang = user.language
        new_lang = 'en' if current_lang == 'ru' else 'ru'
        
        # Обновление языка
        await user_service.update_user_language(callback.from_user.id, new_lang)
        
        # Текст подтверждения на новом языке
        if new_lang == 'ru':
            success_text = "✅ Язык изменен на русский"
        else:
            success_text = "✅ Language changed to English"
        
        await callback.answer(success_text)
        
        # Обновить профиль (так как теперь настройки в профиле)
        await show_profile_menu(callback, session)
        
    except Exception as e:
        logger.error(f"Ошибка при изменении языка: {e}")
        await callback.answer("❌ Ошибка при изменении языка")


@router.callback_query(F.data == "toggle_notifications")
async def toggle_notifications(callback: CallbackQuery, session: AsyncSession):
    """Переключить уведомления"""
    try:
        user_service = UserService(session)
        user = await user_service.get_user_by_telegram_id(callback.from_user.id)
        
        if not user:
            await callback.answer("❌ Профиль не найден")
            return
        
        new_status = not user.is_active
        await user_service.update_user_status(callback.from_user.id, new_status)
        
        status_text = "✅ Уведомления включены" if new_status else "❌ Уведомления отключены"
        await callback.answer(status_text)
        
        # Обновить профиль (так как теперь настройки в профиле)
        await show_profile_menu(callback, session)
        
    except Exception as e:
        logger.error(f"Ошибка при изменении уведомлений: {e}")
        await callback.answer("❌ Ошибка при изменении настроек")


@router.callback_query(F.data == "notifications_settings")
async def notifications_settings(callback: CallbackQuery, session: AsyncSession):
    """Настройки уведомлений - переключить состояние"""
    # Используем ту же логику что и toggle_notifications
    await toggle_notifications(callback, session)