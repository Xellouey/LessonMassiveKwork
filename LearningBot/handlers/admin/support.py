"""
Обработчики поддержки для администраторов
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from services.support import SupportService
from services.notification import NotificationService
from services.admin import AdminService
from states.admin import SupportManagementStates
from middlewares.admin import AdminOnlyMiddleware
from database.models import SupportTicket

logger = logging.getLogger(__name__)

router = Router()
router.message.middleware(AdminOnlyMiddleware())
router.callback_query.middleware(AdminOnlyMiddleware())


def support_tickets_keyboard(tickets: List[SupportTicket], page: int = 0, per_page: int = 10) -> InlineKeyboardMarkup:
    """Клавиатура со списком тикетов поддержки"""
    builder = InlineKeyboardBuilder()
    
    # Группируем тикеты по статусу
    status_icons = {
        "open": "🟡",
        "in_progress": "🔵", 
        "closed": "🟢"
    }
    
    start_idx = page * per_page
    end_idx = start_idx + per_page
    tickets_page = tickets[start_idx:end_idx]
    
    for ticket in tickets_page:
        icon = status_icons.get(ticket.status, "⚪")
        text = f"{icon} #{ticket.ticket_number} - {ticket.user.full_name[:20]}"
        builder.row(InlineKeyboardButton(
            text=text,
            callback_data=f"ticket:{ticket.id}"
        ))
    
    # Навигация
    nav_buttons = []
    total_pages = (len(tickets) + per_page - 1) // per_page
    
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"tickets_page:{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="current_page"))
    
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"tickets_page:{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Фильтры по статусу
    builder.row(
        InlineKeyboardButton(text="🟡 Открытые", callback_data="filter:open"),
        InlineKeyboardButton(text="🔵 В работе", callback_data="filter:in_progress")
    )
    builder.row(
        InlineKeyboardButton(text="🟢 Закрытые", callback_data="filter:closed"),
        InlineKeyboardButton(text="📋 Все", callback_data="filter:all")
    )
    
    builder.row(InlineKeyboardButton(text="🔙 Админ панель", callback_data="admin_menu"))
    
    return builder.as_markup()


def ticket_details_keyboard(ticket: SupportTicket, admin_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для управления конкретным тикетом"""
    builder = InlineKeyboardBuilder()
    
    # Ответить на тикет
    builder.row(InlineKeyboardButton(
        text="💬 Ответить",
        callback_data=f"respond:{ticket.id}"
    ))
    
    # Действия в зависимости от статуса
    if ticket.status == "open":
        builder.row(
            InlineKeyboardButton(text="📝 Взять в работу", callback_data=f"assign:{ticket.id}"),
            InlineKeyboardButton(text="✅ Закрыть", callback_data=f"close:{ticket.id}")
        )
    elif ticket.status == "in_progress":
        if ticket.assigned_admin_id == admin_id:
            builder.row(InlineKeyboardButton(text="✅ Закрыть тикет", callback_data=f"close:{ticket.id}"))
        builder.row(InlineKeyboardButton(text="🔄 Переназначить", callback_data=f"reassign:{ticket.id}"))
    elif ticket.status == "closed":
        builder.row(InlineKeyboardButton(text="🔄 Переоткрыть", callback_data=f"reopen:{ticket.id}"))
    

    
    builder.row(InlineKeyboardButton(text="🔙 К списку тикетов", callback_data="admin_support"))
    
    return builder.as_markup()


