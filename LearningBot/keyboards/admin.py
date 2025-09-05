"""
Клавиатуры для административной панели
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional
from database.models import Lesson, User


def admin_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню административной панели - упрощенная версия"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="📚 Управление уроками", callback_data="admin_lessons"),
        # InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")  # Закомментировано - избыточно
    )
    keyboard.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton(text="📢 Рассылки", callback_data="admin_broadcasts")
    )
    keyboard.row(
        InlineKeyboardButton(text="📋 Категории", callback_data="admin_categories_list"),
        InlineKeyboardButton(text="🎫 Поддержка", callback_data="admin_support")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Выйти из админки", callback_data="main_menu")
    )
    
    return keyboard.as_markup()


def lessons_management_keyboard() -> InlineKeyboardMarkup:
    """Меню управления уроками - упрощенное"""
    keyboard = InlineKeyboardBuilder()
    
    # Только основные функции, которые работают
    keyboard.row(
        InlineKeyboardButton(text="➕ Создать урок", callback_data="admin_create_lesson"),
        InlineKeyboardButton(text="📋 Список уроков", callback_data="admin_lessons_list")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")
    )
    
    return keyboard.as_markup()


def bulk_operations_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для массовых операций с уроками"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="✅ Активировать все", callback_data="bulk_activate_all"),
        InlineKeyboardButton(text="❌ Деактивировать все", callback_data="bulk_deactivate_all")
    )
    keyboard.row(
        InlineKeyboardButton(text="🎁 Сделать все бесплатными", callback_data="bulk_make_free")
    )
    keyboard.row(
        InlineKeyboardButton(text="🗑️ Массовое мягкое удаление", callback_data="bulk_soft_delete")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_lessons")
    )
    
    return keyboard.as_markup()


def lesson_edit_keyboard(lesson_id: int) -> InlineKeyboardMarkup:
    """Клавиатура редактирования конкретного урока"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="✏️ Название", callback_data=f"edit_lesson_title:{lesson_id}"),
        InlineKeyboardButton(text="📝 Описание", callback_data=f"edit_lesson_description:{lesson_id}")
    )
    keyboard.row(
        InlineKeyboardButton(text="💰 Цена", callback_data=f"edit_lesson_price:{lesson_id}"),
        InlineKeyboardButton(text="🎬 Фото/Видео", callback_data=f"edit_lesson_media:{lesson_id}")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔄 Статус", callback_data=f"toggle_lesson_status:{lesson_id}"),
        InlineKeyboardButton(text="🎁 Бесплатный", callback_data=f"toggle_lesson_free:{lesson_id}")
    )
    keyboard.row(
        InlineKeyboardButton(text="🗑️ Удалить урок", callback_data=f"delete_lesson:{lesson_id}")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 К списку уроков", callback_data="admin_lessons_list")
    )
    
    return keyboard.as_markup()


