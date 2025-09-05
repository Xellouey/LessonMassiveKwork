"""
Test lesson functionality end-to-end
"""
import asyncio
import sys
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Add current directory to path
sys.path.insert(0, '.')

from database.database import Base
from database.models import User, Lesson, Purchase, Admin
from services.user import UserService
from services.lesson import LessonService

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

async def test_lesson_functionality():
    """Test complete lesson functionality"""
    print("🧪 Testing lesson functionality...")
    
    # Create test database engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = async_sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        # Create test user
        user = User(
            user_id=897676474,  # User's actual ID
            username="dmitriy_mityuk",
            full_name="Дмитрий Митюк",
            language="ru",
            registration_date=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc),
            is_active=True
        )
        session.add(user)
        
        # Create test admin
        admin = Admin(
            user_id=897676474,
            username="dmitriy_mityuk",
            permissions="all",
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        session.add(admin)
        
        # Create test lessons
        lessons = [
            Lesson(
                title="Free Python Lesson",
                description="Learn Python basics for free",
                price_stars=0,
                content_type="video",
                file_id="test_video_123",
                duration=600,
                is_active=True,
                is_free=True,
                category="Programming",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                views_count=0
            ),
            Lesson(
                title="Advanced JavaScript",
                description="Advanced JavaScript concepts and patterns",
                price_stars=100,
                content_type="video",
                file_id="test_video_456",
                duration=900,
                is_active=True,
                is_free=False,
                category="Programming",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                views_count=5
            ),
            Lesson(
                title="Database Design",
                description="How to design efficient databases",
                price_stars=150,
                content_type="document",
                file_id="test_doc_789",
                duration=1200,
                is_active=True,
                is_free=False,
                category="Database",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                views_count=3
            )
        ]
        
        for lesson in lessons:
            session.add(lesson)
        
        await session.commit()
        
        # Test lesson service functionality
        print("  ✅ 1. Testing LessonService...")
        lesson_service = LessonService(session)
        
        # Test get all lessons
        all_lessons, total_count = await lesson_service.get_lessons_paginated()
        print(f"     📚 Total lessons: {total_count}")
        print(f"     📚 Retrieved lessons: {len(all_lessons)}")
        
        # Test get free lessons
        free_lessons = await lesson_service.get_free_lessons()
        print(f"     🎁 Free lessons: {len(free_lessons)}")
        
        # Test get specific lesson
        first_lesson = await lesson_service.get_lesson_by_id(1)
        if first_lesson:
            print(f"     📖 First lesson: {first_lesson.title}")
        else:
            print("     ❌ Could not retrieve first lesson")
        
        # Test user access to lessons
        print("  ✅ 2. Testing user lesson access...")
        user_service = UserService(session)
        
        # Check access to free lesson
        has_free_access = await lesson_service.check_user_has_lesson(897676474, 1)
        print(f"     🎁 Access to free lesson: {has_free_access}")
        
        # Check access to paid lesson (should be False)
        has_paid_access = await lesson_service.check_user_has_lesson(897676474, 2)
        print(f"     💰 Access to paid lesson: {has_paid_access}")
        
        # Test admin lessons functionality
        print("  ✅ 3. Testing admin lesson management...")
        admin_lessons, admin_total = await lesson_service.get_lessons_paginated(include_inactive=True)
        print(f"     👨‍💼 Admin can see {admin_total} lessons (including inactive)")
        
        print("  ✅ 4. Testing database integrity...")
        # Check if lessons have proper content
        for lesson in all_lessons:
            if not lesson.title or not lesson.description:
                print(f"     ❌ Lesson {lesson.id} missing title or description")
            elif not lesson.content_type:
                print(f"     ❌ Lesson {lesson.id} missing content type")
            else:
                print(f"     ✅ Lesson {lesson.id}: {lesson.title} ({lesson.content_type})")
        
    await engine.dispose()
    print("🎉 Lesson functionality test completed!")

if __name__ == "__main__":
    asyncio.run(test_lesson_functionality())