@router.callback_query(F.data == "admin_support")
async def show_support_tickets(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Показать список тикетов поддержки"""
    try:
        support_service = SupportService(session)
        
        # Получаем все тикеты
        tickets = await support_service.get_admin_tickets(limit=100)
        
        # Статистика
        open_count = len([t for t in tickets if t.status == "open"])
        in_progress_count = len([t for t in tickets if t.status == "in_progress"])
        closed_count = len([t for t in tickets if t.status == "closed"])
        
        text = f"""
🎫 <b>Тикеты поддержки</b>

📊 <b>Статистика:</b>
🟡 Открытые: {open_count}
🔵 В работе: {in_progress_count}
🟢 Закрытые: {closed_count}
📝 Всего: {len(tickets)}

Выберите тикет для просмотра:
"""
        
        await state.set_state(SupportManagementStates.viewing_support_tickets)
        
        if callback.message:
            await callback.message.edit_text(
                text,
                reply_markup=support_tickets_keyboard(tickets),
                parse_mode="HTML"
            )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе тикетов поддержки: {e}")
        await callback.answer("Произошла ошибка")


@router.callback_query(F.data.startswith("filter:"))
async def filter_support_tickets(callback: CallbackQuery, session: AsyncSession):
    """Фильтрация тикетов по статусу"""
    try:
        status = callback.data.split(":")[1]
        support_service = SupportService(session)
        
        if status == "all":
            tickets = await support_service.get_admin_tickets(limit=100)
        else:
            tickets = await support_service.get_tickets_by_status(status, limit=100)
        
        status_names = {
            "open": "Открытые",
            "in_progress": "В работе", 
            "closed": "Закрытые",
            "all": "Все"
        }
        
        text = f"""
🎫 <b>Тикеты поддержки - {status_names.get(status, status)}</b>

📝 Найдено тикетов: {len(tickets)}

Выберите тикет для просмотра:
"""
        
        if callback.message:
            await callback.message.edit_text(
                text,
                reply_markup=support_tickets_keyboard(tickets),
                parse_mode="HTML"
            )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при фильтрации тикетов: {e}")
        await callback.answer("Произошла ошибка")


@router.callback_query(F.data.startswith("ticket:"))
async def show_ticket_details(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Показать детали тикета"""
    try:
        ticket_id = int(callback.data.split(":")[1])
        support_service = SupportService(session)
        
        ticket = await support_service.get_ticket_by_id(ticket_id)
        if not ticket:
            await callback.answer("Тикет не найден")
            return
        
        # Формируем информацию о тикете
        status_icons = {
            "open": "🟡 Открыт",
            "in_progress": "🔵 В работе",
            "closed": "🟢 Закрыт"
        }
        
        priority_icons = {
            "low": "🟢 Низкий",
            "normal": "🟡 Обычный",
            "high": "🟠 Высокий",
            "urgent": "🔴 Срочный"
        }
        
        assigned_text = "Не назначен"
        if ticket.assigned_admin:
            assigned_text = f"@{ticket.assigned_admin.username or 'Admin'}"
        
        # Подсчитываем ответы
        user_responses = len([r for r in ticket.responses if r.sender_type == "user"])
        admin_responses = len([r for r in ticket.responses if r.sender_type == "admin" and not r.is_internal])
        
        text = f"""
🎫 <b>Тикет #{ticket.ticket_number}</b>

📊 <b>Статус:</b> {status_icons.get(ticket.status, ticket.status)}
🔥 <b>Приоритет:</b> {priority_icons.get(ticket.priority, ticket.priority)}
👨‍💼 <b>Назначен:</b> {assigned_text}

👤 <b>Пользователь:</b>
• Имя: {ticket.user.full_name}
• ID: <code>{ticket.user_id}</code>
• Username: @{ticket.user.username or 'не указан'}

💬 <b>Первоначальное сообщение:</b>
{ticket.initial_message}

📈 <b>Активность:</b>
• Ответов пользователя: {user_responses}
• Ответов поддержки: {admin_responses}

🕐 <b>Время:</b>
• Создан: {ticket.created_at.strftime('%d.%m.%Y %H:%M')}
• Обновлен: {ticket.updated_at.strftime('%d.%m.%Y %H:%M') if ticket.updated_at else 'Нет'}
{f"• Закрыт: {ticket.closed_at.strftime('%d.%m.%Y %H:%M')}" if ticket.closed_at else ""}
"""
        
        await state.set_state(SupportManagementStates.viewing_ticket_details)
        await state.update_data(current_ticket_id=ticket_id)
        
        if callback.message:
            try:
                await callback.message.edit_text(
                    text,
                    reply_markup=ticket_details_keyboard(ticket, callback.from_user.id),
                    parse_mode="HTML"
                )
            except Exception as edit_error:
                logger.warning(f"Не удалось редактировать сообщение, отправляем новое: {edit_error}")
                # Отправляем новое сообщение вместо редактирования
                from aiogram import Bot
                bot = Bot.get_current()
                await bot.send_message(
                    chat_id=callback.from_user.id,
                    text=text,
                    reply_markup=ticket_details_keyboard(ticket, callback.from_user.id),
                    parse_mode="HTML"
                )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе деталей тикета: {e}")
        await callback.answer("Произошла ошибка")


@router.callback_query(F.data.startswith("respond:"))
async def start_response(callback: CallbackQuery, state: FSMContext):
    """Начать ответ на тикет"""
    try:
        ticket_id = int(callback.data.split(":")[1])
        
        await state.set_state(SupportManagementStates.responding_to_support)
        await state.update_data(responding_to_ticket=ticket_id)
        
        text = """
💬 <b>Ответ на тикет</b>

Напишите ваш ответ пользователю. Сообщение будет отправлено ему автоматически.

<i>Отправьте текстовое сообщение с ответом:</i>
"""
        
        cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data=f"ticket:{ticket_id}")]
        ])
        
        if callback.message:
            await callback.message.edit_text(
                text,
                reply_markup=cancel_keyboard,
                parse_mode="HTML"
            )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при начале ответа: {e}")
        await callback.answer("Произошла ошибка")


