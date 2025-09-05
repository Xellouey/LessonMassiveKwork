"""
Обработчики управления пользователями в административной панели
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.user_management import UserManagementService
from keyboards.admin import (
    users_management_keyboard, user_details_keyboard, 
    confirm_action_keyboard, back_to_admin_keyboard
)
from middlewares.admin import AdminOnlyMiddleware
from states.admin import UserManagementStates

logger = logging.getLogger(__name__)
router = Router()
router.callback_query.middleware(AdminOnlyMiddleware())


@router.callback_query(F.data == "admin_users")
async def show_users_menu(callback: CallbackQuery):
    """Показать меню управления пользователями"""
    try:
        text = """
👥 <b>Управление пользователями</b>

Выберите действие:

👥 <b>Все пользователи</b> - просмотр списка всех пользователей
🔍 <b>Поиск пользователя</b> - найти пользователя по имени или ID
🚫 <b>Заблокированные</b> - список заблокированных пользователей
⭐ <b>Активные покупатели</b> - пользователи с покупками
📊 <b>Статистика</b> - общая статистика пользователей
👑 <b>Администраторы</b> - управление администраторами
"""

        if callback.message:
            await callback.message.edit_text(
                text,
                reply_markup=users_management_keyboard(),
                parse_mode="HTML"
            )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при показе меню пользователей: {e}")
        await callback.answer("Произошла ошибка при загрузке меню")


@router.callback_query(F.data == "admin_users_list")
async def show_users_list(callback: CallbackQuery, session: AsyncSession):
    """Показать список всех пользователей"""
    try:
        user_service = UserManagementService(session)
        users = await user_service.get_all_users(limit=10)
        
        if not users:
            text = "📭 <b>Пользователи не найдены</b>"
        else:
            text = "👥 <b>Список пользователей</b>\n\n"
            
            for i, user in enumerate(users, 1):
                status_icon = "✅" if user.is_active else "🚫"
                activity_days = (user.last_activity - user.registration_date).days if user.last_activity else 0
                
                text += f"{i}. {status_icon} <b>{user.full_name}</b>\n"
                text += f"   🆔 ID: <code>{user.user_id}</code>\n"
                text += f"   👤 @{user.username or 'Нет username'}\n"
                text += f"   📅 Регистрация: {user.registration_date.strftime('%d.%m.%Y')}\n"
                text += f"   💰 Потрачено: ⭐ {user.total_spent}\n\n"

        if callback.message:
            await callback.message.edit_text(
                text,
                reply_markup=back_to_admin_keyboard(),
                parse_mode="HTML"
            )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении списка пользователей: {e}")
        await callback.answer("Произошла ошибка при загрузке списка пользователей")


@router.callback_query(F.data == "admin_user_search")
async def start_user_search(callback: CallbackQuery, state: FSMContext):
    """Начать поиск пользователя"""
    try:
        await state.set_state(UserManagementStates.searching_user)
        
        text = """
🔍 <b>Поиск пользователя</b>

Отправьте один из следующих параметров для поиска:
• <b>Telegram ID</b> (числовой ID пользователя)
• <b>Username</b> (без @)
• <b>Имя пользователя</b> (полное имя)

