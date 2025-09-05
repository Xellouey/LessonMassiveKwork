"""
Обработчики статистики для административной панели
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.statistics import StatisticsService
from keyboards.admin import admin_stats_keyboard, back_to_admin_keyboard
from middlewares.admin import AdminOnlyMiddleware

logger = logging.getLogger(__name__)
router = Router()
router.callback_query.middleware(AdminOnlyMiddleware())


@router.callback_query(F.data == "admin_stats")
async def show_stats_menu(callback: CallbackQuery):
    """Показать меню статистики"""
    try:
        text = """
📊 <b>Статистика системы</b>

Выберите тип статистики для просмотра:

📈 <b>Общая статистика</b> - основные показатели системы
💰 <b>Доходы</b> - статистика по доходам и продажам
# 👥 <b>Пользователи</b> - активность пользователей
📚 <b>Уроки</b> - статистика по урокам
📅 <b>За период</b> - статистика за выбранный период
📊 <b>Топ уроки</b> - самые популярные уроки
"""

        if callback.message:
            await callback.message.edit_text(
                text,
                reply_markup=admin_stats_keyboard(),
                parse_mode="HTML"
            )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при показе меню статистики: {e}")
        await callback.answer("Произошла ошибка при загрузке меню статистики")


@router.callback_query(F.data == "admin_general_stats")
async def show_general_stats(callback: CallbackQuery, session: AsyncSession):
    """Показать общую статистику"""
    try:
        stats_service = StatisticsService(session)
        stats = await stats_service.get_general_stats()

        if not stats:
            await callback.answer("Ошибка при получении статистики")
            return

        text = f"""
📈 <b>Общая статистика системы</b>

👥 <b>Пользователи:</b>
• Всего пользователей: {stats.get('total_users', 0)}
• Активных (30 дней): {stats.get('active_users', 0)}

📚 <b>Уроки:</b>
• Всего уроков: {stats.get('total_lessons', 0)}
• Активных уроков: {stats.get('active_lessons', 0)}

💰 <b>Продажи:</b>
• Всего покупок: {stats.get('total_purchases', 0)}
• Общий доход: ⭐ {stats.get('total_revenue', 0)}
• Доход на пользователя: ⭐ {stats.get('revenue_per_user', 0)}
"""

        await callback.message.edit_text(
            text,
            reply_markup=back_to_admin_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении общей статистики: {e}")
        await callback.answer("Произошла ошибка при загрузке статистики")


@router.callback_query(F.data == "admin_revenue_stats")
async def show_revenue_stats(callback: CallbackQuery, session: AsyncSession):
    """Показать статистику доходов"""
    try:
        stats_service = StatisticsService(session)
        stats = await stats_service.get_revenue_stats(30)  # За последние 30 дней

        if not stats:
            await callback.answer("Ошибка при получении статистики доходов")
            return

        text = f"""
💰 <b>Статистика доходов (30 дней)</b>

📊 <b>Основные показатели:</b>
• Доход за период: ⭐ {stats.get('period_revenue', 0)}
• Количество покупок: {stats.get('period_purchases', 0)}
• Средний чек: ⭐ {stats.get('avg_purchase', 0)}

📅 <b>Доходы по дням (последние 7 дней):</b>
"""

        # Добавляем ежедневную статистику
        daily_revenue = stats.get('daily_revenue', [])
        for day_data in daily_revenue:
            text += f"• {day_data.get('date', 'N/A')}: ⭐ {day_data.get('revenue', 0)}\n"

        await callback.message.edit_text(
            text,
            reply_markup=back_to_admin_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении статистики доходов: {e}")
        await callback.answer("Произошла ошибка при загрузке статистики доходов")


@router.callback_query(F.data == "admin_top_lessons")
async def show_top_lessons(callback: CallbackQuery, session: AsyncSession):
    """Показать топ уроков по продажам"""
    try:
        stats_service = StatisticsService(session)
        top_lessons = await stats_service.get_top_lessons(10)

        text = "📊 <b>Топ-10 уроков по продажам</b>\n\n"

        if not top_lessons:
            text += "📭 Пока нет данных о продажах уроков"
        else:
            for i, lesson in enumerate(top_lessons, 1):
                text += f"{i}. <b>{lesson.get('title', 'Без названия')}</b>\n"
                text += f"   💰 Цена: ⭐ {lesson.get('price', 0)}\n"
                text += f"   🛒 Продаж: {lesson.get('sales', 0)}\n"
                text += f"   💵 Доход: ⭐ {lesson.get('revenue', 0)}\n\n"

        await callback.message.edit_text(
            text,
            reply_markup=back_to_admin_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении топ уроков: {e}")
        await callback.answer("Произошла ошибка при загрузке топ уроков")


@router.callback_query(F.data == "admin_users_stats")
async def show_users_stats(callback: CallbackQuery, session: AsyncSession):
    """Показать статистику пользователей"""
    try:
        stats_service = StatisticsService(session)
        
        # Получаем статистику активности и конверсии
        activity_stats = await stats_service.get_user_activity_stats(7)
        conversion_stats = await stats_service.get_conversion_stats()

        text = f"""
