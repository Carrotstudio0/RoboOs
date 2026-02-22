"""
RoboOS CLI — واجهة سطر الأوامر الاحترافية
==========================================
أداة شاملة للتحكم الكامل في RoboOS:
  roboos build   <target>          — بناء الفيرمور
  roboos flash   <target> [port]   — نشر على الشريحة
  roboos targets                   — عرض الشرائح المدعومة
  roboos run     [example]         — تشغيل مثال
  roboos test                      — تشغيل الاختبارات
  roboos ai      <command>         — أوامر الذكاء الاصطناعي
  roboos monitor [port]            — مراقبة المنفذ التسلسلي
  roboos status                    — حالة النظام
  roboos shell                     — وضع REPL التفاعلي
"""

import sys
import os
import time
import json
import math
import random
import argparse
import threading
from pathlib import Path
from typing import Optional, List

# ─── مسار المشروع ───────────────────────────────────────────
PROJECT_ROOT = str(Path(__file__).parent)
sys.path.insert(0, PROJECT_ROOT)


def _banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    ██████╗  ██████╗ ██████╗  ██████╗  ██████╗ ███████╗     ║
║    ██╔══██╗██╔═══██╗██╔══██╗██╔═══██╗██╔═══██╗██╔════╝     ║
║    ██████╔╝██║   ██║██████╔╝██║   ██║██║   ██║███████╗     ║
║    ██╔══██╗██║   ██║██╔══██╗██║   ██║██║   ██║╚════██║     ║
║    ██║  ██║╚██████╔╝██████╔╝╚██████╔╝╚██████╔╝███████║     ║
║    ╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝     ║
║                                                              ║
║    Embedded OS for Robots | v2.0 | © 2026 Eslam Ibrahim     ║
╚══════════════════════════════════════════════════════════════╝
""")


# ─────────────────────────────────────────────────────────────
# CMD: BUILD
# ─────────────────────────────────────────────────────────────

def cmd_build(args):
    """بناء الفيرمور للشريحة المحددة"""
    from firmware.deploy.flash_tool import FirmwareBuilder, BuildConfig, TargetMCU

    target_name = args.target.upper()
    try:
        target = TargetMCU[target_name]
    except KeyError:
        print(f"❌ شريحة غير معروفة: {args.target}")
        print(f"   الشرائح المتاحة: {', '.join(t.name for t in TargetMCU)}")
        return 1

    config = BuildConfig(
        target=target,
        optimization=args.opt,
        debug=args.debug,
        enable_ai=not args.no_ai,
        enable_wifi=not args.no_wifi,
        heap_size_kb=args.heap,
    )

    builder = FirmwareBuilder(PROJECT_ROOT, config)
    print(f"\n🔨 بناء RoboOS للهدف: {target.name}")
    print(f"   التحسين: -{args.opt} | Debug: {args.debug} | AI: {not args.no_ai}")
    print()

    success = builder.build()
    if success:
        print(f"\n✅ Build مكتمل → {PROJECT_ROOT}/build/{target.value}/")
        return 0
    else:
        print("\n❌ Build فشل")
        return 1


# ─────────────────────────────────────────────────────────────
# CMD: FLASH
# ─────────────────────────────────────────────────────────────

def cmd_flash(args):
    """نشر الفيرمور على الشريحة"""
    from firmware.deploy.flash_tool import DeployManager, TargetMCU

    target_name = args.target.upper()
    try:
        target = TargetMCU[target_name]
    except KeyError:
        print(f"❌ شريحة غير معروفة: {args.target}")
        return 1

    manager = DeployManager(PROJECT_ROOT)
    success = manager.deploy(
        target=target,
        port=args.port,
        optimization=args.opt,
        enable_ai=not args.no_ai
    )
    return 0 if success else 1


# ─────────────────────────────────────────────────────────────
# CMD: TARGETS
# ─────────────────────────────────────────────────────────────

def cmd_targets(args):
    """عرض الشرائح المدعومة"""
    from firmware.deploy.flash_tool import DeployManager

    manager = DeployManager(PROJECT_ROOT)
    manager.flash_tool.flash_tool if hasattr(manager, 'flash_tool') else None

    from firmware.deploy.flash_tool import MCU_PROFILES, TargetMCU
    print(f"\n  الشرائح المدعومة في RoboOS")
    print(f"  {'═'*70}")
    print(f"  {'الشريحة':<18} {'المعالج':<12} {'Flash':<10} {'RAM':<8} {'MHz':<6} المميزات")
    print(f"  {'─'*70}")
    for mcu, p in MCU_PROFILES.items():
        feats = ", ".join(p.features[:4])
        print(f"  {mcu.name:<18} {p.arch:<12} {p.flash_size_kb}KB{'':<6} {p.ram_size_kb}KB{'':<4} {p.cpu_freq_mhz:<6} {feats}")
    print()
    return 0


# ─────────────────────────────────────────────────────────────
# CMD: RUN
# ─────────────────────────────────────────────────────────────

def cmd_run(args):
    """تشغيل مثال"""
    examples_dir = Path(PROJECT_ROOT) / "examples"
    available = list(examples_dir.glob("*.py"))

    if not available:
        print("❌ لا توجد أمثلة في مجلد examples/")
        return 1

    if args.example:
        example_path = examples_dir / f"{args.example}.py"
        if not example_path.exists():
            # بحث جزئي
            matches = [e for e in available if args.example.lower() in e.stem.lower()]
            if not matches:
                print(f"❌ المثال '{args.example}' غير موجود")
                print(f"   المتاح: {', '.join(e.stem for e in available)}")
                return 1
            example_path = matches[0]
    else:
        print(f"\n  الأمثلة المتاحة:")
        for i, ex in enumerate(available, 1):
            print(f"  {i}. {ex.stem}")
        print()
        try:
            choice = int(input("  اختر رقم المثال: ")) - 1
            example_path = available[choice]
        except (ValueError, IndexError):
            print("❌ اختيار غير صحيح")
            return 1

    print(f"\n▶ تشغيل: {example_path.stem}")
    print("─" * 40)
    import subprocess
    result = subprocess.run([sys.executable, str(example_path)],
                           cwd=PROJECT_ROOT)
    return result.returncode


# ─────────────────────────────────────────────────────────────
# CMD: TEST
# ─────────────────────────────────────────────────────────────

def cmd_test(args):
    """تشغيل الاختبارات"""
    test_file = Path(PROJECT_ROOT) / "tests" / "test_suite.py"

    if not test_file.exists():
        print("❌ ملف الاختبارات غير موجود")
        return 1

    print(f"\n🧪 تشغيل اختبارات RoboOS...")
    print("─" * 40)

    import subprocess
    cmd = [sys.executable, str(test_file)]
    if args.verbose:
        cmd.append("-v")

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode


# ─────────────────────────────────────────────────────────────
# CMD: AI
# ─────────────────────────────────────────────────────────────

def cmd_ai(args):
    """أوامر نظام الذكاء الاصطناعي"""
    from firmware.ai.engine import RoboAI, PIDController, AStarPlanner, NeuralNetwork

    ai = RoboAI("CLI-RoboAI")

    if args.ai_command == "status":
        ai.print_status()

    elif args.ai_command == "demo":
        print("\n🧠 عرض تجريبي لنظام الـ AI")
        print("─" * 50)

        # PID Demo
        print("\n[1] PID Controller:")
        pid = PIDController(kp=2.0, ki=0.1, kd=0.05)
        target = 100.0
        current = 0.0
        for i in range(20):
            output = pid.compute(target, current)
            current += output * 0.05
            bar = "█" * int(current / 5)
            print(f"  Step {i+1:2d}: {current:6.1f}/{target} |{bar:<20}|")
            if abs(current - target) < 1:
                print(f"  ✅ استقر في {i+1} خطوة!")
                break
        print(f"  Stats: {pid.get_stats()}")

        # Fuzzy Demo
        print("\n[2] Fuzzy Logic:")
        from firmware.ai.engine import FuzzyController
        fuzzy = FuzzyController()
        for dist in [10, 30, 50, 80, 120]:
            speed = fuzzy.infer(dist)
            bar = "█" * int(abs(speed) / 15)
            print(f"  مسافة={dist:3d}cm → سرعة={speed:6.1f} |{bar}")

        # A* Demo
        print("\n[3] A* Path Planning:")
        planner = AStarPlanner(10, 10)
        planner.set_obstacle(3, 1)
        planner.set_obstacle(3, 2)
        planner.set_obstacle(3, 3)
        planner.set_obstacle(3, 4)
        planner.set_obstacle(7, 5)
        planner.set_obstacle(7, 6)
        planner.set_obstacle(7, 7)
        start, goal = (0, 5), (9, 5)
        path = planner.find_path(start, goal)
        print(planner.print_grid(path, start, goal))
        if path:
            print(f"  ✅ المسار: {len(path)} نقطة")

        # Q-Learning Demo
        print("\n[4] Q-Learning (10 حلقات تعلم):")
        from firmware.ai.engine import QLearningAgent
        agent = QLearningAgent(n_states=5, n_actions=4)
        for ep in range(10):
            state = random.randint(0, 4)
            action = agent.choose_action(state)
            reward = random.uniform(-1, 1)
            next_state = random.randint(0, 4)
            agent.learn(state, action, reward, next_state)
        print(f"  السياسة: {agent.get_policy()}")
        print(f"  Epsilon: {agent.epsilon:.4f}")

        # Neural Net Demo
        print("\n[5] Neural Network:")
        nn = NeuralNetwork([4, 6, 3])
        dataset = [(
            [random.random(), random.random(), random.random(), random.random()],
            random.randint(0, 2)
        ) for _ in range(50)]
        nn.train(dataset, epochs=30, lr=0.01)
        test_input = [0.8, 0.2, 0.5, 0.9]
        pred = nn.predict(test_input)
        states = ["NORMAL", "OBSTACLE", "STUCK"]
        print(f"  مدخل: {test_input} → تصنيف: {states[pred]}")

    elif args.ai_command == "train":
        print(f"\n🎓 تدريب Q-Learning ({args.episodes} حلقة)...")
        from firmware.ai.engine import QLearningAgent
        agent = QLearningAgent()

        for ep in range(args.episodes):
            state = 0
            total_reward = 0
            for step in range(50):
                action = agent.choose_action(state)
                # محاكاة بيئة بسيطة
                sensor = random.uniform(0, 200)
                reward = sensor / 100.0 - 0.5
                next_state = agent.discretize_state(sensor)
                agent.learn(state, action, reward, next_state)
                state = next_state
                total_reward += reward

            if ep % (args.episodes // 10) == 0:
                print(f"  Episode {ep:4d}/{args.episodes} | "
                      f"Reward: {total_reward:6.2f} | "
                      f"ε: {agent.epsilon:.4f}")

        model_path = str(Path(PROJECT_ROOT) / "build" / "ai_model.json")
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
        agent.save(model_path)
        print(f"\n✅ تم الحفظ في: {model_path}")

    elif args.ai_command == "path":
        print("\n🗺️ اختبار تخطيط المسار...")
        planner = AStarPlanner(15, 12)
        # عقبات عشوائية
        for _ in range(20):
            planner.set_obstacle(random.randint(2,12), random.randint(1,10))

        start, goal = (0,6), (14,6)
        path = planner.find_path(start, goal)
        print(planner.print_grid(path, start, goal))
        if path:
            print(f"\n✅ مسار: {len(path)} نقطة")
            print(f"   {path}")
        else:
            print("\n❌ لا يوجد مسار")

    return 0


# ─────────────────────────────────────────────────────────────
# CMD: MONITOR
# ─────────────────────────────────────────────────────────────

def cmd_monitor(args):
    """مراقبة المنفذ التسلسلي"""
    try:
        import serial
    except ImportError:
        print("❌ pyserial غير مثبت — تثبيت: pip install pyserial")
        return 1

    from firmware.deploy.flash_tool import FlashTool
    tool = FlashTool(PROJECT_ROOT)

    port = args.port
    if not port:
        port = tool.detect_port()
        if not port:
            print("❌ لم يُكتشف منفذ — حدد --port")
            return 1

    baud = args.baud
    print(f"\n📡 مراقبة {port} @ {baud} baud")
    print("  CTRL+C للخروج")
    print("─" * 40)

    try:
        ser = serial.Serial(port, baud, timeout=1)
        while True:
            line = ser.readline().decode("utf-8", errors="replace").strip()
            if line:
                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] {line}")
    except serial.SerialException as e:
        print(f"❌ خطأ في الاتصال: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n👋 انتهت المراقبة")
        return 0


# ─────────────────────────────────────────────────────────────
# CMD: STATUS
# ─────────────────────────────────────────────────────────────

def cmd_status(args):
    """حالة نظام RoboOS"""
    print("\n📊 حالة نظام RoboOS")
    print("─" * 50)

    # فحص الملفات
    checks = {
        "firmware/core/scheduler.py":        "Core Scheduler",
        "firmware/hal/__init__.py":           "HAL Layer",
        "firmware/lang/engine.py":            "Language Engine",
        "firmware/robot_api/robot.py":        "Robot APIs",
        "firmware/simulator/simulator.py":    "Simulator",
        "firmware/ai/engine.py":              "AI Engine",
        "firmware/deploy/flash_tool.py":      "Flash Tool",
        "tests/test_suite.py":               "Test Suite",
        "CMakeLists.txt":                    "CMake Build",
    }

    for path, name in checks.items():
        full_path = Path(PROJECT_ROOT) / path
        status = "✅" if full_path.exists() else "❌"
        size = f"({full_path.stat().st_size // 1024}KB)" if full_path.exists() else ""
        print(f"  {status} {name:<25} {size}")

    print()

    # حجم المشروع
    total_lines = 0
    total_files = 0
    for ext in [".py", ".c", ".h", ".s", ".ld"]:
        for f in Path(PROJECT_ROOT).rglob(f"*{ext}"):
            if ".venv" not in str(f) and ".git" not in str(f):
                try:
                    lines = len(f.read_text(errors="ignore").splitlines())
                    total_lines += lines
                    total_files += 1
                except:
                    pass

    print(f"  📁 إجمالي الملفات: {total_files}")
    print(f"  📝 إجمالي الأسطر: {total_lines:,}")
    print()

    # فحص الأدوات المتاحة
    print("  الأدوات الخارجية:")
    tools = {
        "cmake":        "CMake (للبناء)",
        "arm-none-eabi-gcc": "ARM GCC (STM32)",
        "esptool.py":   "esptool (ESP32)",
        "openocd":      "OpenOCD (JTAG/SWD)",
        "mpremote":     "mpremote (MicroPython)",
    }
    import subprocess
    for tool, desc in tools.items():
        try:
            subprocess.run([tool, "--version"], capture_output=True, timeout=3)
            print(f"  ✅ {desc}")
        except:
            print(f"  ⚪ {desc} (غير مثبت)")

    return 0


# ─────────────────────────────────────────────────────────────
# CMD: SHELL (REPL)
# ─────────────────────────────────────────────────────────────

def cmd_shell(args):
    """REPL تفاعلي للغة RoboOS المخصصة"""
    from firmware.lang.engine import LanguageEngine

    print("\n🔤 RoboOS Language Shell (اكتب 'exit' للخروج)")
    print("   اكتب كود بلغة RoboOS المخصصة مباشرة")
    print("─" * 40)
    print("   مثال: var x = 10; print(x);")
    print()

    engine = LanguageEngine()
    buffer = ""

    while True:
        try:
            prompt = "... " if buffer else ">>> "
            line = input(prompt)

            if line.strip() == "exit":
                print("👋 خروج من Shell")
                break
            elif line.strip() == "reset":
                engine = LanguageEngine()
                buffer = ""
                print("♻️ إعادة تعيين")
                continue
            elif line.strip() == "help":
                print("""
  الكلمات المفتاحية:
    var x = 10;              — تعريف متغير
    if (x > 5) { ... }       — شرط
    while (x < 10) { ... }   — حلقة
    for (var i=0; i<5; i=i+1) { ... }  — حلقة for
    func add(a, b) { ... }   — دالة
    print(x);                — طباعة
    delay(100);              — تأخير (ميلي ثانية)
