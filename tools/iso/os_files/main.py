#!/usr/bin/env python
"""
البرنامج الرئيسي للمشروع
Main Program for the Project
"""

import sys
import argparse
from pathlib import Path

# إضافة المسار الأب
sys.path.insert(0, str(Path(__file__).parent))

def run_examples():
    """تشغيل الأمثلة"""
    print("\n" + "="*60)
    print("تشغيل جميع الأمثلة")
    print("="*60 + "\n")
    
    from examples import motor_control, led_control, language_demo, robot_simulation
    
    examples = [
        ("Motor Control", motor_control.example_motor_control),
        ("LED Control", led_control.example_led_blink),
        ("Language Demo", language_demo.example_language_program),
        ("Robot Simulation", robot_simulation.example_robot_simulation),
    ]
    
    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"❌ خطأ في المثال '{name}': {e}")
        print("\n" + "-"*60)

def run_tests():
    """تشغيل الاختبارات"""
    from tests.test_suite import run_all_tests
    run_all_tests()

def run_simulator():
    """تشغيل المحاكاة التفاعلية"""
    from firmware.simulator.simulator import FirmwareSimulator
    
    simulator = FirmwareSimulator()
    simulator.init()
    
    # برنامج مثال
    program = """
    var x = 10;
    var y = 20;
    var sum = x + y;
    print("نتيجة:");
    print(sum);
    """
    
    simulator.run_program(program, duration_s=3)
    simulator.print_statistics()
    simulator.deinit()

def main():
    """الدالة الرئيسية"""
    parser = argparse.ArgumentParser(
        description="Robot Firmware Operating System"
    )
    
    parser.add_argument(
        "command",
        choices=["examples", "tests", "simulator", "all"],
        help="الأمر المراد تنفيذه"
    )
    
    args = parser.parse_args()
    
    if args.command == "examples":
        run_examples()
    elif args.command == "tests":
        run_tests()
    elif args.command == "simulator":
        run_simulator()
    elif args.command == "all":
        run_tests()
        run_examples()
        run_simulator()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("استخدام:")
        print("  python main.py examples   # تشغيل الأمثلة")
        print("  python main.py tests      # تشغيل الاختبارات")
        print("  python main.py simulator  # تشغيل المحاكاة")
        print("  python main.py all        # تشغيل الكل")
    else:
        main()
