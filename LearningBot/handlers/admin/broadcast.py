"""
Обработчики рассылок для административной панели
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.broadcast import BroadcastService
from keyboards.admin import (
    broadcasts_keyboard, broadcast_audience_keyboard, broadcast_confirm_keyboard,
    broadcast_media_keyboard, broadcast_history_keyboard, broadcast_actions_keyboard,
    back_to_admin_keyboard
)
from states.admin import BroadcastStates
from middlewares.admin import AdminOnlyMiddleware

logger = logging.getLogger(__name__)
router = Router()
router.callback_query.middleware(AdminOnlyMiddleware())
router.message.middleware(AdminOnlyMiddleware())


@router.callback_query(F.data == "admin_broadcasts")
async def show_broadcasts_menu(callback: CallbackQuery):
    """Показать меню управления рассылками"""
    try:
        text = """
📢 <b>Управление рассылками</b>

Здесь вы можете создавать и управлять массовыми рассылками для пользователей бота.

🆕 <b>Новая рассылка</b> - создать и отправить рассылку
📋 <b>История рассылок</b> - просмотр всех отправленных рассылок
⏸️ <b>Активные рассылки</b> - текущие рассылки в процессе отправки
📊 <b>Статистика</b> - общая статистика по рассылкам

Выберите действие:
"""

        await callback.message.edit_text(
            text,
            reply_markup=broadcasts_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при показе меню рассылок: {e}")
        await callback.answer("Произошла ошибка при загрузке меню рассылок")


@router.callback_query(F.data == "admin_new_broadcast")
async def show_new_broadcast_form(callback: CallbackQuery, state: FSMContext):
    """Начать создание новой рассылки"""
    try:
        text = """
📝 <b>Создание новой рассылки</b>

Шаг 1 из 3: Введите текст рассылки

Напишите сообщение, которое будет отправлено пользователям.
Максимальная длина: 4000 символов.