def lessons_list_keyboard(lessons: List[Lesson], page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    """Клавиатура со списком уроков для администрирования"""
    keyboard = InlineKeyboardBuilder()
    
    # Добавляем кнопки для каждого урока
    for lesson in lessons:
        status_icon = "✅" if lesson.is_active else "❌"
        free_icon = "🎁" if lesson.is_free else "💰"
        
        lesson_text = f"{status_icon}{free_icon} {lesson.title[:25]}{'...' if len(lesson.title) > 25 else ''}"
        
        keyboard.row(
            InlineKeyboardButton(text=lesson_text, callback_data=f"admin_edit_lesson:{lesson.id}")
        )
    
    # Навигация по страницам
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_lessons_page:{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"📄 {page + 1}", callback_data="current_page"))
    
    # Предполагаем, что есть следующая страница (это нужно проверять отдельно)
    nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_lessons_page:{page+1}"))
    
    if nav_buttons:
        keyboard.row(*nav_buttons)
    
    keyboard.row(
        InlineKeyboardButton(text="➕ Новый урок", callback_data="admin_create_lesson"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_lessons")
    )
    
    return keyboard.as_markup()


def users_management_keyboard() -> InlineKeyboardMarkup:
    """Меню управления пользователями"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="👥 Все пользователи", callback_data="admin_users_list"),
        InlineKeyboardButton(text="🔍 Поиск пользователя", callback_data="admin_user_search")
    )
    keyboard.row(
        InlineKeyboardButton(text="🚫 Заблокированные", callback_data="admin_blocked_users"),
        InlineKeyboardButton(text="⭐ Активные покупатели", callback_data="admin_active_buyers")
    )
    keyboard.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_user_stats"),
        InlineKeyboardButton(text="👑 Администраторы", callback_data="admin_admins_list")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")
    )
    
    return keyboard.as_markup()


def user_details_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для действий с конкретным пользователем"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data=f"admin_user_stats:{user_id}"),
        InlineKeyboardButton(text="🛒 Покупки", callback_data=f"admin_user_purchases:{user_id}")
    )
    keyboard.row(
        InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"admin_block_user:{user_id}"),
        InlineKeyboardButton(text="✅ Разблокировать", callback_data=f"admin_unblock_user:{user_id}")
    )
    keyboard.row(
        InlineKeyboardButton(text="📨 Отправить сообщение", callback_data=f"admin_message_user:{user_id}"),
        InlineKeyboardButton(text="💳 История платежей", callback_data=f"admin_user_payments:{user_id}")
    )
    keyboard.row(
        InlineKeyboardButton(text="👑 Сделать админом", callback_data=f"admin_promote_user:{user_id}"),
        InlineKeyboardButton(text="🗑️ Удалить пользователя", callback_data=f"admin_delete_user:{user_id}")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 К списку", callback_data="admin_users_list")
    )
    
    return keyboard.as_markup()


def admin_stats_keyboard() -> InlineKeyboardMarkup:
    """Меню статистики"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="📈 Общая статистика", callback_data="admin_general_stats"),
        InlineKeyboardButton(text="💰 Доходы", callback_data="admin_revenue_stats")
    )
    keyboard.row(
        # InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users_stats"),  # Закомментировано по запросу
        InlineKeyboardButton(text="📚 Уроки", callback_data="admin_lessons_statistics")
    )
    keyboard.row(
        InlineKeyboardButton(text="📅 За период", callback_data="admin_period_stats"),
        InlineKeyboardButton(text="📊 Топ уроки", callback_data="admin_top_lessons")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")
    )
    
    return keyboard.as_markup()


def broadcasts_keyboard() -> InlineKeyboardMarkup:
    """Меню рассылок"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="📢 Новая рассылка", callback_data="admin_new_broadcast")
    )
    # Removed buttons per user request:
    # - 📋 История рассылок (admin_broadcasts_history)
    # - 👥 Рассылка всем (admin_broadcast_all) 
    # - ⭐ Рассылка покупателям (admin_broadcast_buyers)
    # - ⏸️ Активные рассылки (admin_active_broadcasts)
    # - 📊 Статистика рассылок (admin_broadcast_stats)
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")
    )
    
    return keyboard.as_markup()


def admin_settings_keyboard() -> InlineKeyboardMarkup:
    """Меню настроек администрирования - упрощенная версия"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="📝 Тексты интерфейса", callback_data="admin_texts"),
        # InlineKeyboardButton(text="🎥 Медиа файлы", callback_data="admin_media")  # Закомментировано - не основной функционал
    )
    keyboard.row(
        InlineKeyboardButton(text="🤖 Настройки бота", callback_data="admin_bot_settings"),
        InlineKeyboardButton(text="💳 Настройки оплаты", callback_data="admin_payment_settings")
    )
    keyboard.row(
        InlineKeyboardButton(text="👑 Управление админами", callback_data="admin_manage_admins"),
        InlineKeyboardButton(text="🔄 Очистить кеш", callback_data="admin_clear_cache")
    )
    keyboard.row(
        InlineKeyboardButton(text="📊 Системная информация", callback_data="admin_system_info"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")
    )
    
    return keyboard.as_markup()


def confirm_action_keyboard(action: str, item_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    keyboard = InlineKeyboardBuilder()
    
    callback_data = f"admin_confirm:{action}:{item_id}" if item_id else f"admin_confirm:{action}"
    
    keyboard.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=callback_data),
        InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")
    )
    
    return keyboard.as_markup()


