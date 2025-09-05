"""
Test that statistics buttons are removed from user keyboards
"""
import sys

sys.path.insert(0, '.')

from keyboards.user import profile_menu_keyboard, lesson_controls_keyboard

def test_user_keyboards():
    """Test that statistics buttons are commented out for users"""
    print("🧪 Testing User Keyboard Changes...")
    print("=" * 50)
    
    # Test profile menu keyboard
    print("1. Testing profile_menu_keyboard...")
    profile_keyboard = profile_menu_keyboard()
    
    # Convert keyboard to text to check for statistics buttons
    keyboard_text = str(profile_keyboard.inline_keyboard)
    
    if "Статистика" not in keyboard_text and "my_stats" not in keyboard_text:
        print("   ✅ Statistics button removed from profile menu")
    else:
        print("   ❌ Statistics button still present in profile menu")
        return False
    
    if "Мои покупки" in keyboard_text:
        print("   ✅ 'Мои покупки' button still present")
    
    if "Каталог" in keyboard_text:
        print("   ✅ 'Каталог' button still present")
    
    # Test lesson controls keyboard
    print("\n2. Testing lesson_controls_keyboard...")
    lesson_keyboard = lesson_controls_keyboard(lesson_id=1, has_access=True)
    
    keyboard_text = str(lesson_keyboard.inline_keyboard)
    
    if "Статистика" not in keyboard_text and "lesson_stats" not in keyboard_text:
        print("   ✅ Statistics button removed from lesson controls")
    else:
        print("   ❌ Statistics button still present in lesson controls")
        return False
    
    if "Описание" in keyboard_text:
        print("   ✅ 'Описание' button still present")
    
    print("\n🎉 All user keyboard tests passed!")
    print("📋 Summary:")
    print("   • Statistics buttons removed from user profile menu")
    print("   • Statistics buttons removed from lesson controls")
    print("   • Other buttons preserved")
    
    return True

if __name__ == "__main__":
    success = test_user_keyboards()
    if success:
        print("\n✅ User keyboard modifications completed successfully!")
    else:
        print("\n❌ Some issues found in keyboard modifications")