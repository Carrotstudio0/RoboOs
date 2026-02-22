"""
مثال 4: محاكاة كاملة للروبوت
Example 4: Full Robot Simulation
"""

from firmware.simulator.simulator import FirmwareSimulator
from firmware.robot_api.robot import Robot
import time

def example_robot_simulation():
    """مثال على محاكاة روبوت كاملة"""
    
    print("\n🎮 مثال 4: محاكاة روبوت كاملة")
    print("="*50)
    
    # إنشاء المحاكاة
    simulator = FirmwareSimulator()
    simulator.init()
    
    # إنشاء روبوت
    robot = Robot("SimulatedBot")
    robot.add_motor("left_motor", pin=5, enable_pin=6)
    robot.add_motor("right_motor", pin=10, enable_pin=11)
    robot.add_led("status_led", pin=13)
    robot.add_sensor("distance", pin=2, sensor_type="analog")
    
    print("\n الروبوت:")
    print(robot.info())
    
    # سيناريو: تحريك الروبوت للأمام
    print("\n السيناريو: تحريك الروبوت للأمام")
    print("-" * 40)
    
    left_motor = robot.get_motor("left_motor")
    right_motor = robot.get_motor("right_motor")
    status_led = robot.get_led("status_led")
    
    # إضاءة LED
    status_led.turn_on()
    
    # تحريك المحركات
    left_motor.forward(200)
    right_motor.forward(200)
    
    print("\n المحاكاة قيد التشغيل لمدة 3 ثوان...")
    time.sleep(3)
    
    # إيقاف المحركات
    left_motor.stop()
    right_motor.stop()
    status_led.turn_off()
    
    # فترة انتظار قبل الإيقاف
    print("\nفترة انتظار 1 ثانية...")
    time.sleep(1)
    
    # الإحصائيات
    simulator.print_statistics()
    
    # إيقاف المحاكاة
    simulator.deinit()
    
    print("\n✓ انتهى المثال")

if __name__ == "__main__":
    example_robot_simulation()
