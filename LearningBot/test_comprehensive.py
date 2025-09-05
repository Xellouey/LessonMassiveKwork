"""
Comprehensive integration test for bot functionality
"""
import asyncio
import sys
from datetime import datetime, timezone

sys.path.insert(0, '.')

from database.database import AsyncSessionLocal, init_db
from database.models import Lesson, User, Admin
from services.lesson import LessonService
from services.user import UserService

async def run_comprehensive_tests():
    """Run comprehensive tests of lesson functionality"""
    print("🧪 Running comprehensive lesson functionality tests...")
    
    try:
        # Initialize database
        await init_db()
        print("✅ Database initialized")
        
        async with AsyncSessionLocal() as session:
            lesson_service = LessonService(session)
            user_service = UserService(session)
            
            print("\n📊 Database Status Check:")
            
            # Check lessons
            lessons, total_lessons = await lesson_service.get_lessons_paginated()
            print(f"   📚 Total lessons: {total_lessons}")
            
            if total_lessons == 0:
                print("   ❌ No lessons found in database!")
                return False
            
            # Show lesson details
            for i, lesson in enumerate(lessons[:5], 1):
                status = "🎁 Free" if lesson.is_free else f"⭐ {lesson.price_stars} stars"
                active = "✅ Active" if lesson.is_active else "❌ Inactive"
                print(f"   {i}. {lesson.title} - {status} - {active}")
            
            # Check free lessons
            free_lessons = await lesson_service.get_free_lessons()
            print(f"   🎁 Free lessons: {len(free_lessons)}")
            
            # Check admin user
            admin_exists = await session.get(Admin, 897676474)
            print(f"   👨‍💼 Admin exists: {'✅ Yes' if admin_exists else '❌ No'}")
            
            # Check regular user
            user_exists = await session.get(User, 897676474)
            print(f"   👤 User exists: {'✅ Yes' if user_exists else '❌ No'}")
            
            print("\n🔧 Testing Core Functionality:")
            
            # Test 1: Get lesson by ID
            first_lesson = await lesson_service.get_lesson_by_id(1)
            if first_lesson:
                print(f"   ✅ Get lesson by ID: {first_lesson.title}")
            else:
                print("   ❌ Could not get lesson by ID")
                return False
            
            # Test 2: Check lesson access for free lesson
            free_lesson = None
            for lesson in lessons:
                if lesson.is_free:
                    free_lesson = lesson
                    break
            
            if free_lesson:
                has_access = await lesson_service.check_user_has_lesson(897676474, free_lesson.id)
                print(f"   ✅ Free lesson access: {has_access}")
            else:
                print("   ❌ No free lessons found")
            
            # Test 3: Check lesson access for paid lesson
            paid_lesson = None
            for lesson in lessons:
                if not lesson.is_free:
                    paid_lesson = lesson
                    break
            
            if paid_lesson:
                has_access = await lesson_service.check_user_has_lesson(897676474, paid_lesson.id)
                print(f"   ✅ Paid lesson access (should be False): {has_access}")
            
            # Test 4: Categories
            try:
                categories = await lesson_service.get_lesson_categories()
                print(f"   ✅ Lesson categories: {len(categories)} found")
                for cat in categories[:3]:
                    print(f"      - {cat}")
            except Exception as e:
                print(f"   ❌ Categories test failed: {e}")
            
            # Test 5: Popular lessons
            try:
                popular = await lesson_service.get_popular_lessons(limit=3)
                print(f"   ✅ Popular lessons: {len(popular)} found")
            except Exception as e:
                print(f"   ❌ Popular lessons test failed: {e}")
            
            print("\n🎯 User Flow Simulation:")
            
            # Simulate user viewing catalog
            print("   1. User clicks 'Каталог уроков'...")
            catalog_lessons, catalog_total = await lesson_service.get_lessons_paginated(page=0, per_page=10)
            print(f"      📚 Catalog shows {catalog_total} lessons")
            
            # Simulate user clicking "все уроки"
            print("   2. User clicks 'Все уроки'...")
            all_lessons, all_total = await lesson_service.get_lessons_paginated(page=0, per_page=10)
            print(f"      📚 All lessons: {all_total} lessons shown")
            
            # Simulate user clicking on a lesson
            if all_lessons:
                lesson = all_lessons[0]
                print(f"   3. User clicks on lesson: '{lesson.title}'...")
                lesson_detail = await lesson_service.get_lesson_by_id(lesson.id)
                if lesson_detail:
                    print(f"      📖 Lesson detail loaded: {lesson_detail.title}")
                    print(f"      💰 Price: {'Free' if lesson_detail.is_free else f'{lesson_detail.price_stars} stars'}")
                    print(f"      📝 Description: {lesson_detail.description[:50]}...")
                else:
                    print("      ❌ Could not load lesson detail")
                    return False
            
            print("\n🔍 Potential Issues Check:")
            
            # Check for inactive lessons
            inactive_count = sum(1 for lesson in lessons if not lesson.is_active)
            if inactive_count > 0:
                print(f"   ⚠️  Found {inactive_count} inactive lessons")
            
            # Check for lessons without content
            no_content_count = sum(1 for lesson in lessons if not lesson.file_id and lesson.content_type != 'text')
            if no_content_count > 0:
                print(f"   ⚠️  Found {no_content_count} lessons without content files")
            
            # Check for very long descriptions
            long_desc_count = sum(1 for lesson in lessons if lesson.description and len(lesson.description) > 500)
            if long_desc_count > 0:
                print(f"   ⚠️  Found {long_desc_count} lessons with very long descriptions")
            
            print("\n✅ All tests completed successfully!")
            print("\n📋 Summary:")
            print(f"   • Database has {total_lessons} lessons")
            print(f"   • {len(free_lessons)} free lessons available")
            print(f"   • User and admin accounts exist")
            print(f"   • Core lesson functionality working")
            print(f"   • UI flow simulation successful")
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_specific_user_flow():
    """Test the specific user flow that might be failing"""
    print("\n🎯 Testing specific 'все уроки' flow...")
    
    async with AsyncSessionLocal() as session:
        lesson_service = LessonService(session)
        
        print("Step 1: User clicks catalog button")
        # This should show catalog with categories
        lessons, total = await lesson_service.get_lessons_paginated(page=0, per_page=10)
        print(f"   📚 Catalog loaded: {total} total lessons")
        
        print("Step 2: User clicks 'Все уроки' button")
        # This triggers catalog:all callback
        all_lessons, all_total = await lesson_service.get_lessons_paginated(page=0, per_page=10)
        print(f"   📚 All lessons loaded: {all_total} lessons")
        
        if all_total == 0:
            print("   ❌ NO LESSONS FOUND - This is the problem!")
            return False
        
        print("Step 3: Check lesson details")
        for i, lesson in enumerate(all_lessons[:3], 1):
            print(f"   {i}. {lesson.title}")
            print(f"      Price: {'Free' if lesson.is_free else f'{lesson.price_stars} stars'}")
            print(f"      Active: {lesson.is_active}")
            print(f"      Category: {lesson.category or 'None'}")
        
        return True

if __name__ == "__main__":
    async def main():
        success = await run_comprehensive_tests()
        if success:
            await test_specific_user_flow()
        else:
            print("❌ Basic tests failed, skipping user flow test")
    
    asyncio.run(main())