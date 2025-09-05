"""
Test the main menu changes - settings button replaced with profile button
"""
import sys
sys.path.insert(0, '.')

from keyboards.user import main_menu_keyboard, profile_menu_keyboard

def test_main_menu_changes():
    """Test that main menu has profile button instead of settings"""
    print("🧪 Testing Main Menu Changes...")
    print("=" * 50)
    
    # Test main menu
    main_kb = main_menu_keyboard()
    main_text = str(main_kb.inline_keyboard)
    
    print("1. Testing main menu keyboard:")
    
    # Check that settings button is removed
    if "Настройки" not in main_text and "settings" not in main_text:
        print("   ✅ Settings button successfully removed from main menu")
    else:
        print("   ❌ Settings button still present in main menu")
        return False
    
    # Check that profile button is added
    if "Мой профиль" in main_text and "profile" in main_text:
        print("   ✅ Profile button successfully added to main menu")
    else:
        print("   ❌ Profile button missing from main menu")
        return False
    
    # Check other buttons remain
    if "Каталог уроков" in main_text:
        print("   ✅ Catalog button preserved")
    
    if "Бесплатный урок" in main_text:
        print("   ✅ Free lesson button preserved")
    
    if "Мои покупки" in main_text:
        print("   ✅ My purchases button preserved")
    
    if "Поддержка" in main_text:
        print("   ✅ Support button preserved")
    
    return True

def test_profile_menu_functionality():
    """Test that profile menu has settings functionality"""
    print("\n2. Testing profile menu functionality:")
    
    profile_kb = profile_menu_keyboard()
    profile_text = str(profile_kb.inline_keyboard)
    
    # Check settings functionality is integrated
    if "Язык" in profile_text and "change_language" in profile_text:
        print("   ✅ Language settings integrated in profile")
    else:
        print("   ❌ Language settings missing from profile")
        return False
    
    if "Уведомления" in profile_text and "notifications_settings" in profile_text:
        print("   ✅ Notification settings integrated in profile")
    else:
        print("   ❌ Notification settings missing from profile")
        return False
    
    # Check other profile functionality
    if "Мои покупки" in profile_text:
        print("   ✅ My purchases option available")
    
    if "Каталог" in profile_text:
        print("   ✅ Catalog option available")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Testing Main Menu Profile Integration")
    print("=" * 60)
    
    success_count = 0
    total_tests = 2
    
    # Test 1: Main menu changes
    if test_main_menu_changes():
        success_count += 1
    
    # Test 2: Profile functionality
    if test_profile_menu_functionality():
        success_count += 1
    
    print(f"\n📊 Test Results: {success_count}/{total_tests} passed")
    
    if success_count == total_tests:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Settings button successfully removed from main menu")
        print("✅ Profile button successfully added to main menu")
        print("✅ Settings functionality integrated into profile menu")
        print("✅ Language and notification settings accessible via profile")
        print("\n🚀 The modification is working correctly!")
    else:
        print("❌ Some tests failed")
        print("🔧 Please check the failed tests above")

if __name__ == "__main__":
    main()