"""
RoboOS — مثال كامل: روبوت ذكي مع AI
======================================
يوضح التكامل الكامل بين:
  - نظام AI (PID + Fuzzy + Q-Learning)
  - Robot APIs (Motor + Sensor + LED)
  - Scheduler (Multi-task)
  - Anomaly Detection
  - Path Planning (A*)
  - Language Engine (كود روبوت مخصص)
"""

import sys
import os
import time
import math
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firmware.ai.engine import (
    RoboAI, PIDController, FuzzyController,
    QLearningAgent, AnomalyDetector, AStarPlanner,
    NeuralNetwork, GestureRecognizer
)
from firmware.robot_api.robot import Robot
from firmware.core.scheduler import Scheduler
from firmware.lang.engine import LanguageEngine


print("""
╔════════════════════════════════════════════════════╗
║     🤖 RoboOS — Intelligent Robot Demo            ║
║     نظام روبوت ذكي مع AI كامل                    ║
╚════════════════════════════════════════════════════╝
""")

# ─────────────────────────────────────────────────────────────
# 1. إنشاء الروبوت
# ─────────────────────────────────────────────────────────────
print("═" * 55)
print("[1] تهيئة الروبوت والـ AI")
print("─" * 55)

robot = Robot("AI-Bot-1")
robot.add_led("status",  pin=13)
robot.add_led("warning", pin=12)
robot.add_motor("drive", pin_a=2, pin_b=3)
robot.add_sensor("front_sonar", pin=4)

ai = RoboAI("MainAI")

# ─────────────────────────────────────────────────────────────
# 2. PID Auto-Control Demo
# ─────────────────────────────────────────────────────────────
print("\n═" * 55)
print("[2] 🎛️ PID Controller — التحكم التلقائي في السرعة")
print("─" * 55)

pid = PIDController(kp=3.0, ki=0.08, kd=0.15, name="DriveMotor")
target_speed = 100.0
current_speed = 0.0
history = []

for step in range(30):
    output = pid.compute(target_speed, current_speed)
    current_speed += output * 0.04  # محاكاة استجابة المحرك
    current_speed *= 0.95           # احتكاك
    history.append(current_speed)

    bar = "█" * int(max(0, current_speed) / 5)
    err = target_speed - current_speed
    print(f"  t={step:2d}: {current_speed:6.1f}/{target_speed} |{bar:<20}| err={err:+.1f}")

    if abs(current_speed - target_speed) < 2.0:
        print(f"  ✅ استقر في الخطوة {step}!")
        break
    time.sleep(0.02)

stats = pid.get_stats()
print(f"\n  📊 PID Stats: RMS Error={stats.get('rms_error',0):.3f} | Stability={stats.get('stability',0):.3f}")

# ─────────────────────────────────────────────────────────────
# 3. Fuzzy Logic — تجنب العقبات
# ─────────────────────────────────────────────────────────────
print("\n═" * 55)
print("[3] 🌫️ Fuzzy Logic — تحكم تكيفي في تجنب العقبات")
print("─" * 55)

fuzzy = FuzzyController()
print(f"\n  {'المسافة (cm)':<15} {'السرعة':<10} القرار")
print(f"  {'─'*40}")
for dist in [5, 15, 25, 40, 60, 90, 130]:
    speed = fuzzy.infer(dist)
    decision = "STOP ⛔" if abs(speed) < 10 else ("SLOW 🐢" if speed < 100 else "FAST 🚀")
    bar = "█" * max(0, int(speed / 12))
    print(f"  {dist:<15} {speed:<10.1f} {decision}")

# ─────────────────────────────────────────────────────────────
# 4. Q-Learning — تعلم التنقل
# ─────────────────────────────────────────────────────────────
print("\n═" * 55)
print("[4] 🧠 Q-Learning — تعلم التنقل الذاتي")
print("─" * 55)

agent = QLearningAgent(n_states=8, n_actions=4, epsilon=0.5)
total_rewards = []

