"""
Клавиатуры для пользователей
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from typing import List, Optional

# Экспорт классов для использования в других модулях
__all__ = [
    'InlineKeyboardMarkup', 
    'InlineKeyboardButton', 
    'InlineKeyboardBuilder',
    'ReplyKeyboardMarkup', 
    'KeyboardButton',
    'main_menu_keyboard',
    'catalog_keyboard', 
    'dynamic_catalog_keyboard',
    'categories_list_keyboard',
    'lesson_detail_keyboard',
    'payment_keyboard',
    'my_purchases_keyboard',
    'settings_keyboard',
    'language_keyboard',
    'search_keyboard',
    'confirmation_keyboard',
    'lesson_list_keyboard',
    'profile_menu_keyboard',
    'lesson_controls_keyboard'
]


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню пользователя"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📚 Каталог уроков", callback_data="catalog"),
        InlineKeyboardButton(text="🎁 Бесплатный урок", callback_data="free_lesson")
    )
    builder.row(
        InlineKeyboardButton(text="👤 Мои покупки", callback_data="my_purchases")
        # InlineKeyboardButton(text="🔍 Поиск", callback_data="search")  # ❌ Закомментировано для MVP
    )
    builder.row(
        InlineKeyboardButton(text="📞 Поддержка", callback_data="support")
    )
    
    return builder.as_markup()


def catalog_keyboard(page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Клавиатура для каталога уроков (устаревшая)"""
    builder = InlineKeyboardBuilder()
    
    # Основные категории
    builder.row(
        InlineKeyboardButton(text="🎯 Все уроки", callback_data="catalog:all"),
        InlineKeyboardButton(text="📋 Категории", callback_data="catalog:categories")
    )
    
    # Кнопка назад
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    
    return builder.as_markup()


def lesson_detail_keyboard(lesson_id: int, is_purchased: bool = False, is_free: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура для детальной карточки урока"""
    builder = InlineKeyboardBuilder()
    
    if is_purchased:
        builder.row(InlineKeyboardButton(text="▶️ Открыть урок", callback_data=f"open_lesson:{lesson_id}"))
    elif is_free:
        builder.row(InlineKeyboardButton(text="🎁 Получить бесплатно", callback_data=f"get_free:{lesson_id}"))
    else:
        builder.row(InlineKeyboardButton(text="💳 Купить урок", callback_data=f"buy_lesson:{lesson_id}"))
    
    builder.row(
        InlineKeyboardButton(text="👀 Предпросмотр", callback_data=f"preview:{lesson_id}"),
        InlineKeyboardButton(text="📋 Подробнее", callback_data=f"info:{lesson_id}")
    )
    
    builder.row(
        InlineKeyboardButton(text="🔙 К каталогу", callback_data="catalog"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


def payment_keyboard(lesson_id: int, price_stars: int) -> InlineKeyboardMarkup:
    """Клавиатура для оплаты урока"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text=f"⭐ Оплатить {price_stars} звезд", 
            callback_data=f"pay:{lesson_id}:{price_stars}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"lesson:{lesson_id}")
    )
    
    return builder.as_markup()