def confirm_lesson_delete_keyboard(lesson_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления урока"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_lesson:{lesson_id}"),
        InlineKeyboardButton(text="❌ Нет, отмена", callback_data=f"admin_edit_lesson:{lesson_id}")
    )
    
    return keyboard.as_markup()


def lesson_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа контента урока"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="🎥 Видео", callback_data="lesson_type:video"),
        InlineKeyboardButton(text="📷 Фото", callback_data="lesson_type:photo")
    )
    keyboard.row(
        InlineKeyboardButton(text="📝 Текст", callback_data="lesson_type:text")
    )
    keyboard.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="admin_lessons")
    )
    
    return keyboard.as_markup()


def media_update_type_keyboard(lesson_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора типа медиа для обновления"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="🎥 Обновить видео", callback_data=f"update_media_video:{lesson_id}"),
        InlineKeyboardButton(text="📷 Обновить фото", callback_data=f"update_media_photo:{lesson_id}")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_edit_lesson:{lesson_id}")
    )
    
    return keyboard.as_markup()


def simple_confirmation_keyboard(action_data: str, cancel_data: str = "admin_lessons_list") -> InlineKeyboardMarkup:
    """Простая клавиатура подтверждения действия"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="✅ Да, я уверен", callback_data=action_data),
        InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_data)
    )
    
    return keyboard.as_markup()


def back_to_admin_keyboard() -> InlineKeyboardMarkup:
    """Простая клавиатура возврата в админ меню"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="🔙 В админ меню", callback_data="admin_menu"))
    return keyboard.as_markup()


def broadcast_audience_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора аудитории для рассылки"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="👥 Всем пользователям", callback_data="broadcast_audience:all"),
        InlineKeyboardButton(text="✅ Активным пользователям", callback_data="broadcast_audience:active")
    )
    keyboard.row(
        InlineKeyboardButton(text="⭐ Покупателям", callback_data="broadcast_audience:buyers")
    )
    keyboard.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="admin_broadcasts")
    )
    
    return keyboard.as_markup()


def broadcast_confirm_keyboard(broadcast_id: int, audience: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения отправки рассылки"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="✅ Отправить", callback_data=f"confirm_broadcast:{broadcast_id}:{audience}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="admin_broadcasts")
    )
    
    return keyboard.as_markup()


def broadcast_media_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для загрузки медиа в рассылку"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="⏭️ Пропустить медиа", callback_data="skip_broadcast_media")
    )
    keyboard.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="admin_broadcasts")
    )
    
    return keyboard.as_markup()


def broadcast_history_keyboard(broadcasts: List, page: int = 0) -> InlineKeyboardMarkup:
    """Клавиатура для истории рассылок"""
    keyboard = InlineKeyboardBuilder()
    
    # Добавляем рассылки
    for broadcast in broadcasts:
        status_icon = {
            "pending": "⏳",
            "sending": "📤", 
            "completed": "✅",
            "failed": "❌",
            "cancelled": "🚫"
        }.get(broadcast.status, "❓")
        
        text = f"{status_icon} {broadcast.text[:30]}{'...' if len(broadcast.text) > 30 else ''}"
        keyboard.row(
            InlineKeyboardButton(text=text, callback_data=f"broadcast_stats:{broadcast.id}")
        )
    
    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"broadcasts_page:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"broadcasts_page:{page+1}"))
    
    if nav_buttons:
        keyboard.row(*nav_buttons)
    
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_broadcasts")
    )
    
    return keyboard.as_markup()


def broadcast_actions_keyboard(broadcast_id: int, status: str) -> InlineKeyboardMarkup:
    """Клавиатура действий с рассылкой"""
    keyboard = InlineKeyboardBuilder()
    
    # Действия в зависимости от статуса
    if status == "pending":
        keyboard.row(
            InlineKeyboardButton(text="📤 Отправить", callback_data=f"send_broadcast:{broadcast_id}"),
            InlineKeyboardButton(text="🚫 Отменить", callback_data=f"cancel_broadcast:{broadcast_id}")
        )
    
    keyboard.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data=f"broadcast_stats:{broadcast_id}"),
        InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_broadcast:{broadcast_id}")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 К истории", callback_data="admin_broadcasts_history")
    )
    
    return keyboard.as_markup()