<i>Поддерживается форматирование HTML: &lt;b&gt;жирный&lt;/b&gt;, &lt;i&gt;курсив&lt;/i&gt;, &lt;code&gt;код&lt;/code&gt;</i>
"""

        await callback.message.edit_text(
            text,
            parse_mode="HTML"
        )
        await state.set_state(BroadcastStates.entering_broadcast_text)
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при показе формы создания рассылки: {e}")
        await callback.answer("Произошла ошибка при создании формы рассылки")


@router.message(BroadcastStates.entering_broadcast_text)
async def handle_broadcast_text(message: Message, state: FSMContext):
    """Обработать введенный текст рассылки"""
    try:
        text = message.text
        
        # Валидация текста
        if not text or len(text.strip()) == 0:
            await message.answer("❌ Текст рассылки не может быть пустым. Попробуйте еще раз:")
            return
        
        if len(text) > 4000:
            await message.answer(
                "❌ Текст слишком длинный. Максимальная длина: 4000 символов.\n"
                f"Ваш текст: {len(text)} символов. Сократите текст и попробуйте еще раз:"
            )
            return
        
        # Сохраняем текст в состоянии
        await state.set_data({'text': text})
        
        # Переходим к загрузке медиа
        await message.answer(
            "✅ Текст сохранен!\n\n"
            "📎 <b>Шаг 2 из 3: Добавление медиа (необязательно)</b>\n\n"
            "Вы можете добавить к рассылке:\n"
            "• 🖼️ Фото\n"
            "• 🎥 Видео\n"
            "• 📄 Документ\n\n"
            "Или нажмите \"Пропустить\", чтобы отправить только текст.",
            reply_markup=broadcast_media_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(BroadcastStates.uploading_broadcast_media)
        
        # Удаляем сообщение пользователя для чистоты интерфейса
        try:
            await message.delete()
        except:
            pass

    except Exception as e:
        logger.error(f"Ошибка при обработке текста рассылки: {e}")
        await message.answer("❌ Произошла ошибка при сохранении текста. Попробуйте еще раз:")


@router.message(BroadcastStates.uploading_broadcast_media)
async def handle_broadcast_media(message: Message, state: FSMContext):
    """Обработать загруженное медиа для рассылки"""
    try:
        data = await state.get_data()
        
        # Определяем тип медиа и file_id
        media_type = None
        file_id = None
        
        if message.photo:
            media_type = "photo"
            file_id = message.photo[-1].file_id
        elif message.video:
            media_type = "video"
            file_id = message.video.file_id
        elif message.document:
            media_type = "document"
            file_id = message.document.file_id
        else:
            await message.answer(
                "❌ Неподдерживаемый тип медиа.\n"
                "Поддерживаются: фото, видео, документы.\n"
                "Попробуйте еще раз или нажмите \"Пропустить\"."
            )
            return
        
        # Сохраняем медиа данные
        data.update({
            'media_type': media_type,
            'file_id': file_id
        })
        await state.set_data(data)
        
        # Переходим к выбору аудитории
        await message.answer(
            "✅ Медиа добавлено!\n\n"
            "👥 <b>Шаг 3 из 3: Выбор аудитории</b>\n\n"
            "Кому отправить рассылку?",
            reply_markup=broadcast_audience_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(BroadcastStates.selecting_audience)
        
        # Удаляем сообщение пользователя
        try:
            await message.delete()
        except:
            pass

    except Exception as e:
        logger.error(f"Ошибка при обработке медиа рассылки: {e}")
        await message.answer("❌ Произошла ошибка при загрузке медиа. Попробуйте еще раз:")


@router.callback_query(F.data == "skip_broadcast_media")
async def skip_media_upload(callback: CallbackQuery, state: FSMContext):
    """Пропустить загрузку медиа"""
    try:
        await callback.message.edit_text(
            "👥 <b>Шаг 3 из 3: Выбор аудитории</b>\n\n"
            "Кому отправить рассылку?",
            reply_markup=broadcast_audience_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(BroadcastStates.selecting_audience)
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при пропуске медиа: {e}")
        await callback.answer("Произошла ошибка")


@router.callback_query(F.data.startswith("broadcast_audience:"))
async def select_audience(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Выбрать аудиторию и создать рассылку"""
    try:
        audience = callback.data.split(":")[1]
        data = await state.get_data()
        
        # Создаем рассылку в базе данных
        broadcast_service = BroadcastService(session)
        broadcast = await broadcast_service.create_broadcast(
            admin_id=callback.from_user.id,
            text=data.get('text'),
            media_type=data.get('media_type'),
            file_id=data.get('file_id')
        )
        
        if not broadcast:
            await callback.answer("❌ Ошибка при создании рассылки")
            return
        
        # Определяем название аудитории
        audience_names = {
            "all": "всем пользователям",
            "active": "активным пользователям", 
            "buyers": "покупателям"
        }
        audience_name = audience_names.get(audience, "выбранной аудитории")
        
        # Показываем подтверждение
        text = f"""
✅ <b>Рассылка готова к отправке!</b>

📝 <b>Текст:</b>
{data.get('text')[:200]}{'...' if len(data.get('text', '')) > 200 else ''}

📎 <b>Медиа:</b> {'Да' if data.get('media_type') else 'Нет'}

👥 <b>Аудитория:</b> {audience_name}

⚠️ <b>Внимание!</b> После отправки рассылку нельзя будет остановить.
"""

        await callback.message.edit_text(
            text,
            reply_markup=broadcast_confirm_keyboard(broadcast.id, audience),
            parse_mode="HTML"
        )
        await state.clear()
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при выборе аудитории: {e}")
        await callback.answer("❌ Ошибка при создании рассылки")


