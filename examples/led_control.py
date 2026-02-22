"""
مثال 2: نظام LED مع وميض
Example 2: LED Blink System
"""

from firmware.robot_api.robot import LED
import time

def example_led_blink():
    """مثال على نظام LED مع وميض"""
    
    print("\n💡 مثال 2: نظام LED مع الوميض")
    print("="*50)
    
    # إنشاء مصباح LED على الطرف 13
    led = LED(pin=13)
    
    print("\n الخطوات:")
    
    print("\n1️⃣  إضاءة المصباح")
    led.turn_on()
    time.sleep(1)
    
    print("\n2️⃣  إطفاء المصباح")
    led.turn_off()
    time.sleep(1)
    
    print("\n3️⃣  تبديل الحالة (تبديل)")
    led.toggle()
    time.sleep(0.5)
    
    print("\n4️⃣  وميض متكرر")
    led.blink(times=5, duration_ms=200)
    
    print("\n✓ انتهى المثال")

if __name__ == "__main__":
    example_led_blink()