@router.message(SupportManagementStates.responding_to_support)
async def handle_support_response(message: Message, session: AsyncSession, state: FSMContext, bot: Bot):
    """Обработка ответа администратора"""
    try:
        if not message.text:
            await message.answer("❗ Пожалуйста, отправьте текстовое сообщение")
            return
        
        data = await state.get_data()
        ticket_id = data.get("responding_to_ticket")
        
        if not ticket_id:
            await message.answer("❌ Ошибка: тикет не найден")
            await state.clear()
            return
        
        support_service = SupportService(session)
        notification_service = NotificationService(bot, session)
        admin_service = AdminService(session)
        
        # Получаем тикет
        ticket = await support_service.get_ticket_by_id(ticket_id)
        if not ticket:
            await message.answer("❌ Тикет не найден")
            await state.clear()
            return
        
        # Добавляем ответ
        response = await support_service.add_response(
            ticket_id=ticket_id,
            sender_id=message.from_user.id,
            message=message.text,
            sender_type="admin"
        )
        
        if not response:
            await message.answer("❌ Не удалось добавить ответ")
            return
        
        # Обновляем статус на "в работе" если был "открыт"
        if ticket.status == "open":
            await support_service.update_ticket_status(
                ticket_id=ticket_id,
                status="in_progress",
                admin_id=message.from_user.id
            )
        
        # Получаем информацию об администраторе
        admin = await admin_service.get_admin_by_user_id(message.from_user.id)
        admin_name = admin.username if admin and admin.username else "Support"
        
        # Отправляем уведомление пользователю
        await notification_service.notify_user_of_response(
            ticket=ticket,
            response_message=message.text,
            admin_name=admin_name
        )
        
        # Подтверждение
        await message.answer(
            f"✅ <b>Ответ отправлен!</b>\\n\\n"
            f"Пользователю {ticket.user.full_name} отправлен ваш ответ по тикету #{ticket.ticket_number}.",
            parse_mode="HTML"
        )
        
        await state.clear()
        
        # Возвращаемся к деталям тикета
        try:
            # Создаем фиктивный callback для обновления деталей тикета
            fake_callback = type('FakeCallback', (), {
                'data': f'ticket:{ticket_id}',
                'from_user': message.from_user,
                'message': None,
                'answer': lambda text="": None
            })()
            
            await show_ticket_details(
                callback=fake_callback,
                session=session,
                state=state
            )
        except Exception as detail_error:
            logger.error(f"Ошибка при обновлении деталей тикета: {detail_error}")
            # Если не удалось обновить детали, просто отправляем новое сообщение
            pass
        
    except Exception as e:
        logger.error(f"Ошибка при обработке ответа поддержки: {e}")
        await message.answer("❌ Произошла ошибка при отправке ответа")
        await state.clear()


