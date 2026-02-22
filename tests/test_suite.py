"""
Test Suite - مجموعة الاختبارات
"""

import sys
import time
from pathlib import Path

# إضافة المسار الأب
sys.path.insert(0, str(Path(__file__).parent.parent))

# الاختبار 1: HAL
def test_hal_gpio():
    """اختبار HAL GPIO"""
    from firmware.hal.manager import get_hal
    from firmware.hal import PinMode
    
    hal = get_hal()
    gpio = hal.get_gpio(13)
    
    assert gpio is not None
    gpio.set_mode(PinMode.OUTPUT)
    gpio.digital_write(1)
    gpio.digital_read()
    
    print("✓ اختبار GPIO نجح")

def test_hal_pwm():
    """اختبار HAL PWM"""
    from firmware.hal.manager import get_hal
    
    hal = get_hal()
    pwm = hal.get_pwm(9, frequency_hz=1000)
    
    assert pwm is not None
    pwm.set_duty(50)
    pwm.set_frequency(500)
    
    print("✓ اختبار PWM نجح")

def test_hal_uart():
    """اختبار HAL UART"""
    from firmware.hal.manager import get_hal
    
    hal = get_hal()
    uart = hal.get_uart(0, baudrate=115200)
    
    assert uart is not None
    uart.write(b"Hello UART")
    uart.read(10)
    
    print("✓ اختبار UART نجح")

# الاختبار 2: Simulator
def test_virtual_hardware():
    """اختبار Virtual Hardware"""
    from firmware.simulator.virtual_hw import get_virtual_hardware
    
    hw = get_virtual_hardware()
    hw.init_pin(13, "OUTPUT")
    hw.digital_write(13, 1)
    
    assert hw.digital_read(13) == 1
    
    hw.digital_write(13, 0)
    assert hw.digital_read(13) == 0
    
    print("✓ اختبار Virtual Hardware نجح")

def test_virtual_uart():
    """اختبار Virtual UART"""
    from firmware.simulator.virtual_hw import get_virtual_hardware
    
    hw = get_virtual_hardware()
    hw.init_uart(0, baudrate=115200)
    hw.uart_write(0, b"Test")
    
    print("✓ اختبار Virtual UART نجح")

# الاختبار 3: Scheduler
def test_scheduler_task_creation():
    """اختبار إنشاء مهام الجدولة"""
    from firmware.core.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    
    def dummy_task():
        pass
    
    task_id = scheduler.create_task("test_task", dummy_task, priority=50)
    assert task_id is not None
    
    print("✓ اختبار إنشاء المهام نجح")

def test_scheduler_execution():
    """اختبار تنفيذ المهام"""
    from firmware.core.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    counter = {"count": 0}
    
    def increment():
        counter["count"] += 1
    
    scheduler.create_task("increment", increment, priority=50)
    
    # تشغيل عدة ticks
    for _ in range(10):
        scheduler.tick()
    
    assert counter["count"] > 0
    
    print("✓ اختبار تنفيذ المهام نجح")

# الاختبار 4: Language Engine
def test_language_lexer():
    """اختبار محلل الرموز"""
    from firmware.lang.engine import Lexer, TokenType
    
    code = "var x = 10;"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    
    assert tokens[0].type == TokenType.VAR
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[2].type == TokenType.ASSIGN
    assert tokens[3].type == TokenType.NUMBER
    
    print("✓ اختبار محلل الرموز نجح")

def test_language_parser():
    """اختبار محلل البناء"""
    from firmware.lang.engine import Lexer, Parser
    
    code = "var x = 10;"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    assert ast is not None
    assert len(ast["statements"]) > 0
    
    print("✓ اختبار محلل البناء نجح")

def test_language_execution():
    """اختبار تنفيذ اللغة"""
    from firmware.lang.engine import LanguageEngine
    
    engine = LanguageEngine()
    code = """
    var x = 5;
    var y = x + 10;
    """
    
    ast = engine.compile(code)
    engine.execute(ast)
    
    assert engine.variables["x"] == 5
    assert engine.variables["y"] == 15
    
    print("✓ اختبار تنفيذ اللغة نجح")

def test_language_control_flow():
    """اختبار التحكم في التدفق"""
    from firmware.lang.engine import LanguageEngine
    
    engine = LanguageEngine()
    code = """
    var sum = 0;
    for (var i = 1; i <= 5; i = i + 1) {
        var sum = sum + i;
    }
    """
    
    ast = engine.compile(code)
    engine.execute(ast)
    
    print("✓ اختبار التحكم في التدفق نجح")

# الاختبار 5: Robot API
def test_robot_creation():
    """اختبار إنشاء روبوت"""
    from firmware.robot_api.robot import Robot
    
    robot = Robot("TestBot")
    assert robot.name == "TestBot"
    
    robot.add_motor("main_motor", 5)
    robot.add_led("status_led", 13)
    robot.add_sensor("distance", 2)
    
    assert "main_motor" in robot.motors
    assert "status_led" in robot.leds
    assert "distance" in robot.sensors
    
    print("✓ اختبار إنشاء الروبوت نجح")

def test_robot_motor_control():
    """اختبار التحكم بالمحركات"""
    from firmware.robot_api.robot import Motor
    
    motor = Motor(5)
    motor.forward(200)
    assert motor.direction == 1
    assert motor.speed == 200
    
    motor.backward(150)
    assert motor.direction == -1
    assert motor.speed == 150
    
    motor.stop()
    assert motor.direction == 0
    assert motor.speed == 0
    
    print("✓ اختبار التحكم بالمحركات نجح")

# الاختبار 6: Simulator الكامل
def test_firmware_simulator():
    """اختبار محاكاة البرنامج الثابت الكاملة"""
    from firmware.simulator.simulator import FirmwareSimulator
    
    simulator = FirmwareSimulator()
    simulator.init()
    
    test_program = """
    var counter = 0;
    var counter = counter + 1;
    """
    
    # تشغيل البرنامج لفترة قصيرة
    import threading
    thread = threading.Thread(
        target=simulator.run_program,
        args=(test_program, 1)
    )
    thread.start()
    thread.join(timeout=3)
    
    simulator.deinit()
    
    print("✓ اختبار المحاكاة الكاملة نجح")

def run_all_tests():
    """تشغيل جميع الاختبارات"""
    print("\n" + "="*60)
    print("🧪 تشغيل جميع الاختبارات")
    print("="*60 + "\n")
    
    tests = [
        ("HAL GPIO", test_hal_gpio),
        ("HAL PWM", test_hal_pwm),
        ("HAL UART", test_hal_uart),
        ("Virtual Hardware", test_virtual_hardware),
        ("Virtual UART", test_virtual_uart),
        ("Scheduler Creation", test_scheduler_task_creation),
        ("Scheduler Execution", test_scheduler_execution),
        ("Language Lexer", test_language_lexer),
        ("Language Parser", test_language_parser),
        ("Language Execution", test_language_execution),
        ("Language Control Flow", test_language_control_flow),
        ("Robot Creation", test_robot_creation),
        ("Robot Motor Control", test_robot_motor_control),
        ("Firmware Simulator", test_firmware_simulator),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"تشغيل: {test_name:30s} ... ", end="", flush=True)
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ فشل")
            print(f"  الخطأ: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"✓ نجح: {passed}")
    print(f"✗ فشل: {failed}")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_all_tests()