Пример: <code>12345678</code> или <code>ivan_petrov</code> или <code>Иван</code>
"""

        if callback.message:
            await callback.message.edit_text(
                text,
                reply_markup=back_to_admin_keyboard(),
                parse_mode="HTML"
            )
        await callback.answer("🔍 Введите данные для поиска")

    except Exception as e:
        logger.error(f"Ошибка при начале поиска пользователя: {e}")
        await callback.answer("Произошла ошибка при запуске поиска")


@router.message(UserManagementStates.searching_user)
async def process_user_search(message: Message, session: AsyncSession, state: FSMContext):
    """Обработка поискового запроса"""
    try:
        if not message.text:
            await message.answer("❌ Пожалуйста, отправьте текстовое сообщение для поиска")
            return

        user_service = UserManagementService(session)
        users = await user_service.search_users(message.text.strip())
        
        if not users:
            await message.answer(
                f"📭 Пользователи по запросу '<b>{message.text}</b>' не найдены",
                parse_mode="HTML"
            )
        elif len(users) == 1:
            # Если найден один пользователь, показываем детальную информацию
            user = users[0]
            await show_user_details(message, session, user.user_id)
        else:
            # Если найдено несколько пользователей, показываем список
            text = f"🔍 <b>Результаты поиска по запросу '{message.text}'</b>\n\n"
            
            for i, user in enumerate(users[:10], 1):  # Показываем максимум 10
                status_icon = "✅" if user.is_active else "🚫"
                text += f"{i}. {status_icon} <b>{user.full_name}</b>\n"
                text += f"   🆔 ID: <code>{user.user_id}</code>\n"
                text += f"   👤 @{user.username or 'Нет username'}\n\n"
            
            if len(users) > 10:
                text += f"... и еще {len(users) - 10} пользователей"
            
            await message.answer(text, parse_mode="HTML")
        
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка при поиске пользователя: {e}")
        await message.answer("❌ Произошла ошибка при поиске")
        await state.clear()


async def show_user_details(message: Message, session: AsyncSession, user_id: int):
    """Показать детальную информацию о пользователе"""
    try:
        user_service = UserManagementService(session)
        stats = await user_service.get_user_statistics(user_id)
        
        if not stats:
            await message.answer("❌ Пользователь не найден")
            return

        status_text = "✅ Активен" if stats['is_active'] else "🚫 Заблокирован"
        last_activity = stats['last_activity'].strftime('%d.%m.%Y %H:%M') if stats['last_activity'] else "Никогда"
        last_purchase = stats['last_purchase'].strftime('%d.%m.%Y %H:%M') if stats['last_purchase'] else "Нет покупок"
        
        text = f"""
👤 <b>Информация о пользователе</b>

<b>Основные данные:</b>
• Имя: <b>{stats['full_name']}</b>
• Username: @{stats['username'] or 'Отсутствует'}
• Telegram ID: <code>{stats['user_id']}</code>
• Язык: {stats['language']}
• Статус: {status_text}

<b>Активность:</b>
• Регистрация: {stats['registration_date'].strftime('%d.%m.%Y %H:%M')}
• Последняя активность: {last_activity}
• Всего действий: {stats['total_activities']}