""")
                continue

            buffer += line + "\n"

            # تنفيذ عند اكتمال الكود
            if not line.strip() or (buffer.count("{") == buffer.count("}")):
                if buffer.strip():
                    try:
                        ast = engine.compile(buffer)
                        engine.execute(ast)
                    except SyntaxError as e:
                        print(f"  ⚠️ خطأ نحوي: {e}")
                    except Exception as e:
                        print(f"  ❌ خطأ: {e}")
                buffer = ""

        except (EOFError, KeyboardInterrupt):
            print("\n👋 خروج")
            break

    return 0


# ─────────────────────────────────────────────────────────────
# MAIN PARSER
# ─────────────────────────────────────────────────────────────

def main():
    _banner()

    parser = argparse.ArgumentParser(
        prog="roboos",
        description="RoboOS CLI — نظام تشغيل مدمج ذكي للروبوتات",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
الأوامر:
  build     بناء الفيرمور
  flash     نشر على الشريحة
  targets   عرض الشرائح المدعومة
  run       تشغيل مثال
  test      تشغيل الاختبارات
  ai        أوامر الذكاء الاصطناعي
  monitor   مراقبة المنفذ التسلسلي
  status    حالة النظام
  shell     وضع REPL التفاعلي

أمثلة:
  python roboos.py build esp32
  python roboos.py flash esp32 --port COM3
  python roboos.py ai demo
  python roboos.py ai train --episodes 1000
  python roboos.py shell
  python roboos.py test
        """
    )

    sub = parser.add_subparsers(dest="command")

    # ── build ──────────────────────────────
    p_build = sub.add_parser("build", help="بناء الفيرمور")
    p_build.add_argument("target", help="الشريحة (ESP32, STM32F407, SIMULATOR, ...)")
    p_build.add_argument("--opt", default="Os", choices=["O0","O1","O2","O3","Os","Og"],
                        help="مستوى التحسين (افتراضي: Os)")
    p_build.add_argument("--debug", action="store_true", help="وضع Debug")
    p_build.add_argument("--no-ai", action="store_true", help="تعطيل AI")
    p_build.add_argument("--no-wifi", action="store_true", help="تعطيل WiFi")
    p_build.add_argument("--heap", type=int, default=16, help="حجم Heap بـ KB")

    # ── flash ──────────────────────────────
    p_flash = sub.add_parser("flash", help="نشر على الشريحة")
    p_flash.add_argument("target", help="الشريحة")
    p_flash.add_argument("--port", help="منفذ التسلسل (COM3, /dev/ttyUSB0)")
    p_flash.add_argument("--opt", default="Os")
    p_flash.add_argument("--no-ai", action="store_true")

    # ── targets ────────────────────────────
    p_targets = sub.add_parser("targets", help="عرض الشرائح المدعومة")

    # ── run ────────────────────────────────
    p_run = sub.add_parser("run", help="تشغيل مثال")
    p_run.add_argument("example", nargs="?", help="اسم المثال")

    # ── test ───────────────────────────────
    p_test = sub.add_parser("test", help="تشغيل الاختبارات")
    p_test.add_argument("-v", "--verbose", action="store_true")

    # ── ai ─────────────────────────────────
    p_ai = sub.add_parser("ai", help="أوامر الذكاء الاصطناعي")
    p_ai.add_argument("ai_command",
                     choices=["status", "demo", "train", "path"],
                     help="status|demo|train|path")
    p_ai.add_argument("--episodes", type=int, default=100,
                     help="عدد حلقات التدريب")

    # ── monitor ────────────────────────────
    p_mon = sub.add_parser("monitor", help="مراقبة المنفذ التسلسلي")
    p_mon.add_argument("--port", help="المنفذ")
    p_mon.add_argument("--baud", type=int, default=115200)

    # ── status ─────────────────────────────
    p_status = sub.add_parser("status", help="حالة النظام")

    # ── shell ──────────────────────────────
    p_shell = sub.add_parser("shell", help="REPL تفاعلي")

    # ─────────────────────────────────────────
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        print("\n💡 ابدأ بـ: python roboos.py status")
        return 0

    commands = {
        "build":   cmd_build,
        "flash":   cmd_flash,
        "targets": cmd_targets,
        "run":     cmd_run,
        "test":    cmd_test,
        "ai":      cmd_ai,
        "monitor": cmd_monitor,
        "status":  cmd_status,
        "shell":   cmd_shell,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args) or 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
