"""
Скрипт для добавления тестовых уроков в базу данных
"""
import asyncio
import sys
sys.path.insert(0, '.')

from datetime import datetime, timezone
from database.database import init_db, get_db_session
from database.models import Lesson

async def add_sample_lessons():
    """Добавление тестовых уроков"""
    print("📚 Добавление тестовых уроков...")
    
    # Инициализируем базу данных
    await init_db()
    
    async for session in get_db_session():
        # Проверяем, есть ли уже уроки
        from sqlalchemy import select, func
        count_result = await session.execute(select(func.count(Lesson.id)))
        lesson_count = count_result.scalar()
        
        if lesson_count > 0:
            print(f"✅ Уроки уже существуют в базе ({lesson_count} шт.)")
            return
        
        # Создаем тестовые уроки с тематикой нейросетей и ИИ
        lessons = [
            Lesson(
                title="🎁 Бесплатный урок: Что такое ИИ?",
                description="Бесплатный лид-магнит урок о мире искусственного интеллекта. Узнайте, как ИИ уже изменил нашу жизнь и какие возможности открывает для вашей карьеры!",
                price_stars=0,
                content_type="text",
                file_id="free_ai_intro",
                duration=300,
                is_active=True,
                is_free=True,
                category="Основы ИИ",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                views_count=0
            ),
            Lesson(
                title="🤖 Машинное обучение для новичков",
                description="Познакомьтесь с основами машинного обучения без сложной математики. Узнайте о supervised, unsupervised и reinforcement learning на простых примерах.",
                price_stars=50,
                content_type="text",
                file_id="ml_basics",
                duration=1200,
                is_active=True,
                is_free=False,
                category="Машинное обучение",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                views_count=0
            ),
            Lesson(
                title="🚀 Создание AI-стартапа: от идеи до MVP",
                description="Пошаговый алгоритм запуска стартапа в сфере ИИ. Как найти проблему, создать решение на базе нейросетей и привлечь первых пользователей. Реальные кейсы успешных AI-компаний.",
                price_stars=150,
                content_type="text",
                file_id="ai_startup_guide",
                duration=2400,
                is_active=True,
                is_free=False,
                category="AI-Бизнес",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                views_count=0
            ),
            Lesson(
                title="⭐ Prompt Engineering: искусство общения с ИИ",
                description="Узнайте, как получать максимум от ChatGPT, Claude и других языковых моделей. Изучите техники написания эффективных промптов для решения бизнес-задач.",
                price_stars=75,
                content_type="text",
                file_id="prompt_engineering",
                duration=900,
                is_active=True,
                is_free=False,
                category="Промпт-инжиниринг",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                views_count=0
            ),
            Lesson(
                title="💎 Монетизация ИИ: как зарабатывать на нейросетях",
                description="Стратегии заработка с помощью искусственного интеллекта. Создание AI-сервисов, автоматизация процессов, NFT с ИИ. Как выйти на доходы от $1000 до $10000 в месяц.",
                price_stars=250,
                content_type="text", 
                file_id="ai_monetization",
                duration=3600,
                is_active=True,
                is_free=False,
                category="AI-Заработок",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                views_count=0
            )
        ]
        
        # Добавляем уроки в сессию
        session.add_all(lessons)
        await session.commit()
        
        print(f"✅ Добавлено {len(lessons)} тестовых уроков:")
        for lesson in lessons:
            price = "Бесплатно" if lesson.is_free else f"{lesson.price_stars} ⭐"
            print(f"   • {lesson.title} - {price}")
        
        break  # Выходим из цикла after first session

if __name__ == "__main__":
    print("📚 НАСТРОЙКА КОНТЕНТА БОТА...")
    print()
    
    try:
        asyncio.run(add_sample_lessons())
        print()
        print("🎉 Готово! Контент добавлен в базу данных!")
        print("💡 Теперь можно запускать бота: python bot.py")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()