👥 <b>Статистика пользователей</b>

📈 <b>Конверсия:</b>
• Всего пользователей: {conversion_stats.get('total_users', 0)}
• Покупателей: {conversion_stats.get('buyers', 0)}
• Конверсия в покупку: {conversion_stats.get('conversion_rate', 0)}%
• Покупок на покупателя: {conversion_stats.get('avg_purchases_per_buyer', 0)}

📅 <b>Активность (последние 7 дней):</b>
"""

        # Добавляем ежедневную активность
        for day_data in activity_stats:
            text += f"• {day_data.get('date', 'N/A')}: {day_data.get('unique_users', 0)} польз., {day_data.get('total_actions', 0)} действий\n"

        await callback.message.edit_text(
            text,
            reply_markup=back_to_admin_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении статистики пользователей: {e}")
        await callback.answer("Произошла ошибка при загрузке статистики пользователей")


@router.callback_query(F.data == "admin_lessons_statistics")
async def show_lessons_statistics(callback: CallbackQuery, session: AsyncSession):
    """Показать статистику по урокам"""
    try:
        stats_service = StatisticsService(session)
        general_stats = await stats_service.get_general_stats()
        top_lessons = await stats_service.get_top_lessons(5)

        text = f"""
📚 <b>Статистика по урокам</b>

📊 <b>Общие показатели:</b>
• Всего уроков: {general_stats.get('total_lessons', 0)}
• Активных уроков: {general_stats.get('active_lessons', 0)}
• Всего продаж: {general_stats.get('total_purchases', 0)}

🏆 <b>Топ-5 уроков по продажам:</b>
"""

        if not top_lessons:
            text += "📭 Пока нет данных о продажах"
        else:
            for i, lesson in enumerate(top_lessons, 1):
                text += f"{i}. {lesson.get('title', 'Без названия')} - {lesson.get('sales', 0)} продаж\n"

        await callback.message.edit_text(
            text,
            reply_markup=back_to_admin_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении статистики уроков: {e}")
        await callback.answer("Произошла ошибка при загрузке статистики уроков")


@router.callback_query(F.data == "admin_period_stats")
async def show_period_stats(callback: CallbackQuery, session: AsyncSession):
    """Показать статистику за разные периоды"""
    try:
        stats_service = StatisticsService(session)
        
        # Получаем статистику за разные периоды
        stats_7d = await stats_service.get_revenue_stats(7)
        stats_30d = await stats_service.get_revenue_stats(30)
        stats_90d = await stats_service.get_revenue_stats(90)

        text = f"""
📅 <b>Статистика по периодам</b>

📊 <b>7 дней:</b>
• Доход: ⭐ {stats_7d.get('period_revenue', 0)}
• Покупок: {stats_7d.get('period_purchases', 0)}
• Средний чек: ⭐ {stats_7d.get('avg_purchase', 0)}

📊 <b>30 дней:</b>
• Доход: ⭐ {stats_30d.get('period_revenue', 0)}
• Покупок: {stats_30d.get('period_purchases', 0)}
• Средний чек: ⭐ {stats_30d.get('avg_purchase', 0)}

📊 <b>90 дней:</b>
• Доход: ⭐ {stats_90d.get('period_revenue', 0)}
• Покупок: {stats_90d.get('period_purchases', 0)}
• Средний чек: ⭐ {stats_90d.get('avg_purchase', 0)}
"""

        await callback.message.edit_text(
            text,
            reply_markup=back_to_admin_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении статистики по периодам: {e}")
        await callback.answer("Произошла ошибка при загрузке статистики по периодам")


