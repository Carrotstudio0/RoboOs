"""
مثال 1: تشغيل محرك بسيط
Example 1: Simple Motor Control
"""

from firmware.robot_api.robot import Robot, Motor

def example_motor_control():
    """مثال على التحكم بمحرك"""
    
    print("\n🤖 مثال 1: التحكم بمحرك بسيط")
    print("="*50)
    
    # إنشاء روبوت
    robot = Robot("SimpleBot")
    
    # إضافة محرك
    robot.add_motor("main_motor", pin=5, enable_pin=6)
    
    # الحصول على المحرك
    motor = robot.get_motor("main_motor")
    
    # التحكم بالمحرك
    print("\nالخطوات:")
    print("1️⃣  تحريك للأمام بسرعة كاملة")
    motor.forward(255)
    
    print("\n2️⃣  تحريك بسرعة وسطية (128/255)")
    motor.forward(128)
    
    print("\n3️⃣  تحريك للخلف")
    motor.backward(200)
    
    print("\n4️⃣  إيقاف المحرك")
    motor.stop()
    
    print("\n✓ انتهى المثال")

if __name__ == "__main__":
    example_motor_control()
