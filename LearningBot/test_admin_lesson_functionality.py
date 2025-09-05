#!/usr/bin/env python3
"""
Comprehensive test for admin lesson functionality
This test identifies gaps in CRUD operations and interface issues
"""
import asyncio
import logging
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.database import async_session
from services.lesson import LessonService
from database.models import Lesson, Admin
from keyboards.admin import (
    lessons_management_keyboard,
    lesson_edit_keyboard,
    lessons_list_keyboard,
    confirm_action_keyboard
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdminLessonFunctionalityTest:
    """Test suite for admin lesson functionality"""
    
    def __init__(self):
        self.issues_found = []
        self.missing_handlers = []
        self.missing_service_methods = []
        self.interface_duplicates = []
        
    async def run_all_tests(self):
        """Run all functionality tests"""
        print("\n" + "="*60)
        print("🧪 ADMIN LESSON FUNCTIONALITY TEST")
        print("="*60)
        
        await self.test_service_layer_completeness()
        await self.test_handler_completeness()
        await self.test_interface_consistency()
        await self.test_create_functionality()
        await self.test_read_functionality()
        await self.test_update_functionality()
        await self.test_delete_functionality()
        
        self.generate_report()
        
    async def test_service_layer_completeness(self):
        """Test if all CRUD operations are available in service layer"""
        print("\n📋 Testing Service Layer Completeness...")
        
        async with async_session() as session:
            service = LessonService(session)
            
            # Test required methods exist
            required_methods = [
                # READ operations
                'get_lesson_by_id',
                'get_lessons_paginated',
                'get_free_lessons',
                'search_lessons',
                'get_lessons_by_category',
                'get_popular_lessons',
                'get_lesson_categories',
                
                # UPDATE operations  
                'update_lesson_title',
                'update_lesson_description',
                'update_lesson_price',
                'update_lesson_category',
                'update_lesson_status',
                'update_lesson_media',
                'increment_lesson_views',
                
                # Missing DELETE operations
                'delete_lesson',
                'soft_delete_lesson',
                'can_delete_lesson',
                'get_lesson_dependencies'
            ]
            
            for method in required_methods:
                if not hasattr(service, method):
                    self.missing_service_methods.append(method)
                    print(f"❌ Missing service method: {method}")
                else:
                    print(f"✅ Service method exists: {method}")
                    
    async def test_handler_completeness(self):
        """Test if all CRUD handlers are implemented"""
        print("\n🎯 Testing Handler Completeness...")
        
        # Import handlers to check what exists
        try:
            from handlers.admin import lessons
            
            # Required handlers for CRUD operations
            required_handlers = [
                # CREATE handlers
                'start_lesson_creation',
                'process_lesson_creation', 
                'select_lesson_type',
                'process_lesson_media',
                'finalize_lesson_creation',
                
                # READ handlers
                'show_lessons_list',
                'navigate_lessons_pages',
                'edit_lesson_menu',
                
                # UPDATE handlers
                'edit_lesson_title',
                'edit_lesson_description', 
                'edit_lesson_price',
                'process_lesson_description_edit',
                'process_lesson_price_edit',
                'toggle_lesson_status',
                'toggle_lesson_free_status',
                
                # DELETE handlers (likely missing)
                'delete_lesson_handler',
                'confirm_lesson_deletion',
                'process_lesson_deletion'
            ]
            
            for handler in required_handlers:
                if not hasattr(lessons, handler):
                    self.missing_handlers.append(handler)
                    print(f"❌ Missing handler: {handler}")
                else:
                    print(f"✅ Handler exists: {handler}")
                    
        except Exception as e:
            self.issues_found.append(f"Error importing lesson handlers: {e}")
            print(f"❌ Error importing handlers: {e}")
            
    async def test_interface_consistency(self):
        """Test for interface duplicates and inconsistencies"""
        print("\n🖥️ Testing Interface Consistency...")
        
        # Check for duplicate buttons across different keyboards
        lesson_mgmt_kb = lessons_management_keyboard()
        
        buttons_in_mgmt = []
        for row in lesson_mgmt_kb.inline_keyboard:
            for button in row:
                buttons_in_mgmt.append(button.text)
                
        print(f"📋 Lesson management keyboard buttons: {buttons_in_mgmt}")
        
        # Check if lesson edit keyboard has delete functionality
        try:
            edit_kb = lesson_edit_keyboard(1)  # Test with ID 1
            edit_buttons = []
            for row in edit_kb.inline_keyboard:
                for button in row:
                    edit_buttons.append((button.text, button.callback_data))
                    
            print(f"✏️ Lesson edit keyboard buttons:")
            for text, data in edit_buttons:
                print(f"   - {text}: {data}")
                
            # Check for delete functionality in edit keyboard
            has_delete = any("Удалить" in text for text, _ in edit_buttons)
            if has_delete:
                print("✅ Delete button found in lesson edit keyboard")
            else:
                self.interface_duplicates.append("Missing delete button in lesson edit keyboard")
                print("❌ Delete button missing in lesson edit keyboard")
                
        except Exception as e:
            self.issues_found.append(f"Error testing lesson edit keyboard: {e}")
            print(f"❌ Error testing lesson edit keyboard: {e}")
            
    async def test_create_functionality(self):
        """Test lesson creation functionality"""
        print("\n➕ Testing CREATE Functionality...")
        
        async with async_session() as session:
            try:
                service = LessonService(session)
                
                # Test basic lesson creation via direct DB insert (service layer test)
                test_lesson = Lesson(
                    title="Test Lesson - Delete Me",
                    description="This is a test lesson for functionality testing",
                    price_stars=100,
                    category="Test Category", 
                    content_type="text",
                    is_free=False,
                    is_active=True,
                    views_count=0
                )
                
                session.add(test_lesson)
                await session.commit()
                await session.refresh(test_lesson)
                
                print(f"✅ Successfully created test lesson with ID: {test_lesson.id}")
                
                # Store ID for cleanup
                self.test_lesson_id = test_lesson.id
                
            except Exception as e:
                self.issues_found.append(f"CREATE functionality error: {e}")
                print(f"❌ CREATE functionality error: {e}")
                
    async def test_read_functionality(self):
        """Test lesson reading functionality"""
        print("\n📖 Testing READ Functionality...")
        
        async with async_session() as session:
            try:
                service = LessonService(session)
                
                # Test get_lesson_by_id
                if hasattr(self, 'test_lesson_id'):
                    lesson = await service.get_lesson_by_id(self.test_lesson_id, include_inactive=True)
                    if lesson:
                        print(f"✅ Successfully retrieved lesson: {lesson.title}")
                    else:
                        self.issues_found.append("Could not retrieve created lesson")
                        print("❌ Could not retrieve created lesson")
                
                # Test get_lessons_paginated
                lessons, count = await service.get_lessons_paginated(page=0, per_page=5, include_inactive=True)
                print(f"✅ Retrieved {len(lessons)} lessons, total count: {count}")
                
                # Test search functionality
                search_lessons, search_count = await service.search_lessons("Test", page=0, per_page=5)
                print(f"✅ Search found {len(search_lessons)} lessons")
                
            except Exception as e:
                self.issues_found.append(f"READ functionality error: {e}")
                print(f"❌ READ functionality error: {e}")
                
    async def test_update_functionality(self):
        """Test lesson update functionality"""
        print("\n✏️ Testing UPDATE Functionality...")
        
        async with async_session() as session:
            try:
                service = LessonService(session)
                
                if not hasattr(self, 'test_lesson_id'):
                    print("⚠️ No test lesson available for UPDATE tests")
                    return
                    
                lesson_id = self.test_lesson_id
                
                # Test update title
                success = await service.update_lesson_title(lesson_id, "Updated Test Title")
                if success:
                    print("✅ Successfully updated lesson title")
                else:
                    self.issues_found.append("Failed to update lesson title")
                    print("❌ Failed to update lesson title")
                
                # Test update description
                success = await service.update_lesson_description(lesson_id, "Updated test description")
                if success:
                    print("✅ Successfully updated lesson description")
                else:
                    self.issues_found.append("Failed to update lesson description")
                    print("❌ Failed to update lesson description")
                
                # Test update price
                success = await service.update_lesson_price(lesson_id, 200)
                if success:
                    print("✅ Successfully updated lesson price")
                else:
                    self.issues_found.append("Failed to update lesson price")
                    print("❌ Failed to update lesson price")
                
                # Test status toggle
                success = await service.update_lesson_status(lesson_id, False)
                if success:
                    print("✅ Successfully updated lesson status")
                else:
                    self.issues_found.append("Failed to update lesson status")
                    print("❌ Failed to update lesson status")
                    
            except Exception as e:
                self.issues_found.append(f"UPDATE functionality error: {e}")
                print(f"❌ UPDATE functionality error: {e}")
                
    async def test_delete_functionality(self):
        """Test lesson delete functionality"""
        print("\n🗑️ Testing DELETE Functionality...")
        
        async with async_session() as session:
            try:
                service = LessonService(session)
                
                if not hasattr(self, 'test_lesson_id'):
                    print("⚠️ No test lesson available for DELETE tests")
                    return
                
                lesson_id = self.test_lesson_id
                
                # Check if delete methods exist
                if hasattr(service, 'delete_lesson'):
                    try:
                        success = await service.delete_lesson(lesson_id)
                        if success:
                            print("✅ Successfully deleted lesson (hard delete)")
                        else:
                            print("❌ Failed to delete lesson")
                    except Exception as e:
                        print(f"❌ Error in delete_lesson method: {e}")
                else:
                    self.missing_service_methods.append('delete_lesson')
                    print("❌ delete_lesson method not found in service")
                    
                # Test soft delete via status update (workaround)
                try:
                    success = await service.update_lesson_status(lesson_id, False)
                    if success:
                        print("✅ Successfully soft-deleted lesson via status update")
                        
                        # Verify lesson is now inactive
                        lesson = await service.get_lesson_by_id(lesson_id, include_inactive=True)
                        if lesson and not lesson.is_active:
                            print("✅ Lesson correctly marked as inactive")
                        else:
                            print("❌ Lesson status not properly updated")
                    else:
                        print("❌ Failed to soft-delete lesson")
                        
                except Exception as e:
                    print(f"❌ Error in soft delete: {e}")
                    
            except Exception as e:
                self.issues_found.append(f"DELETE functionality error: {e}")
                print(f"❌ DELETE functionality error: {e}")
                
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("📊 FUNCTIONALITY TEST REPORT")
        print("="*60)
        
        print(f"\n🚨 Issues Found: {len(self.issues_found)}")
        for issue in self.issues_found:
            print(f"   • {issue}")
            
        print(f"\n❌ Missing Service Methods: {len(self.missing_service_methods)}")
        for method in self.missing_service_methods:
            print(f"   • {method}")
            
        print(f"\n🎯 Missing Handlers: {len(self.missing_handlers)}")  
        for handler in self.missing_handlers:
            print(f"   • {handler}")
            
        print(f"\n🖥️ Interface Issues: {len(self.interface_duplicates)}")
        for issue in self.interface_duplicates:
            print(f"   • {issue}")
            
        print("\n📋 SUMMARY OF REQUIRED FIXES:")
        print("="*40)
        
        if self.missing_service_methods:
            print("\n🔧 SERVICE LAYER FIXES NEEDED:")
            print("   1. Implement delete_lesson() method")
            print("   2. Implement soft_delete_lesson() method") 
            print("   3. Implement can_delete_lesson() validation method")
            print("   4. Implement get_lesson_dependencies() method")
            
        if self.missing_handlers:
            print("\n🎯 HANDLER LAYER FIXES NEEDED:")
            print("   1. Implement delete lesson callback handlers")
            print("   2. Implement deletion confirmation handlers")
            print("   3. Add proper FSM state transitions for deletion")
            
        print("\n🖥️ INTERFACE CONSOLIDATION NEEDED:")
        print("   1. Unify lesson management into single interface")
        print("   2. Remove duplicate buttons across different menus")
        print("   3. Create comprehensive lesson operations hub")
        print("   4. Implement contextual action menus")
        
        print("\n✅ NEXT STEPS:")
        print("   1. Fix missing delete functionality")
        print("   2. Consolidate lesson management interface")
        print("   3. Create comprehensive test suite")
        print("   4. Validate all CRUD operations work properly")
        
        return {
            'issues_found': self.issues_found,
            'missing_service_methods': self.missing_service_methods,
            'missing_handlers': self.missing_handlers,
            'interface_duplicates': self.interface_duplicates
        }

async def main():
    """Run the comprehensive test"""
    test = AdminLessonFunctionalityTest()
    await test.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())