def text_categories_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура категорий текстов"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="💬 Сообщения", callback_data="text_category:messages"),
        InlineKeyboardButton(text="🔘 Кнопки", callback_data="text_category:buttons")
    )
    keyboard.row(
        InlineKeyboardButton(text="❌ Ошибки", callback_data="text_category:errors"),
        InlineKeyboardButton(text="✅ Успех", callback_data="text_category:success")
    )
    keyboard.row(
        InlineKeyboardButton(text="📄 Описания", callback_data="text_category:descriptions")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔍 Поиск", callback_data="admin_text_search"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_text_stats")
    )
    keyboard.row(
        InlineKeyboardButton(text="➕ Создать текст", callback_data="admin_text_create"),
        InlineKeyboardButton(text="📤 Экспорт", callback_data="admin_text_export")
    )
    keyboard.row(
        InlineKeyboardButton(text="🎆 Инициализация", callback_data="admin_text_init"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")
    )
    
    return keyboard.as_markup()


def text_settings_keyboard(texts: List, category: str, page: int = 0) -> InlineKeyboardMarkup:
    """Клавиатура со списком текстов категории"""
    keyboard = InlineKeyboardBuilder()
    
    # Добавляем тексты
    for text in texts[:10]:  # Показываем первые 10
        translation_icon = "🌐" if text.value_en else "🇷🇺"
        text_preview = f"{translation_icon} {text.key[:25]}{'...' if len(text.key) > 25 else ''}"
        
        keyboard.row(
            InlineKeyboardButton(text=text_preview, callback_data=f"edit_text:{text.key}")
        )
    
    # Навигация по страницам
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"texts_page:{category}:{page-1}"))
    
    if len(texts) > 10:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"texts_page:{category}:{page+1}"))
    
    if nav_buttons:
        keyboard.row(*nav_buttons)
    
    keyboard.row(
        InlineKeyboardButton(text="➕ Новый текст", callback_data="admin_text_create"),
        InlineKeyboardButton(text="🔙 К категориям", callback_data="admin_texts")
    )
    
    return keyboard.as_markup()


def text_actions_keyboard(text_key: str) -> InlineKeyboardMarkup:
    """Клавиатура действий с текстом"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="🇷🇺 Ред. русский", callback_data=f"edit_text_lang:{text_key}:ru"),
        InlineKeyboardButton(text="🇬🇧 Ред. английский", callback_data=f"edit_text_lang:{text_key}:en")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔍 Просмотреть", callback_data=f"preview_text:{text_key}"),
        InlineKeyboardButton(text="📋 Копировать", callback_data=f"copy_text:{text_key}")
    )
    keyboard.row(
        InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_text:{text_key}"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_texts")
    )
    
    return keyboard.as_markup()


def text_language_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка для редактирования"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="edit_lang:ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="edit_lang:en")
    )
    keyboard.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="admin_texts")
    )
    
    return keyboard.as_markup()


def text_search_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура поиска текстов"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="🔑 По ключу", callback_data="text_search:key"),
        InlineKeyboardButton(text="💬 По содержанию", callback_data="text_search:content")
    )
    keyboard.row(
        InlineKeyboardButton(text="📂 По категории", callback_data="text_search:category"),
        InlineKeyboardButton(text="📝 По описанию", callback_data="text_search:description")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_texts")
    )
    
    return keyboard.as_markup()


def media_management_keyboard() -> InlineKeyboardMarkup:
    """Меню управления медиа"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="🎥 Видео", callback_data="media_type:video"),
        InlineKeyboardButton(text="🖼️ Фото", callback_data="media_type:photo")
    )
    keyboard.row(
        InlineKeyboardButton(text="📄 Документы", callback_data="media_type:document"),
        InlineKeyboardButton(text="🎧 Аудио", callback_data="media_type:audio")
    )
    keyboard.row(
        InlineKeyboardButton(text="📄 Загрузить", callback_data="media_upload"),
        InlineKeyboardButton(text="🔍 Поиск", callback_data="media_search")
    )
    keyboard.row(
        InlineKeyboardButton(text="📈 Статистика", callback_data="media_statistics"),
        InlineKeyboardButton(text="📈 Аналитика", callback_data="media_analytics")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔧 Оптимизация", callback_data="media_optimize"),
        InlineKeyboardButton(text="💾 Бэкап", callback_data="media_backup")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")
    )
    
    return keyboard.as_markup()