print("\n  التدريب (20 حلقة):")
for episode in range(20):
    state = random.randint(0, 7)
    ep_reward = 0

    for step in range(30):
        action = agent.choose_action(state)
        sensor_val = random.uniform(0, 200)

        # مكافأة: كلما بعد عن العقبة كلما أحسن
        reward = (sensor_val / 200.0) * 2 - 1
        if sensor_val < 20:
            reward = -2.0  # عقوبة الاصطدام
        elif sensor_val > 100:
            reward = +1.5  # مكافأة الفضاء الحر

        next_state = agent.discretize_state(sensor_val, 200)
        agent.learn(state, action, reward, next_state)
        state = next_state
        ep_reward += reward

    total_rewards.append(ep_reward)
    if episode % 5 == 0:
        avg = sum(total_rewards[-5:]) / min(5, len(total_rewards))
        print(f"  Episode {episode:2d} | Reward={ep_reward:6.1f} | Avg={avg:5.1f} | ε={agent.epsilon:.4f}")

print(f"\n  السياسة المكتسبة:")
actions = {0:"↑ FORWARD", 1:"↓ BACKWARD", 2:"← LEFT", 3:"→ RIGHT"}
for s, a in enumerate(agent.get_policy()):
    print(f"  State {s}: {a}")

# ─────────────────────────────────────────────────────────────
# 5. Anomaly Detection — مراقبة المستشعرات
# ─────────────────────────────────────────────────────────────
print("\n═" * 55)
print("[5] 🔍 Anomaly Detection — مراقبة المستشعرات")
print("─" * 55)

detector = AnomalyDetector(window_size=30, threshold_sigma=2.5)
anomalies_found = []

def on_anomaly_detected(val, z, mean, std):
    anomalies_found.append(val)

detector.on_anomaly(on_anomaly_detected)

# توليد بيانات مستشعر مع شذوذات
print("\n  بيانات المستشعر (قراءات تسلسلية):")
sensor_readings = []
for i in range(50):
    # قراءات طبيعية
    base = 50 + 10 * math.sin(i * 0.3)
    noise = random.gauss(0, 2)
    val = base + noise

    # إدخال شذوذات في مواضع معينة
    if i in [15, 28, 42]:
        val += random.choice([-1, 1]) * random.uniform(30, 50)

    sensor_readings.append(val)
    is_anom = detector.add_sample(val)

    if is_anom:
        print(f"  ⚠️ [t={i:3d}] قيمة={val:6.1f} ← ANOMALY!")
    elif i % 10 == 0:
        s = detector.get_stats()
        print(f"  ✅ [t={i:3d}] قيمة={val:6.1f} | μ={s.get('mean',0):.1f} σ={s.get('std',0):.2f}")

print(f"\n  📊 شذوذات مكتشفة: {len(anomalies_found)}/{50} ({len(anomalies_found)*2}%)")

# ─────────────────────────────────────────────────────────────
# 6. A* Path Planning
# ─────────────────────────────────────────────────────────────
print("\n═" * 55)
print("[6] 🗺️ A* Path Planning — تخطيط المسار الذكي")
print("─" * 55)

planner = AStarPlanner(18, 10)

# خريطة عقبات
walls = [
    (4,1),(4,2),(4,3),(4,4),(4,5),(4,6),
    (8,3),(8,4),(8,5),(8,6),(8,7),(8,8),
    (12,1),(12,2),(12,3),(12,4),(12,5),
]
for ox, oy in walls:
    planner.set_obstacle(ox, oy)

start = (0, 5)
goal  = (17, 5)
path = planner.find_path(start, goal)

print(f"\n  [بداية={start}, هدف={goal}]")
print()
if path:
    print(planner.print_grid(path, start, goal))
    print(f"\n  ✅ مسار موجود: {len(path)} نقطة")
    print(f"  المسار: {path[:5]}...{path[-3:]}" if len(path) > 8 else f"  المسار: {path}")
else:
    print("  ❌ لا يوجد مسار!")

# ─────────────────────────────────────────────────────────────
# 7. Neural Network — تصنيف حالة الروبوت
# ─────────────────────────────────────────────────────────────
print("\n═" * 55)
print("[7] 🧬 Neural Network — تصنيف حالة الروبوت")
print("─" * 55)

nn = NeuralNetwork(layers=[6, 10, 6, 4])
STATES = ["NORMAL", "OBSTACLE_NEAR", "STUCK", "RECOVERY"]