@router.callback_query(F.data.startswith("confirm_broadcast:"))
async def confirm_broadcast_send(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Подтвердить и отправить рассылку"""
    try:
        _, broadcast_id, audience = callback.data.split(":")
        broadcast_id = int(broadcast_id)
        
        # Отправляем рассылку через сервис
        broadcast_service = BroadcastService(session)
        
        # Получаем токен бота из конфигурации
        from config import settings
        bot_token = settings.telegram.bot_token
        
        success = await broadcast_service.send_broadcast(
            broadcast_id=broadcast_id,
            target_audience=audience,
            bot_token=bot_token
        )
        
        if success:
            await callback.message.edit_text(
                "✅ <b>Рассылка запущена!</b>\n\n",
                reply_markup=back_to_admin_keyboard(),
                parse_mode="HTML"
            )
            await callback.answer("✅ Рассылка запущена успешно!")
        else:
            await callback.answer("❌ Ошибка при запуске рассылки")

    except Exception as e:
        logger.error(f"Ошибка при подтверждении рассылки: {e}")
        await callback.answer("❌ Ошибка при отправке рассылки")


@router.callback_query(F.data == "admin_broadcasts_history")
async def show_broadcasts_history(callback: CallbackQuery, session: AsyncSession):
    """Показать историю рассылок"""
    try:
        broadcast_service = BroadcastService(session)
        broadcasts = await broadcast_service.get_broadcasts_history(limit=10)
        
        if not broadcasts:
            text = """
📋 <b>История рассылок</b>

📭 У вас пока нет рассылок.
Создайте первую рассылку, чтобы увидеть её здесь.
"""
            await callback.message.edit_text(
                text,
                reply_markup=back_to_admin_keyboard(),
                parse_mode="HTML"
            )
        else:
            text = "📋 <b>История рассылок</b>\n\nПоследние рассылки (нажмите для просмотра статистики):\n\n"
            
            await callback.message.edit_text(
                text,
                reply_markup=broadcast_history_keyboard(broadcasts),
                parse_mode="HTML"
            )
        
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении истории рассылок: {e}")
        await callback.answer("Ошибка при загрузке истории рассылок")


@router.callback_query(F.data.startswith("broadcast_stats:"))
async def show_broadcast_stats(callback: CallbackQuery, session: AsyncSession):
    """Показать статистику конкретной рассылки"""
    try:
        broadcast_id = int(callback.data.split(":")[1])
        
        broadcast_service = BroadcastService(session)
        stats = await broadcast_service.get_broadcast_statistics(broadcast_id)
        
        if not stats:
            await callback.answer("❌ Статистика не найдена")
            return
        
        # Формируем текст статистики
        status_emojis = {
            "pending": "⏳ Ожидает",
            "sending": "📤 Отправляется",
            "completed": "✅ Завершена",
            "failed": "❌ Ошибка",
            "cancelled": "🛑 Отменена"
        }
        
        status_text = status_emojis.get(stats['status'], stats['status'])
        
        text = f"""
📊 <b>Статистика рассылки</b>

📝 <b>Текст:</b>
{stats['text'][:150]}{'...' if len(stats['text']) > 150 else ''}

📈 <b>Статус:</b> {status_text}

👥 <b>Статистика доставки:</b>
• Всего получателей: {stats.get('total_users', 0)}
• Успешно доставлено: {stats.get('success_count', 0)}
• Не доставлено: {stats.get('failed_count', 0)}
• Процент успеха: {stats.get('success_rate', 0)}%

🕐 <b>Отправлено:</b> {stats.get('sent_at', 'Еще не отправлено')}
"""

        await callback.message.edit_text(
            text,
            reply_markup=broadcast_actions_keyboard(broadcast_id, stats['status']),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении статистики рассылки: {e}")
        await callback.answer("Ошибка при загрузке статистики")


@router.callback_query(F.data.startswith("cancel_broadcast:"))
async def cancel_broadcast(callback: CallbackQuery, session: AsyncSession):
    """Отменить рассылку"""
    try:
        broadcast_id = int(callback.data.split(":")[1])
        
        broadcast_service = BroadcastService(session)
        success = await broadcast_service.cancel_broadcast(broadcast_id)
        
        if success:
            await callback.answer("✅ Рассылка отменена")
            # Обновляем статистику
            await show_broadcast_stats(callback, session)
        else:
            await callback.answer("❌ Не удалось отменить рассылку")

    except Exception as e:
        logger.error(f"Ошибка при отмене рассылки: {e}")
        await callback.answer("Ошибка при отмене рассылки")


@router.callback_query(F.data.startswith("delete_broadcast:"))
async def delete_broadcast(callback: CallbackQuery, session: AsyncSession):
    """Удалить рассылку"""
    try:
        broadcast_id = int(callback.data.split(":")[1])
        
        broadcast_service = BroadcastService(session)
        success = await broadcast_service.delete_broadcast(broadcast_id)
        
        if success:
            await callback.answer("✅ Рассылка удалена")
            # Возвращаемся к истории рассылок
            await show_broadcasts_history(callback, session)
        else:
            await callback.answer("❌ Не удалось удалить рассылку")

    except Exception as e:
        logger.error(f"Ошибка при удалении рассылки: {e}")
        await callback.answer("Ошибка при удалении рассылки")


@router.callback_query(F.data == "admin_active_broadcasts")
async def show_active_broadcasts(callback: CallbackQuery, session: AsyncSession):
    """Показать активные рассылки"""
    try:
        broadcast_service = BroadcastService(session)
        active_broadcasts = await broadcast_service.get_active_broadcasts()
        
        if not active_broadcasts:
            text = """
⏸️ <b>Активные рассылки</b>

📭 Сейчас нет активных рассылок.
Все рассылки завершены или отменены.
"""
        else:
            text = "⏸️ <b>Активные рассылки</b>\n\nРассылки в процессе отправки:\n\n"
            
            for broadcast in active_broadcasts:
                status_icon = "📤" if broadcast.status == "sending" else "⏳"
                text += f"{status_icon} {broadcast.text[:40]}{'...' if len(broadcast.text) > 40 else ''}\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=back_to_admin_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении активных рассылок: {e}")
        await callback.answer("Ошибка при загрузке активных рассылок")


@router.callback_query(F.data == "admin_broadcast_stats")
async def show_general_broadcast_stats(callback: CallbackQuery, session: AsyncSession):
    """Показать общую статистику рассылок"""
    try:
        broadcast_service = BroadcastService(session)
        all_broadcasts = await broadcast_service.get_broadcasts_history(limit=100)
        
        if not all_broadcasts:
            text = """
📊 <b>Статистика рассылок</b>

📭 У вас пока нет рассылок для анализа.
"""
        else:
            # Подсчитываем статистику
            total_broadcasts = len(all_broadcasts)
            completed = len([b for b in all_broadcasts if b.status == "completed"])
            failed = len([b for b in all_broadcasts if b.status == "failed"])
            pending = len([b for b in all_broadcasts if b.status == "pending"])
            
            total_users = sum(b.total_users or 0 for b in all_broadcasts)
            total_success = sum(b.success_count or 0 for b in all_broadcasts)
            
            success_rate = (total_success / total_users * 100) if total_users > 0 else 0
            
            text = f"""
📊 <b>Общая статистика рассылок</b>

📈 <b>Всего рассылок:</b> {total_broadcasts}
✅ <b>Завершено:</b> {completed}
❌ <b>Неудачно:</b> {failed}
⏳ <b>В ожидании:</b> {pending}

👥 <b>Охват:</b>
• Всего отправок: {total_users}
• Успешно доставлено: {total_success}
• Общий процент успеха: {success_rate:.1f}%
"""
        
        await callback.message.edit_text(
            text,
            reply_markup=back_to_admin_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении статистики рассылок: {e}")
        await callback.answer("Ошибка при загрузке статистики")