def media_types_keyboard(selected_type: Optional[str] = None) -> InlineKeyboardMarkup:
    """Клавиатура типов медиа"""
    keyboard = InlineKeyboardBuilder()
    
    if selected_type:
        # Показываем действия для конкретного типа
        keyboard.row(
            InlineKeyboardButton(text="📄 Загрузить", callback_data=f"upload_type:{selected_type}"),
            InlineKeyboardButton(text="🔍 Поиск", callback_data="media_search")
        )
        keyboard.row(
            InlineKeyboardButton(text="📈 Статистика", callback_data="media_statistics")
        )
    else:
        # Обычные типы для выбора
        keyboard.row(
            InlineKeyboardButton(text="🎥 Видео", callback_data="upload_type:video"),
            InlineKeyboardButton(text="🖼️ Фото", callback_data="upload_type:photo")
        )
        keyboard.row(
            InlineKeyboardButton(text="📄 Документ", callback_data="upload_type:document"),
            InlineKeyboardButton(text="🎧 Аудио", callback_data="upload_type:audio")
        )
    
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_media")
    )
    
    return keyboard.as_markup()


def media_actions_keyboard(media_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий с медиа"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="👁️ Просмотреть", callback_data=f"view_media:{media_id}"),
        InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_media:{media_id}")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔄 Заменить", callback_data=f"replace_media:{media_id}"),
        InlineKeyboardButton(text="📊 Статистика", callback_data=f"media_stats:{media_id}")
    )
    keyboard.row(
        InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_media:{media_id}"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_media")
    )
    
    return keyboard.as_markup()


def media_categories_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура категорий медиа"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="🎬 Уроки", callback_data="media_category:lessons"),
        InlineKeyboardButton(text="🎓 Курсы", callback_data="media_category:courses")
    )
    keyboard.row(
        InlineKeyboardButton(text="📢 Промо", callback_data="media_category:promo"),
        InlineKeyboardButton(text="📁 Прочее", callback_data="media_category:other")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_media")
    )
    
    return keyboard.as_markup()


# ============= КЛАВИАТУРЫ ДЛЯ СИСТЕМЫ ВЫВОДА СРЕДСТВ =============

def withdrawal_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню управления выводом средств"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="💰 Баланс", callback_data="withdrawal_balance"),
        InlineKeyboardButton(text="💸 Новый запрос", callback_data="withdrawal_create")
    )
    keyboard.row(
        InlineKeyboardButton(text="📋 Мои запросы", callback_data="withdrawal_my_requests")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")
    )
    
    return keyboard.as_markup()


def withdrawal_confirm_keyboard(amount: int, commission: int, net_amount: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения запроса на вывод"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="withdrawal_confirm_yes"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="withdrawal_confirm_no")
    )
    keyboard.row(
        InlineKeyboardButton(text="✏️ Изменить сумму", callback_data="withdrawal_edit_amount"),
        InlineKeyboardButton(text="📝 Изменить кошелек", callback_data="withdrawal_edit_wallet")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="withdrawal_menu")
    )
    
    return keyboard.as_markup()


def withdrawal_requests_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    """Клавиатура для навигации по запросам на вывод"""
    keyboard = InlineKeyboardBuilder()
    
    # Фильтры по статусу
    keyboard.row(
        InlineKeyboardButton(text="⏳ Ожидающие", callback_data="withdrawal_filter:pending"),
        InlineKeyboardButton(text="🔄 В обработке", callback_data="withdrawal_filter:processing")
    )
    keyboard.row(
        InlineKeyboardButton(text="✅ Завершенные", callback_data="withdrawal_filter:completed"),
        InlineKeyboardButton(text="❌ Отклоненные", callback_data="withdrawal_filter:failed")
    )
    keyboard.row(
        InlineKeyboardButton(text="🚫 Отмененные", callback_data="withdrawal_filter:cancelled"),
        InlineKeyboardButton(text="📋 Все", callback_data="withdrawal_filter:all")
    )
    
    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"withdrawal_page:{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"📄 {page + 1}", callback_data="current_page"))
    nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"withdrawal_page:{page+1}"))
    
    keyboard.row(*nav_buttons)
    
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="withdrawal_menu")
    )
    
    return keyboard.as_markup()


