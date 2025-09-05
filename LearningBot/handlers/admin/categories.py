"""
Административные обработчики для управления категориями
"""
import logging
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.category import CategoryService
from keyboards.admin import (
    categories_list_keyboard,
    category_edit_keyboard,
    confirm_action_keyboard,
    simple_confirmation_keyboard,
    back_to_admin_keyboard
)
from states.admin import CategoryManagementStates
from middlewares.admin import AdminOnlyMiddleware

logger = logging.getLogger(__name__)

# Роутер для управления категориями
router = Router()
router.message.middleware(AdminOnlyMiddleware())
router.callback_query.middleware(AdminOnlyMiddleware())


@router.callback_query(F.data == "admin_categories_list")
async def show_categories_list(callback: CallbackQuery, session: AsyncSession):
    """Показать список всех категорий"""
    try:
        category_service = CategoryService(session)
        
        # Получаем категории с количеством уроков
        categories_data = await category_service.get_categories_with_lesson_count()
        
        if not categories_data:
            await callback.message.edit_text(
                "📁 <b>Список категорий пуст</b>\n\nНачните с создания первой категории!",
                reply_markup=back_to_admin_keyboard()
            )
            await callback.answer()
            return
        
        categories_text = f"""
📁 <b>Управление категориями</b>

📊 <b>Всего категорий:</b> {len(categories_data)}

📋 <b>Выберите категорию для редактирования:</b>
"""
        
        await callback.message.edit_text(
            categories_text,
            reply_markup=categories_list_keyboard(categories_data)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе списка категорий: {e}")
        await callback.answer("❌ Ошибка при загрузке списка категорий.")


@router.callback_query(F.data.startswith("admin_edit_category:"))
async def edit_category_menu(callback: CallbackQuery, session: AsyncSession):
    """Меню редактирования конкретной категории"""
    try:
        category_id = int(callback.data.split(":")[1])
        
        category_service = CategoryService(session)
        category = await category_service.get_category_by_id(category_id)
        
        if not category:
            await callback.answer("❌ Категория не найдена")
            return
        
        # Получаем статистику категории
        stats = await category_service.get_category_stats(category_id)
        
        status_text = "✅ Активна" if category.is_active else "❌ Неактивна"
        
        category_text = f"""
📁 <b>Редактирование категории</b>

<b>📖 Название:</b> {category.name}

<b>🔄 Статус:</b> {status_text}

<b>📊 Статистика:</b>
• 📚 Всего уроков: {stats['total_lessons'] if stats else 0}
• ✅ Активных: {stats['active_lessons'] if stats else 0}
• 🎁 Бесплатных: {stats['free_lessons'] if stats else 0}
• 👀 Просмотров: {stats['total_views'] if stats else 0}

Выберите параметр для редактирования:
"""
        
        await callback.message.edit_text(
            category_text,
            reply_markup=category_edit_keyboard(category_id)
        )
        await callback.answer()
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID категории")
    except Exception as e:
        logger.error(f"Ошибка при загрузке категории для редактирования: {e}")
        await callback.answer("❌ Ошибка при загрузке категории.")


@router.callback_query(F.data == "admin_create_category")
async def start_category_creation(callback: CallbackQuery, state: FSMContext):
    """Начать создание новой категории"""
    try:
        await state.set_state(CategoryManagementStates.creating_category)
        await state.update_data(step="name")
        
        create_text = """
➕ <b>Создание новой категории</b>

📝 <b>Шаг 1 из 2:</b> Введите название категории

Отправьте сообщение с названием категории (максимум 100 символов):

<i>Например: "Программирование", "Дизайн", "Маркетинг"</i>
"""
        
        await callback.message.edit_text(
            create_text,
            reply_markup=back_to_admin_keyboard()
        )
        await callback.answer("📝 Введите название категории")
        
    except Exception as e:
        logger.error(f"Ошибка при начале создания категории: {e}")
        await callback.answer("❌ Ошибка при создании категории.")


@router.message(CategoryManagementStates.creating_category)
async def process_category_creation(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка создания категории по шагам"""
    try:
        data = await state.get_data()
        step = data.get("step")
        
        if step == "name":
            # Сохраняем название
            if not message.text or len(message.text) > 100:
                await message.answer("❌ Название слишком длинное. Максимум 100 символов.")
                return
            
            # Проверяем, не существует ли уже такая категория
            category_service = CategoryService(session)
            existing_category = await category_service.get_category_by_name(message.text)
            
            if existing_category:
                if existing_category.is_active:
                    await message.answer(f"❌ Категория '{message.text}' уже существует.")
                    return
                else:
                    # Если категория есть, но неактивна - предлагаем активировать
                    await message.answer(f"""
🔄 Категория '{message.text}' найдена, но неактивна.

Хотите активировать её или создать новую?
""")
                    # TODO: Добавить клавиатуру для выбора
                    return
            
            # Создаем категорию
            await finalize_category_creation(message, state, session, message.text)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке создания категории: {e}")
        await message.answer("❌ Ошибка при создании категории.")


async def finalize_category_creation(message: Message, state: FSMContext, session: AsyncSession, name: str):
    """Завершение создания категории"""
    try:
        category_service = CategoryService(session)
        
        # Создаем категорию без описания
        new_category = await category_service.create_category(
            name=name,
            description=None
        )
        
        await state.clear()
        
        success_text = f"""
✅ <b>Категория успешно создана!</b>

📁 <b>Название:</b> {new_category.name}

Категория активна и доступна для использования!
"""
        
        await message.answer(
            success_text,
            reply_markup=back_to_admin_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка при завершении создания категории: {e}")
        await message.answer("❌ Ошибка при сохранении категории.")


@router.callback_query(F.data.startswith("edit_category_name:"))
async def edit_category_name(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование названия категории"""
    try:
        category_id = int(callback.data.split(":")[1])
        
        await state.set_state(CategoryManagementStates.editing_name)
        await state.update_data(category_id=category_id)
        
        await callback.message.edit_text(
            "📝 <b>Редактирование названия категории</b>\n\nВведите новое название (максимум 100 символов):",
            reply_markup=back_to_admin_keyboard()
        )
        await callback.answer()
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID категории")


@router.message(CategoryManagementStates.editing_name)
async def process_category_name_edit(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка редактирования названия категории"""
    try:
        if len(message.text) > 100:
            await message.answer("❌ Название слишком длинное. Максимум 100 символов.")
            return
        
        data = await state.get_data()
        category_id = data["category_id"]
        
        category_service = CategoryService(session)
        
        # Проверяем, не существует ли уже категория с таким названием
        existing_category = await category_service.get_category_by_name(message.text)
        if existing_category and existing_category.id != category_id:
            await message.answer("❌ Категория с таким названием уже существует.")
            return
        
        updated_category = await category_service.update_category(
            category_id=category_id,
            name=message.text
        )
        
        if updated_category:
            await state.clear()
            await message.answer(
                f"✅ Название категории изменено на: <b>{updated_category.name}</b>",
                reply_markup=back_to_admin_keyboard()
            )
        else:
            await message.answer("❌ Ошибка при обновлении названия.")
        
    except Exception as e:
        logger.error(f"Ошибка при редактировании названия категории: {e}")
        await message.answer("❌ Ошибка при обновлении категории.")


@router.callback_query(F.data.startswith("toggle_category_status:"))
async def toggle_category_status(callback: CallbackQuery, session: AsyncSession):
    """Переключить статус активности категории"""
    try:
        category_id = int(callback.data.split(":")[1])
        
        category_service = CategoryService(session)
        category = await category_service.get_category_by_id(category_id)
        
        if not category:
            await callback.answer("❌ Категория не найдена")
            return
        
        # Переключаем статус
        new_status = not category.is_active
        updated_category = await category_service.update_category(category_id, is_active=new_status)
        
        if updated_category:
            status_text = "активирована" if new_status else "деактивирована"
            await callback.answer(f"✅ Категория {status_text}")
            
            # Обновляем меню редактирования
            await edit_category_menu(callback, session)
        else:
            await callback.answer("❌ Ошибка при изменении статуса")
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID категории")
    except Exception as e:
        logger.error(f"Ошибка при переключении статуса категории: {e}")
        await callback.answer("❌ Ошибка при изменении статуса")


@router.callback_query(F.data.startswith("delete_category:"))
async def confirm_category_deletion(callback: CallbackQuery, session: AsyncSession):
    """Подтверждение удаления категории"""
    try:
        category_id = int(callback.data.split(":")[1])
        
        category_service = CategoryService(session)
        category = await category_service.get_category_by_id(category_id)
        
        if not category:
            await callback.answer("❌ Категория не найдена")
            return
        
        # Получаем статистику для показа
        stats = await category_service.get_category_stats(category_id)
        lesson_count = stats['total_lessons'] if stats else 0
        
        confirm_text = f"""
🗑 <b>Удаление категории</b>

<b>Категория:</b> {category.name}
<b>Уроков в категории:</b> {lesson_count}

⚠️ <b>Внимание!</b> 
"""
        
        if lesson_count > 0:
            confirm_text += f"""
В категории есть уроки ({lesson_count} шт.). 
При удалении категории уроки останутся, но потеряют привязку к категории.

Вы уверены, что хотите удалить категорию?
"""
        else:
            confirm_text += "Вы уверены, что хотите удалить пустую категорию?"
        
        await callback.message.edit_text(
            confirm_text,
            reply_markup=simple_confirmation_keyboard(f"confirm_delete_category:{category_id}", "admin_categories_list")
        )
        await callback.answer()
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID категории")
    except Exception as e:
        logger.error(f"Ошибка при подтверждении удаления категории: {e}")
        await callback.answer("❌ Ошибка при удалении категории")


@router.callback_query(F.data.startswith("confirm_delete_category:"))
async def delete_category(callback: CallbackQuery, session: AsyncSession):
    """Удаление категории"""
    try:
        category_id = int(callback.data.split(":")[1])
        
        category_service = CategoryService(session)
        category = await category_service.get_category_by_id(category_id)
        
        if not category:
            await callback.answer("❌ Категория не найдена")
            return
        
        category_name = category.name
        
        # Удаляем категорию (force=True для полного удаления)
        success = await category_service.delete_category(category_id, force=True)
        
        if success:
            await callback.answer(f"✅ Категория '{category_name}' удалена")
            # Возвращаемся к списку категорий
            await show_categories_list(callback, session)
        else:
            await callback.answer("❌ Ошибка при удалении категории")
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID категории")
    except Exception as e:
        logger.error(f"Ошибка при удалении категории: {e}")
        await callback.answer("❌ Ошибка при удалении категории")