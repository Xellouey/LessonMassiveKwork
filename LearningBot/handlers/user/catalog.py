"""
Обработчики каталога уроков с пагинацией и фильтрами
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from services.lesson import LessonService
from services.user import UserService
from keyboards.user import (
    catalog_keyboard, lesson_list_keyboard, lesson_detail_keyboard, 
    search_keyboard, main_menu_keyboard, categories_list_keyboard
)
from states.user import UserStates

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "catalog")
async def show_catalog(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Показать каталог уроков - с динамическими категориями"""
    try:
        await state.clear()
        
        lesson_service = LessonService(session)
        user_service = UserService(session)
        
        # Логирование активности
        await user_service.log_user_activity(callback.from_user.id, "view_catalog")
        
        # Получаем динамические категории
        from services.category import CategoryService
        category_service = CategoryService(session)
        categories_data = await category_service.get_categories_with_lesson_count()
        
        # Получаем общее количество уроков
        lessons, total_count = await lesson_service.get_lessons_paginated(page=0, per_page=1)
        
        catalog_text = f"""
📚 <b>Каталог уроков</b>

📊 <b>Всего уроков:</b> {total_count}
📋 <b>Категорий:</b> {len(categories_data)}

📋 Выберите категорию или посмотрите все уроки:
"""
        
        # Используем новую упрощенную клавиатуру
        from keyboards.user import dynamic_catalog_keyboard
        
        await callback.message.edit_text(
            catalog_text,
            reply_markup=dynamic_catalog_keyboard(categories_data)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе каталога: {e}")
        await callback.answer("Произошла ошибка при загрузке каталога")


@router.callback_query(F.data.startswith("catalog:"))
async def show_lessons_by_category(callback: CallbackQuery, session: AsyncSession):
    """Показать уроки по категории"""
    try:
        callback_parts = callback.data.split(":")
        
        lesson_service = LessonService(session)
        user_service = UserService(session)
        
        # Логирование активности
        await user_service.log_user_activity(
            callback.from_user.id, 
            "view_category", 
            extra_data=callback.data
        )
        
        # Обработка кнопки "Категории"
        if len(callback_parts) == 2 and callback_parts[1] == "categories":
            # Показать список всех категорий
            from services.category import CategoryService
            category_service = CategoryService(session)
            categories_data = await category_service.get_categories_with_lesson_count()
            
            categories_text = f"""
📋 <b>Категории уроков</b>

📈 <b>Всего категорий:</b> {len(categories_data)}

📋 Выберите категорию:
"""
            
            from keyboards.user import categories_list_keyboard
            await callback.message.edit_text(
                categories_text,
                reply_markup=categories_list_keyboard(categories_data)
            )
            await callback.answer()
            return
        
        # Определяем тип категории
        if len(callback_parts) == 3 and callback_parts[1] == "category":
            # Динамическая категория: catalog:category:id
            category_id = int(callback_parts[2])
            
            from services.category import CategoryService
            category_service = CategoryService(session)
            category = await category_service.get_category_by_id(category_id)
            
            if not category:
                await callback.answer("❌ Категория не найдена")
                return
            
            # Получаем уроки конкретной категории
            lessons, total_count = await lesson_service.get_lessons_by_category(
                category_id, 
                page=0, 
                per_page=10
            )
            category_name = category.name
            
        else:
            # Специальные категории
            category = callback_parts[1]
            
            if category == "all":
                lessons, total_count = await lesson_service.get_lessons_paginated(page=0, per_page=10)
                category_name = "Все уроки"
            else:
                # Неизвестная категория
                await callback.answer("❓ Неизвестная категория")
                return
        
        if not lessons:
            no_lessons_text = f"""
📚 <b>{category_name}</b>

😔 В этой категории пока нет уроков.

<i>Попробуйте другую категорию или вернитесь позже.</i>
"""
            
            # Возвращаемся к каталогу
            from keyboards.user import dynamic_catalog_keyboard
            from services.category import CategoryService
            
            category_service = CategoryService(session)
            categories_data = await category_service.get_categories_with_lesson_count()
            
            await callback.message.edit_text(
                no_lessons_text,
                reply_markup=dynamic_catalog_keyboard(categories_data)
            )
            await callback.answer()
            return
        
        # Показ списка уроков
        await show_lessons_list(callback, lessons, category_name, session)
        
    except Exception as e:
        logger.error(f"Ошибка при показе категории: {e}")
        await callback.answer("Произошла ошибка при загрузке категории")


async def show_lessons_list(callback: CallbackQuery, lessons: list, category_name: str, session: AsyncSession):
    """Показать список уроков"""
    try:
        lessons_text = f"📚 <b>{category_name}</b>\n\n"
        
        builder = InlineKeyboardBuilder()
        
        for i, lesson in enumerate(lessons[:10], 1):
            # Иконка в зависимости от типа контента
            content_icon = {
                'video': '🎥',
                'audio': '🎵', 
                'document': '📄',
                'photo': '📸'
            }.get(lesson.content_type, '📚')
            
            # Цена урока
            if lesson.is_free:
                price_text = "🎁 Бесплатно"
            else:
                from services.currency import CurrencyService
                price_text = f"💰 {CurrencyService.format_usd_price(lesson.price_usd)}"
            
            # Длительность
            duration_text = ""
            if lesson.duration:
                minutes = lesson.duration // 60
                if minutes > 0:
                    duration_text = f" • {minutes} мин"
            
            lesson_line = f"{i}. {content_icon} <b>{lesson.title}</b>\n"
            lesson_line += f"   💰 {price_text}{duration_text} • 👁 {lesson.views_count}\n"
            lesson_line += f"   <i>{lesson.description[:80]}...</i>\n\n"
            
            lessons_text += lesson_line
            
            # Кнопка для урока
            builder.row(InlineKeyboardButton(
                text=f"{i}. {lesson.title} - {price_text}",
                callback_data=f"lesson:{lesson.id}"
            ))
        
        # Навигация и фильтры - ❌ Поиск закомментирован для MVP
        # builder.row(
        #     InlineKeyboardButton(text="🔍 Поиск", callback_data="search"),
        #     InlineKeyboardButton(text="📊 Фильтры", callback_data="filters")
        # )
        
        builder.row(
            InlineKeyboardButton(text="🔙 К каталогу", callback_data="catalog"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        )
        
        await callback.message.edit_text(
            lessons_text,
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе списка уроков: {e}")
        await callback.answer("Произошла ошибка")


@router.callback_query(F.data.startswith("page:"))
async def show_page(callback: CallbackQuery, session: AsyncSession):
    """Показать определенную страницу каталога"""
    try:
        page = int(callback.data.split(":")[1])
        
        lesson_service = LessonService(session)
        user_service = UserService(session)
        
        # Логирование активности
        await user_service.log_user_activity(
            callback.from_user.id, 
            "catalog_page", 
            extra_data=str(page)
        )
        
        # Получение уроков для страницы
        lessons, total_count = await lesson_service.get_lessons_paginated(page=page, per_page=10)
        
        if not lessons:
            await callback.answer("На этой странице нет уроков")
            return
        
        await show_lessons_list(callback, lessons, f"Страница {page + 1}", session)
        
    except (ValueError, IndexError):
        await callback.answer("Некорректный номер страницы")
    except Exception as e:
        logger.error(f"Ошибка при переходе на страницу: {e}")
        await callback.answer("Произошла ошибка")


# ❌ Поиск закомментирован для MVP
# @router.callback_query(F.data == "search")
# async def show_search(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
#     """Показать меню поиска"""
#     try:
#         user_service = UserService(session)
#         await user_service.log_user_activity(callback.from_user.id, "search_menu")
#         
#         search_text = """
# 🔍 <b>Поиск уроков</b>
# 
# Выберите способ поиска:
# """
#         
#         await callback.message.edit_text(
#             search_text,
#             reply_markup=search_keyboard()
#         )
#         await callback.answer()
#         
#     except Exception as e:
#         logger.error(f"Ошибка при показе поиска: {e}")
#         await callback.answer("Произошла ошибка")


# ❌ Поиск закомментирован для MVP
# @router.callback_query(F.data.startswith("search:"))
# async def handle_search_type(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
#     """Обработка типа поиска"""
#     try:
#         search_type = callback.data.split(":")[1]
#         
#         user_service = UserService(session)
#         await user_service.log_user_activity(
#             callback.from_user.id, 
#             "search_type", 
#             extra_data=search_type
#         )
#         
#         if search_type == "title":
#             await state.set_state(UserStates.waiting_for_search)
#             
#             search_prompt_text = """
# 🔍 <b>Поиск по названию</b>
# 
# Введите название урока или ключевые слова для поиска:
# 
# <i>Например: "Python", "маркетинг", "дизайн"</i>
# """
#             
#             cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
#                 [InlineKeyboardButton(text="❌ Отмена", callback_data="catalog")]
#             ])
#             
#             await callback.message.edit_text(
#                 search_prompt_text,
#                 reply_markup=cancel_keyboard
#             )
#             
#         elif search_type == "category":
#             await show_categories_list(callback, session)
#             
#         elif search_type == "price":
#             await show_price_filters(callback, session)
#             
#         elif search_type == "rating":
#             await show_rating_filters(callback, session)
#         
#         await callback.answer()
#         
#     except Exception as e:
#         logger.error(f"Ошибка при обработке типа поиска: {e}")
#         await callback.answer("Произошла ошибка")


# ❌ Поиск закомментирован для MVP
# @router.message(UserStates.waiting_for_search)
# async def process_search_query(message: Message, session: AsyncSession, state: FSMContext):
#     """Обработка поискового запроса"""
#     try:
#         query = message.text.strip()
#         
#         if len(query) < 2:
#             await message.answer(
#                 "❌ Запрос должен содержать минимум 2 символа. Попробуйте еще раз:"
#             )
#             return
#         
#         await state.clear()
#         
#         lesson_service = LessonService(session)
#         user_service = UserService(session)
#         
#         # Логирование поиска
#         await user_service.log_user_activity(
#             message.from_user.id, 
#             "search_query", 
#             extra_data=query
#         )
#         
#         # Поиск уроков
#         lessons, total_count = await lesson_service.search_lessons(query, page=0, per_page=10)
#         
#         if not lessons:
#             no_results_text = f"""
# 🔍 <b>Результаты поиска: "{query}"</b>
# 
# 😔 По вашему запросу ничего не найдено.
# 
# <i>Попробуйте:</i>
# • Изменить ключевые слова
# • Проверить правописание  
# • Использовать более общие термины
# """
#             
#             no_results_keyboard = InlineKeyboardMarkup(inline_keyboard=[
#                 [InlineKeyboardButton(text="🔍 Новый поиск", callback_data="search")],
#                 [InlineKeyboardButton(text="📚 К каталогу", callback_data="catalog")],
#                 [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
#             ])
#             
#             await message.answer(
#                 no_results_text,
#                 reply_markup=no_results_keyboard
#             )
#             return
#         
#         # Показ результатов поиска
#         results_text = f"""
# 🔍 <b>Результаты поиска: "{query}"</b>
# 
# 📊 Найдено уроков: {total_count}
# """
#         
#         await message.answer(results_text)
#         
#         # Создание callback query для показа списка
#         fake_callback = type('CallbackQuery', (), {
#             'message': message,
#             'answer': lambda text="": None,
#             'from_user': message.from_user
#         })()
#         
#         await show_lessons_list(fake_callback, lessons, f"Поиск: {query}", session)
#         
#     except Exception as e:
#         logger.error(f"Ошибка при обработке поискового запроса: {e}")
#         await message.answer(
#             "😔 Произошла ошибка при поиске. Попробуйте еще раз.",
#             reply_markup=search_keyboard()
#         )


# ❌ Функции поиска и фильтров закомментированы для MVP