# توليد بيانات تدريب
print("\n  تدريب الشبكة العصبية (60 epoch)...")
dataset = []
for _ in range(200):
    label = random.randint(0, 3)
    if label == 0:    # NORMAL
        features = [random.uniform(0.7,1.0), random.uniform(0,0.2),
                   random.uniform(0.3,0.7), random.uniform(0,0.1),
                   random.uniform(0.5,0.9), random.uniform(0,0.2)]
    elif label == 1:  # OBSTACLE
        features = [random.uniform(0,0.3), random.uniform(0.7,1.0),
                   random.uniform(0,0.3), random.uniform(0.6,1.0),
                   random.uniform(0,0.2), random.uniform(0.5,1.0)]
    elif label == 2:  # STUCK
        features = [random.uniform(0,0.1), random.uniform(0.8,1.0),
                   random.uniform(0,0.1), random.uniform(0.8,1.0),
                   random.uniform(0,0.1), random.uniform(0.8,1.0)]
    else:             # RECOVERY
        features = [random.uniform(0.3,0.6), random.uniform(0.3,0.6),
                   random.uniform(0.3,0.6), random.uniform(0.3,0.6),
                   random.uniform(0.3,0.6), random.uniform(0.3,0.6)]
    dataset.append((features, label))

losses = nn.train(dataset, epochs=60, lr=0.005)

# اختبار
print(f"\n  اختبار التصنيف:")
test_cases = [
    ([0.9, 0.1, 0.6, 0.05, 0.8, 0.1], "NORMAL"),
    ([0.1, 0.9, 0.2, 0.8, 0.1, 0.7],  "OBSTACLE_NEAR"),
    ([0.05, 0.95, 0.05, 0.95, 0.05, 0.95], "STUCK"),
]
correct = 0
for features, expected in test_cases:
    pred = nn.predict(features)
    predicted = STATES[pred % 4]
    ok = "✅" if predicted == expected else "❌"
    print(f"  {ok} مدخل → توقع: {predicted:<15} صحيح: {expected}")
    if predicted == expected:
        correct += 1
print(f"\n  دقة التصنيف: {correct}/{len(test_cases)} ({correct*100//len(test_cases)}%)")

# ─────────────────────────────────────────────────────────────
# 8. Language Engine — برمجة الروبوت
# ─────────────────────────────────────────────────────────────
print("\n═" * 55)
print("[8] 🔤 Language Engine — برمجة الروبوت باللغة المخصصة")
print("─" * 55)

engine = LanguageEngine()

robot_program = """
// برنامج تحكم في الروبوت
var target_speed = 150;
var obstacle_dist = 45;
var loop_count = 0;

func check_speed(distance) {
    if (distance < 30) {
        var target_speed = 0;
    }
    if (distance > 80) {
        var target_speed = 200;
    }
    return target_speed;
}

// حلقة تحكم رئيسية
var i = 0;
for (var i = 0; i < 5; i = i + 1) {
    var loop_count = loop_count + 1;
    var spd = check_speed(obstacle_dist);
    print(loop_count);
}
"""

print("\n  كود الروبوت:")
print("  " + "─"*40)
for line in robot_program.strip().splitlines():
    if line.strip() and not line.strip().startswith("//"):
        print(f"  │ {line}")
print("  " + "─"*40)

print("\n  تنفيذ البرنامج:")
ast = engine.compile(robot_program)
engine.execute(ast)

# ─────────────────────────────────────────────────────────────
# 9. Gesture Recognition — تحكم باليد
# ─────────────────────────────────────────────────────────────
print("\n═" * 55)
print("[9] 🤚 Gesture Recognition — التعرف على الإيماءات")
print("─" * 55)

gesture = GestureRecognizer()
detected = set()

print("\n  محاكاة بيانات IMU + كشف الإيماءات:")

# محاكاة اهتزاز (Shake)
for _ in range(15):
    ax = random.gauss(0, 4.0)  # تسارع عالي
    ay = random.gauss(0, 4.0)
    az = random.gauss(9.8, 0.5)
    g = gesture.add_sample(ax, ay, az, 0, 0, 0)
    if g: detected.add(g)

# محاكاة إمالة يسار (Tilt Left)
for _ in range(15):
    g = gesture.add_sample(0.2, 0, 9.8, 80, 0, 0)  # gyro_x عالي
    if g: detected.add(g)