@router.callback_query(F.data.startswith("assign:"))
async def assign_ticket(callback: CallbackQuery, session: AsyncSession):
    """Назначить тикет на себя"""
    try:
        ticket_id = int(callback.data.split(":")[1])
        support_service = SupportService(session)
        
        success = await support_service.assign_ticket(ticket_id, callback.from_user.id)
        
        if success:
            await callback.answer("✅ Тикет назначен на вас")
            # Отправляем обновленное сообщение с деталями тикета
            try:
                ticket = await support_service.get_ticket_by_id(ticket_id)
                if ticket and callback.message:
                    # Обновляем сообщение с новыми деталями
                    text = f"✅ Тикет #{ticket.ticket_number} назначен на вас!"
                    await callback.bot.send_message(
                        chat_id=callback.from_user.id,
                        text=text
                    )
            except Exception as update_error:
                logger.error(f"Ошибка при обновлении: {update_error}")
        else:
            await callback.answer("❌ Не удалось назначить тикет")
        
    except Exception as e:
        logger.error(f"Ошибка при назначении тикета: {e}")
        await callback.answer("Произошла ошибка")


@router.callback_query(F.data.startswith("close:"))
async def close_ticket(callback: CallbackQuery, session: AsyncSession):
    """Закрыть тикет"""
    try:
        ticket_id = int(callback.data.split(":")[1])
        support_service = SupportService(session)
        
        success = await support_service.close_ticket(ticket_id, callback.from_user.id)
        
        if success:
            await callback.answer("✅ Тикет закрыт")
            # Отправляем подтверждение
            try:
                ticket = await support_service.get_ticket_by_id(ticket_id)
                if ticket:
                    text = f"✅ Тикет #{ticket.ticket_number} закрыт!"
                    await callback.bot.send_message(
                        chat_id=callback.from_user.id,
                        text=text
                    )
            except Exception as update_error:
                logger.error(f"Ошибка при отправке подтверждения: {update_error}")
        else:
            await callback.answer("❌ Не удалось закрыть тикет")
        
    except Exception as e:
        logger.error(f"Ошибка при закрытии тикета: {e}")
        await callback.answer("Произошла ошибка")


@router.callback_query(F.data.startswith("reopen:"))
async def reopen_ticket(callback: CallbackQuery, session: AsyncSession):
    """Переоткрыть тикет"""
    try:
        ticket_id = int(callback.data.split(":")[1])
        support_service = SupportService(session)
        
        success = await support_service.reopen_ticket(ticket_id)
        
        if success:
            await callback.answer("✅ Тикет переоткрыт")
            # Отправляем подтверждение
            try:
                ticket = await support_service.get_ticket_by_id(ticket_id)
                if ticket:
                    text = f"✅ Тикет #{ticket.ticket_number} переоткрыт!"
                    await callback.bot.send_message(
                        chat_id=callback.from_user.id,
                        text=text
                    )
            except Exception as update_error:
                logger.error(f"Ошибка при отправке подтверждения: {update_error}")
        else:
            await callback.answer("❌ Не удалось переоткрыть тикет")
        
    except Exception as e:
        logger.error(f"Ошибка при переоткрытии тикета: {e}")
        await callback.answer("Произошла ошибка")