def my_purchases_keyboard(page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Клавиатура для списка покупок пользователя"""
    builder = InlineKeyboardBuilder()
    
    # Фильтры
    builder.row(
        InlineKeyboardButton(text="📅 По дате", callback_data="purchases:date"),
        InlineKeyboardButton(text="📚 По урокам", callback_data="purchases:lessons")
    )
    
    # Навигация по страницам
    if total_pages > 1:
        nav_buttons = []
        
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"purchases_page:{page-1}"))
        
        nav_buttons.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="current_page"))
        
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"purchases_page:{page+1}"))
        
        builder.row(*nav_buttons)
    
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    
    return builder.as_markup()


def profile_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура главного меню профиля"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="👤 Мои покупки", callback_data="my_purchases"),
        InlineKeyboardButton(text="📚 Каталог", callback_data="catalog")
        # InlineKeyboardButton(text="📊 Статистика", callback_data="my_stats")  # ❌ Закомментировано для пользователей
    )
    builder.row(
        InlineKeyboardButton(text="🌍 Язык", callback_data="change_language"),
        InlineKeyboardButton(text="🔔 Уведомления", callback_data="notifications_settings")
    )
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    
    return builder.as_markup()


def lesson_controls_keyboard(lesson_id: int, has_access: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура для управления уроком"""
    builder = InlineKeyboardBuilder()
    
    if has_access:
        builder.row(InlineKeyboardButton(text="▶️ Смотреть урок", callback_data=f"watch_lesson:{lesson_id}"))
        builder.row(
            InlineKeyboardButton(text="📝 Описание", callback_data=f"lesson_info:{lesson_id}")
            # InlineKeyboardButton(text="📊 Статистика", callback_data=f"lesson_stats:{lesson_id}")  # ❌ Закомментировано для пользователей
        )
    
    builder.row(
        InlineKeyboardButton(text="👤 Мои покупки", callback_data="my_purchases"),
        InlineKeyboardButton(text="📚 Каталог", callback_data="catalog")
    )
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    
    return builder.as_markup()


def settings_keyboard(current_language: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура настроек пользователя"""
    builder = InlineKeyboardBuilder()
    
    # Выбор языка
    lang_text = "🇷🇺 Русский" if current_language == "ru" else "🇺🇸 English"
    builder.row(InlineKeyboardButton(text=f"🌍 Язык: {lang_text}", callback_data="change_language"))
    
    # Уведомления
    builder.row(InlineKeyboardButton(text="🔔 Уведомления", callback_data="notifications_settings"))
    
    # Профиль
    builder.row(InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile"))
    
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    
    return builder.as_markup()


def language_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇺🇸 English", callback_data="lang:en")
    )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="settings"))
    
    return builder.as_markup()


def search_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для поиска"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🔍 Поиск по названию", callback_data="search:title"),
        InlineKeyboardButton(text="🏷️ По категории", callback_data="search:category")
    )
    builder.row(
        InlineKeyboardButton(text="💰 По цене", callback_data="search:price"),
        InlineKeyboardButton(text="⭐ По рейтингу", callback_data="search:rating")
    )
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    
    return builder.as_markup()


def confirmation_keyboard(action: str, item_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    builder = InlineKeyboardBuilder()
    
    callback_data = f"confirm:{action}:{item_id}" if item_id else f"confirm:{action}"
    
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data=callback_data),
        InlineKeyboardButton(text="❌ Нет", callback_data="cancel")
    )
    
    return builder.as_markup()


def dynamic_catalog_keyboard(categories: List[dict], page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Клавиатура для каталога уроков с динамическими категориями"""
    builder = InlineKeyboardBuilder()
    
    # Основные категории
    builder.row(
        InlineKeyboardButton(text="🎯 Все уроки", callback_data="catalog:all"),
        InlineKeyboardButton(text="📋 Категории", callback_data="catalog:categories")
    )
    
    # Кнопка назад
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    
    return builder.as_markup()


def categories_list_keyboard(categories: List[dict]) -> InlineKeyboardMarkup:
    """Клавиатура со списком категорий"""
    builder = InlineKeyboardBuilder()
    
    # Динамические категории из базы данных
    if categories:
        # Группируем категории по 2 в ряд
        for i in range(0, len(categories), 2):
            row_categories = categories[i:i+2]
            
            if len(row_categories) == 2:
                builder.row(
                    InlineKeyboardButton(
                        text=f"📋 {row_categories[0]['name']} ({row_categories[0]['lesson_count']})",
                        callback_data=f"catalog:category:{row_categories[0]['id']}"
                    ),
                    InlineKeyboardButton(
                        text=f"📋 {row_categories[1]['name']} ({row_categories[1]['lesson_count']})",
                        callback_data=f"catalog:category:{row_categories[1]['id']}"
                    )
                )
            else:
                builder.row(
                    InlineKeyboardButton(
                        text=f"📋 {row_categories[0]['name']} ({row_categories[0]['lesson_count']})",
                        callback_data=f"catalog:category:{row_categories[0]['id']}"
                    )
                )
    else:
        builder.row(InlineKeyboardButton(text="📭 Категории пока нет", callback_data="no_action"))
    
    # Кнопка назад
    builder.row(InlineKeyboardButton(text="🔙 К каталогу", callback_data="catalog"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    
    return builder.as_markup()


def lesson_list_keyboard(lessons: List[dict], page: int = 0, items_per_page: int = 5) -> InlineKeyboardMarkup:
    """Клавиатура со списком уроков"""
    builder = InlineKeyboardBuilder()
    
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(lessons))
    
    for i in range(start_idx, end_idx):
        lesson = lessons[i]
        price_text = "🎁 Бесплатно" if lesson.get('is_free') else f"⭐ {lesson.get('price_stars', 0)} звезд"
        
        builder.row(InlineKeyboardButton(
            text=f"📚 {lesson.get('title', 'Урок')} - {price_text}",
            callback_data=f"lesson:{lesson.get('id')}"
        ))
    
    # Навигация
    total_pages = (len(lessons) + items_per_page - 1) // items_per_page
    if total_pages > 1:
        nav_buttons = []
        
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"lessons_page:{page-1}"))
        
        nav_buttons.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="current_page"))
        
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"lessons_page:{page+1}"))
        
        builder.row(*nav_buttons)
    
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    
    return builder.as_markup()