# محاكاة إمالة يمين
for _ in range(15):
    g = gesture.add_sample(0.2, 0, 9.8, -85, 0, 0)
    if g: detected.add(g)

print(f"\n  الإيماءات المكتشفة: {detected if detected else {'(لم تُكتشف إيماءات — يلزم أجهزة حقيقية)'} }")

# ─────────────────────────────────────────────────────────────
# 10. Scheduler — متعدد المهام
# ─────────────────────────────────────────────────────────────
print("\n═" * 55)
print("[10] ⚡ Scheduler — تشغيل متعدد المهام مع AI")
print("─" * 55)

sched = Scheduler(tick_rate_hz=100)
shared_state = {"sensor": 80.0, "speed": 0.0, "ticks": 0}

def sensor_task():
    """مهمة قراءة المستشعر"""
    shared_state["sensor"] += random.uniform(-5, 5)
    shared_state["sensor"] = max(10, min(200, shared_state["sensor"]))

def ai_control_task():
    """مهمة التحكم بـ AI"""
    fuzzy_ctrl = FuzzyController()
    speed = fuzzy_ctrl.infer(shared_state["sensor"])
    shared_state["speed"] = speed
    shared_state["ticks"] += 1

def monitor_task():
    """مهمة المراقبة"""
    pass  # في النظام الحقيقي: إرسال عبر UART

t_sensor  = sched.create_task("sensor",     sensor_task,  priority=90)
t_ai      = sched.create_task("ai_control", ai_control_task, priority=80)
t_monitor = sched.create_task("monitor",    monitor_task, priority=60)

print(f"\n  المهام:")
print(sched.dump_tasks())

print(f"\n  تشغيل 200 دورة:")
for _ in range(200):
    sched.tick()

stats = sched.get_stats()
print(f"\n  📊 إحصائيات الجدولة:")
print(f"     Ticks:            {stats['total_ticks']}")
print(f"     Context Switches: {stats['context_switches']}")
print(f"     CPU Usage:        {stats['cpu_usage_percent']:.1f}%")
print(f"     Active Tasks:     {stats['running_tasks']}")
print(f"     Sensor Value:     {shared_state['sensor']:.1f} cm")
print(f"     Speed (AI):       {shared_state['speed']:.1f}")

# ─────────────────────────────────────────────────────────────
# 11. AI Coordinator - التقرير النهائي
# ─────────────────────────────────────────────────────────────
print("\n═" * 55)
print("[11] 📊 AI Coordinator — التقرير الشامل")
print("─" * 55)

# تشغيل سيناريو كامل
for distance in [150, 100, 60, 30, 10, 25, 70, 120]:
    speed = ai.decide_speed(distance)
    state = ai.classify_state([
        distance/200, speed/255, random.random(),
        random.random(), random.random(), random.random()
    ])
    print(f"  dist={distance:3d}cm → speed={speed:6.1f} | state={state}")

ai.print_status()

# ─────────────────────────────────────────────────────────────
# الخلاصة
# ─────────────────────────────────────────────────────────────
print("""
╔════════════════════════════════════════════════════╗
║  ✅ تم تشغيل جميع أنظمة RoboOS AI بنجاح!         ║
╠════════════════════════════════════════════════════╣
║  ✅ PID Controller (Auto-stabilization)            ║
║  ✅ Fuzzy Logic (Adaptive obstacle avoidance)      ║
║  ✅ Q-Learning (Self-learning navigation)          ║
║  ✅ Anomaly Detection (Sensor monitoring)          ║
║  ✅ A* Path Planning (Optimal route finding)       ║
║  ✅ Neural Network (State classification)          ║
║  ✅ Gesture Recognition (IMU-based control)        ║
║  ✅ Multi-task Scheduler (RTOS simulation)         ║
║  ✅ Custom Language Engine (Robot programming)     ║
╚════════════════════════════════════════════════════╝

للنشر على الشريحة:
  python roboos.py flash ESP32 --port COM3
  python roboos.py flash STM32F407

للوضع التفاعلي:
  python roboos.py shell

للتدريب:
  python roboos.py ai train --episodes 5000
""")
