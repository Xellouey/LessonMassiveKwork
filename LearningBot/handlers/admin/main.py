"""
Основные обработчики административной панели
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.admin import AdminService
from services.user import UserService
from services.lesson import LessonService
from keyboards.admin import (
    admin_main_menu_keyboard,
    lessons_management_keyboard,
    # users_management_keyboard,  # Закомментировано - не используется
    admin_stats_keyboard,
    broadcasts_keyboard
)
from states.admin import AdminStates
from middlewares.admin import AdminOnlyMiddleware

logger = logging.getLogger(__name__)

# Создаем роутер только для администраторов
router = Router()
router.message.middleware(AdminOnlyMiddleware())
router.callback_query.middleware(AdminOnlyMiddleware())


@router.message(Command("admin"))
async def admin_command(message: Message, session: AsyncSession, admin):
    """Команда входа в административную панель"""
    try:
        if not admin:
            await message.answer("❌ У вас нет прав администратора.")
            return
        
        admin_text = f"""
🔧 <b>Административная панель</b>

👋 Добро пожаловать, <b>{admin.username or 'Администратор'}</b>!

🎛️ <b>Доступные функции:</b>
• Управление уроками и контентом
• Просмотр статистики и аналитики  
• Управление пользователями
• Настройки системы и рассылки

📊 <b>Ваши права:</b> {admin.permissions}

Выберите нужный раздел:
"""
        
        await message.answer(
            admin_text,
            reply_markup=admin_main_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка при открытии админ панели: {e}")
        await message.answer("❌ Ошибка при доступе к административной панели.")


@router.callback_query(F.data == "admin_menu")
async def show_admin_menu(callback: CallbackQuery, session: AsyncSession, admin):
    """Показать главное меню администратора"""
    try:
        admin_text = f"""
🔧 <b>Административная панель</b>

👋 <b>{admin.username or 'Администратор'}</b>

🎛️ Выберите нужный раздел для работы:
"""
        
        await callback.message.edit_text(
            admin_text,
            reply_markup=admin_main_menu_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе админ меню: {e}")
        await callback.answer("❌ Ошибка при загрузке меню.")


@router.callback_query(F.data == "admin_lessons")
async def show_lessons_menu(callback: CallbackQuery, session: AsyncSession):
    """Меню управления уроками"""
    try:
        lesson_service = LessonService(session)
        
        # Получаем общую статистику уроков
        all_lessons, total_lessons = await lesson_service.get_lessons_paginated(
            page=0, 
            per_page=1000,  # Получаем все уроки для подсчета статистики
            include_inactive=True
        )
        
        # Подсчитываем активные и неактивные уроки
        active_lessons = len([l for l in all_lessons if l.is_active]) if all_lessons else 0
        inactive_lessons = total_lessons - active_lessons
        
        lessons_text = f"""
📚 <b>Управление уроками</b>

📊 <b>Статистика:</b>
• Всего уроков: {total_lessons}
• Активных: {active_lessons}
• Неактивных: {inactive_lessons}

🛠️ Выберите действие:
"""
        
        await callback.message.edit_text(
            lessons_text,
            reply_markup=lessons_management_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе меню уроков: {e}")
        await callback.answer("❌ Ошибка при загрузке.")


# УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ - ЗАКОММЕНТИРОВАНО (избыточно для простого бота)
# @router.callback_query(F.data == "admin_users")
# async def show_users_menu(callback: CallbackQuery, session: AsyncSession):
#     """Меню управления пользователями"""
#     try:
#         user_service = UserService(session)
#         
#         # Получаем статистику пользователей (простую версию)
#         users_text = f"""
# 👥 <b>Управление пользователями</b>
# 
# 🛠️ Выберите действие:
# """
#         
#         await callback.message.edit_text(
#             users_text,
#             reply_markup=users_management_keyboard()
#         )
#         await callback.answer()
#         
#     except Exception as e:
#         logger.error(f"Ошибка при показе меню пользователей: {e}")
#         await callback.answer("❌ Ошибка при загрузке.")

@router.callback_query(F.data == "admin_stats")
async def show_stats_menu(callback: CallbackQuery, session: AsyncSession):
    """Меню статистики"""
    try:
        stats_text = f"""
📊 <b>Статистика системы</b>

📈 Выберите тип отчета:
"""
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=admin_stats_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе меню статистики: {e}")
        await callback.answer("❌ Ошибка при загрузке.")


@router.callback_query(F.data == "admin_broadcasts")
async def show_broadcasts_menu(callback: CallbackQuery, session: AsyncSession):
    """Меню рассылок"""
    try:
        broadcasts_text = f"""
📢 <b>Массовые рассылки</b>

📋 Управление рассылками:
"""
        
        await callback.message.edit_text(
            broadcasts_text,
            reply_markup=broadcasts_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе меню рассылок: {e}")
        await callback.answer("❌ Ошибка при загрузке.")


@router.callback_query(F.data == "admin_cancel")
async def admin_cancel_action(callback: CallbackQuery, state: FSMContext):
    """Отмена текущего действия"""
    try:
        await state.clear()
        await show_admin_menu(callback, None, None)
        await callback.answer("❌ Действие отменено")
        
    except Exception as e:
        logger.error(f"Ошибка при отмене действия: {e}")
        await callback.answer("❌ Ошибка при отмене.")