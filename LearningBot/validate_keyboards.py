"""
Simple validation script to confirm statistics buttons are commented out for users
"""
import sys
sys.path.insert(0, '.')

from keyboards.user import profile_menu_keyboard, lesson_controls_keyboard
from keyboards.admin import admin_main_menu_keyboard, admin_stats_keyboard

def validate_user_keyboards():
    """Validate that user keyboards don't have statistics buttons"""
    print("🔍 Validating User Keyboards...")
    
    # Test profile menu
    profile_kb = profile_menu_keyboard()
    profile_text = str(profile_kb.inline_keyboard)
    
    print("   Profile Menu:")
    if "Статистика" not in profile_text and "my_stats" not in profile_text:
        print("     ✅ Statistics button successfully removed")
    else:
        print("     ❌ Statistics button still present")
        return False
    
    # Test lesson controls
    lesson_kb = lesson_controls_keyboard(lesson_id=1, has_access=True)
    lesson_text = str(lesson_kb.inline_keyboard)
    
    print("   Lesson Controls:")
    if "Статистика" not in lesson_text and "lesson_stats" not in lesson_text:
        print("     ✅ Statistics button successfully removed")
    else:
        print("     ❌ Statistics button still present")
        return False
    
    return True

def validate_admin_keyboards():
    """Validate that admin keyboards still have statistics buttons"""
    print("\n🔍 Validating Admin Keyboards...")
    
    # Test admin main menu
    admin_main_kb = admin_main_menu_keyboard()
    admin_main_text = str(admin_main_kb.inline_keyboard)
    
    print("   Admin Main Menu:")
    if "Статистика" in admin_main_text and "admin_stats" in admin_main_text:
        print("     ✅ Statistics button preserved for admin")
    else:
        print("     ❌ Statistics button missing for admin")
        return False
    
    # Test admin stats menu
    admin_stats_kb = admin_stats_keyboard()
    admin_stats_text = str(admin_stats_kb.inline_keyboard)
    
    print("   Admin Stats Menu:")
    if "Общая статистика" in admin_stats_text and "admin_general_stats" in admin_stats_text:
        print("     ✅ Admin statistics functionality preserved")
    else:
        print("     ❌ Admin statistics functionality missing")
        return False
    
    return True

def main():
    """Run validation"""
    print("🧪 Keyboard Validation Test")
    print("=" * 50)
    
    user_valid = validate_user_keyboards()
    admin_valid = validate_admin_keyboards()
    
    print("\n📊 Results:")
    print(f"   User keyboards: {'✅ PASS' if user_valid else '❌ FAIL'}")
    print(f"   Admin keyboards: {'✅ PASS' if admin_valid else '❌ FAIL'}")
    
    if user_valid and admin_valid:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Statistics buttons successfully removed from user keyboards")
        print("✅ Statistics buttons preserved for admin keyboards")
        print("✅ Request completed successfully!")
    else:
        print("\n❌ Some tests failed - please check keyboard configuration")
    
    return user_valid and admin_valid

if __name__ == "__main__":
    main()