<b>Покупки:</b>
• Всего покупок: {stats['total_purchases']}
• Потрачено: ⭐ {stats['total_spent']}
• Последняя покупка: {last_purchase}
"""

        await message.answer(
            text,
            reply_markup=user_details_keyboard(user_id),
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Ошибка при получении информации о пользователе {user_id}: {e}")
        await message.answer("❌ Ошибка при загрузке информации о пользователе")


@router.callback_query(F.data.startswith("admin_block_user:"))
async def block_user(callback: CallbackQuery, session: AsyncSession):
    """Заблокировать пользователя"""
    try:
        user_id = int(callback.data.split(":")[1])
        
        user_service = UserManagementService(session)
        success = await user_service.block_user(user_id)
        
        if success:
            await callback.answer("✅ Пользователь заблокирован")
            # Обновляем информацию о пользователе
            await show_user_details(callback.message, session, user_id)
        else:
            await callback.answer("❌ Ошибка при блокировке пользователя")

    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID пользователя")
    except Exception as e:
        logger.error(f"Ошибка при блокировке пользователя: {e}")
        await callback.answer("❌ Произошла ошибка при блокировке")


@router.callback_query(F.data.startswith("admin_unblock_user:"))
async def unblock_user(callback: CallbackQuery, session: AsyncSession):
    """Разблокировать пользователя"""
    try:
        user_id = int(callback.data.split(":")[1])
        
        user_service = UserManagementService(session)
        success = await user_service.unblock_user(user_id)
        
        if success:
            await callback.answer("✅ Пользователь разблокирован")
            # Обновляем информацию о пользователе
            await show_user_details(callback.message, session, user_id)
        else:
            await callback.answer("❌ Ошибка при разблокировке пользователя")

    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID пользователя")
    except Exception as e:
        logger.error(f"Ошибка при разблокировке пользователя: {e}")
        await callback.answer("❌ Произошла ошибка при разблокировке")


@router.callback_query(F.data.startswith("admin_user_purchases:"))
async def show_user_purchases(callback: CallbackQuery, session: AsyncSession):
    """Показать покупки пользователя"""
    try:
        user_id = int(callback.data.split(":")[1])
        
        user_service = UserManagementService(session)
        purchases = await user_service.get_user_purchases(user_id, limit=10)
        
        if not purchases:
            text = "📭 <b>У пользователя нет покупок</b>"
        else:
            text = f"🛒 <b>Покупки пользователя</b>\n\n"
            
            total_amount = 0
            for i, purchase in enumerate(purchases, 1):
                lesson_title = purchase.lesson.title if purchase.lesson else "Урок удален"
                status_icon = "✅" if purchase.status == "completed" else "❌"
                
                text += f"{i}. {status_icon} <b>{lesson_title}</b>\n"
                text += f"   💰 Сумма: ⭐ {purchase.amount_stars}\n"
                text += f"   📅 Дата: {purchase.purchase_date.strftime('%d.%m.%Y %H:%M')}\n"
                text += f"   📄 Статус: {purchase.status}\n\n"
                
                if purchase.status == "completed":
                    total_amount += purchase.amount_stars
            
            text += f"<b>Общая сумма покупок: ⭐ {total_amount}</b>"

        if callback.message:
            await callback.message.edit_text(
                text,
                reply_markup=back_to_admin_keyboard(),
                parse_mode="HTML"
            )
        await callback.answer()

    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID пользователя")
    except Exception as e:
        logger.error(f"Ошибка при получении покупок пользователя: {e}")
        await callback.answer("❌ Ошибка при загрузке покупок")


@router.callback_query(F.data == "admin_blocked_users")
async def show_blocked_users(callback: CallbackQuery, session: AsyncSession):
    """Показать заблокированных пользователей"""
    try:
        user_service = UserManagementService(session)
        blocked_users = await user_service.get_blocked_users(limit=10)
        
        if not blocked_users:
            text = "✅ <b>Нет заблокированных пользователей</b>"
        else:
            text = "🚫 <b>Заблокированные пользователи</b>\n\n"
            
            for i, user in enumerate(blocked_users, 1):
                text += f"{i}. <b>{user.full_name}</b>\n"
                text += f"   🆔 ID: <code>{user.user_id}</code>\n"
                text += f"   👤 @{user.username or 'Нет username'}\n"
                text += f"   📅 Регистрация: {user.registration_date.strftime('%d.%m.%Y')}\n\n"

        if callback.message:
            await callback.message.edit_text(
                text,
                reply_markup=back_to_admin_keyboard(),
                parse_mode="HTML"
            )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении заблокированных пользователей: {e}")
        await callback.answer("Произошла ошибка при загрузке списка")


@router.callback_query(F.data == "admin_active_buyers")
async def show_active_buyers(callback: CallbackQuery, session: AsyncSession):
    """Показать активных покупателей"""
    try:
        user_service = UserManagementService(session)
        top_buyers = await user_service.get_top_buyers(limit=10)
        
        if not top_buyers:
            text = "📭 <b>Нет покупателей</b>"
        else:
            text = "⭐ <b>Топ покупатели</b>\n\n"
            
            for i, buyer in enumerate(top_buyers, 1):
                text += f"{i}. <b>{buyer['full_name']}</b>\n"
                text += f"   🆔 ID: <code>{buyer['user_id']}</code>\n"
                text += f"   👤 @{buyer['username'] or 'Нет username'}\n"
                text += f"   🛒 Покупок: {buyer['purchases_count']}\n"
                text += f"   💰 Потратил: ⭐ {buyer['total_spent']}\n\n"

        if callback.message:
            await callback.message.edit_text(
                text,
                reply_markup=back_to_admin_keyboard(),
                parse_mode="HTML"
            )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении топ покупателей: {e}")
        await callback.answer("Произошла ошибка при загрузке списка покупателей")


@router.callback_query(F.data == "admin_user_stats")
async def show_user_stats(callback: CallbackQuery, session: AsyncSession):
    """Показать общую статистику пользователей"""
    try:
        user_service = UserManagementService(session)
        counts = await user_service.get_users_count()
        
        text = f"""
📊 <b>Статистика пользователей</b>

👥 <b>Общие показатели:</b>
• Всего пользователей: {counts['total']}
• Активных: {counts['active']}
• Заблокированных: {counts['blocked']}
• Новых (за неделю): {counts['recent']}

📈 <b>Процентное соотношение:</b>
• Активных: {round(counts['active'] / counts['total'] * 100, 1) if counts['total'] > 0 else 0}%
• Заблокированных: {round(counts['blocked'] / counts['total'] * 100, 1) if counts['total'] > 0 else 0}%
• Новых пользователей: {round(counts['recent'] / counts['total'] * 100, 1) if counts['total'] > 0 else 0}%
"""

        if callback.message:
            await callback.message.edit_text(
                text,
                reply_markup=back_to_admin_keyboard(),
                parse_mode="HTML"
            )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении статистики пользователей: {e}")
        await callback.answer("Произошла ошибка при загрузке статистики")