def withdrawal_details_keyboard(request_id: int, status: str, can_cancel: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для действий с конкретным запросом на вывод"""
    keyboard = InlineKeyboardBuilder()
    
    if status == 'pending' and can_cancel:
        keyboard.row(
            InlineKeyboardButton(text="🚫 Отменить запрос", callback_data=f"withdrawal_cancel:{request_id}")
        )
    
    if status in ['failed', 'cancelled']:
        keyboard.row(
            InlineKeyboardButton(text="🔄 Создать новый", callback_data="withdrawal_create")
        )
    
    keyboard.row(
        InlineKeyboardButton(text="📋 К списку", callback_data="withdrawal_my_requests"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="withdrawal_menu")
    )
    
    return keyboard.as_markup()


def withdrawal_cancel_confirm_keyboard(request_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения отмены запроса"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="✅ Да, отменить", callback_data=f"withdrawal_cancel_confirm:{request_id}"),
        InlineKeyboardButton(text="❌ Нет, оставить", callback_data=f"withdrawal_details:{request_id}")
    )
    
    return keyboard.as_markup()


def withdrawal_management_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления запросами (для суперадминов)"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="⏳ Ожидающие обработки", callback_data="admin_withdrawal_pending"),
        InlineKeyboardButton(text="🔄 В процессе", callback_data="admin_withdrawal_processing")
    )
    keyboard.row(
        InlineKeyboardButton(text="📊 Статистика выводов", callback_data="admin_withdrawal_stats"),
        InlineKeyboardButton(text="💰 Общий баланс", callback_data="admin_withdrawal_balance")
    )
    keyboard.row(
        InlineKeyboardButton(text="⚙️ Настройки комиссий", callback_data="admin_withdrawal_settings"),
        InlineKeyboardButton(text="📋 Все запросы", callback_data="admin_withdrawal_all")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")
    )
    
    return keyboard.as_markup()


def admin_withdrawal_action_keyboard(request_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий администратора с запросом на вывод"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="✅ Одобрить", callback_data=f"admin_withdrawal_approve:{request_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_withdrawal_reject:{request_id}")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔄 В обработку", callback_data=f"admin_withdrawal_process:{request_id}"),
        InlineKeyboardButton(text="💳 Добавить транзакцию", callback_data=f"admin_withdrawal_transaction:{request_id}")
    )
    keyboard.row(
        InlineKeyboardButton(text="📋 К списку", callback_data="admin_withdrawal_pending"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_withdrawal_management")
    )
    
    return keyboard.as_markup()


# =========================
# КЛАВИАТУРЫ ДЛЯ КАТЕГОРИЙ
# =========================

def categories_list_keyboard(categories_data: List[dict], page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    """Клавиатура со списком категорий для администрирования"""
    keyboard = InlineKeyboardBuilder()
    
    # Добавляем кнопки для каждой категории
    for category in categories_data:
        status_icon = "✅" if category['is_active'] else "❌"
        lesson_count = category['lesson_count']
        
        category_text = f"{status_icon} {category['name'][:20]}{'...' if len(category['name']) > 20 else ''} ({lesson_count})"
        
        keyboard.row(
            InlineKeyboardButton(text=category_text, callback_data=f"admin_edit_category:{category['id']}")
        )
    
    # Навигация и кнопки управления
    keyboard.row(
        InlineKeyboardButton(text="➕ Новая категория", callback_data="admin_create_category")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")
    )
    
    return keyboard.as_markup()


def category_edit_keyboard(category_id: int) -> InlineKeyboardMarkup:
    """Клавиатура редактирования конкретной категории"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="✏️ Название", callback_data=f"edit_category_name:{category_id}")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔄 Статус", callback_data=f"toggle_category_status:{category_id}"),
        InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_category:{category_id}")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 К списку категорий", callback_data="admin_categories_list")
    )
    
    return keyboard.as_markup()