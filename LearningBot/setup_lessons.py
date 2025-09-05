"""
Database setup and lesson data initialization
"""
import asyncio
import sys
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, '.')

from database.database import AsyncSessionLocal, init_db
from database.models import Lesson, User, Admin
from services.lesson import LessonService

async def setup_test_lessons():
    """Setup test lessons for the bot"""
    print("🔧 Setting up test lessons for the bot...")
    
    try:
        # Initialize database
        await init_db()
        print("✅ Database initialized")
        
        async with AsyncSessionLocal() as session:
            lesson_service = LessonService(session)
            
            # Check if lessons already exist
            existing_lessons, total_count = await lesson_service.get_lessons_paginated()
            
            if total_count > 0:
                print(f"✅ Found {total_count} existing lessons in database")
                for lesson in existing_lessons:
                    print(f"   📚 {lesson.title} - {'🎁 Free' if lesson.is_free else f'⭐ {lesson.price_stars} stars'}")
                return
            
            print("📝 No lessons found. Creating test lessons...")
            
            # Create test lessons with neural network theme
            test_lessons = [
                Lesson(
                    title="🎁 Бесплатный урок - Введение в ИИ",
                    description="Добро пожаловать в мир искусственного интеллекта! Этот урок познакомит вас с основными понятиями ИИ, машинного обучения и нейронных сетей. Узнайте, как ИИ меняет наш мир и как вы можете стать частью этой революции.",
                    price_stars=0,
                    content_type="video",
                    file_id=None,  # Will be set when admin uploads content
                    duration=300,  # 5 minutes
                    is_active=True,
                    is_free=True,
                    category="Основы ИИ",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    views_count=0
                ),
                Lesson(
                    title="🧠 Нейронные сети с нуля",
                    description="Погрузитесь в мир нейронных сетей! Изучите архитектуру нейронов, функции активации, обратное распространение ошибки. Создайте свою первую нейронную сеть на Python с библиотекой TensorFlow.",
                    price_stars=75,
                    content_type="video",
                    file_id=None,
                    duration=2700,  # 45 minutes
                    is_active=True,
                    is_free=False,
                    category="Нейронные сети",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    views_count=0
                ),
                Lesson(
                    title="🎨 Генеративные модели: от GAN до Diffusion",
                    description="Освойте искусство создания изображений с помощью ИИ! Изучите архитектуры GAN, VAE, Diffusion Models. Научитесь создавать уникальные изображения, от портретов до произведений искусства.",
                    price_stars=150,
                    content_type="video",
                    file_id=None,
                    duration=3600,  # 60 minutes
                    is_active=True,
                    is_free=False,
                    category="Генеративный ИИ",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    views_count=0
                ),
                Lesson(
                    title="💬 ChatGPT и языковые модели",
                    description="Раскройте потенциал больших языковых моделей! Изучите архитектуру Transformer, методы fine-tuning, prompt engineering. Создайте собственного чат-бота на базе современных LLM.",
                    price_stars=200,
                    content_type="document",
                    file_id=None,
                    duration=4200,  # 70 minutes
                    is_active=True,
                    is_free=False,
                    category="Языковые модели",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    views_count=0
                ),
                Lesson(
                    title="🚀 Computer Vision: анализ изображений",
                    description="Научите компьютер видеть! Освойте сверточные нейронные сети (CNN), обнаружение объектов, сегментацию изображений. Создайте систему распознавания лиц и анализа медицинских снимков.",
                    price_stars=175,
                    content_type="photo",
                    file_id=None,
                    duration=3300,  # 55 minutes
                    is_active=True,
                    is_free=False,
                    category="Computer Vision",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    views_count=0
                )
            ]
            
            # Add lessons to session
            for lesson in test_lessons:
                session.add(lesson)
            
            await session.commit()
            print(f"✅ Created {len(test_lessons)} test lessons")
            
            # Verify lessons were created
            created_lessons, total = await lesson_service.get_lessons_paginated()
            print(f"✅ Verification: {total} lessons now in database")
            
            for lesson in created_lessons:
                status = "🎁 Free" if lesson.is_free else f"⭐ {lesson.price_stars} stars"
                print(f"   📚 {lesson.title} - {status}")
            
    except Exception as e:
        print(f"❌ Error setting up lessons: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(setup_test_lessons())