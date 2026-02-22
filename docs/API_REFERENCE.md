# 📖 مرجع API السريع
## Quick API Reference

---

## 🛠️ استيراد المكونات الأساسية

### محاكى الهاردوير
```python
from firmware.simulator.virtual_hw import get_virtual_hardware, init_simulator
hw = get_virtual_hardware()
```

### طبقة الاستخلاص
```python
from firmware.hal.manager import get_hal
hal = get_hal()
```

### الجدولة
```python
from firmware.core.scheduler import get_scheduler
scheduler = get_scheduler()
```

### اللغة المخصصة
```python
from firmware.lang.engine import LanguageEngine, Lexer, Parser
engine = LanguageEngine()
```

### واجهات الروبوت
```python
from firmware.robot_api.robot import Robot, Motor, LED, Sensor
robot = Robot("MyRobot")
```

---

## 🔌 Virtual Hardware API

### إنشاء دبوس
```python
hw.init_pin(13, "OUTPUT")  # OUTPUT, INPUT, ANALOG, PWM
```

### إدخال/إخراج رقمي
```python
hw.digital_write(13, 1)      # كتابة 1 أو 0
value = hw.digital_read(13)  # قراءة 0 أو 1
```

### إدخال/إخراج تناظري
```python
hw.analog_write(9, 128)   # PWM (0-255)
value = hw.analog_read(2) # قراءة (0-1023)
```

### UART
```python
hw.init_uart(0, 115200)      # التهيئة
hw.uart_write(0, b"Hello")   # الكتابة
data = hw.uart_read(0, 10)   # القراءة
```

### مراقبة
```python
hw.dump_state()                      # حالة النظام
events = hw.get_event_log(limit=10) # آخر الأحداث
```

---

## 📍 HAL API

### GPIO
```python
gpio = hal.get_gpio(13)
gpio.set_mode(PinMode.OUTPUT)
gpio.digital_write(1)
value = gpio.digital_read()
```

### PWM
```python
pwm = hal.get_pwm(9, frequency_hz=1000)
pwm.set_duty(50)              # 50%
pwm.set_frequency(500)        # تغيير التردد
```

### Timer
```python
timer = hal.get_timer(0, frequency_hz=1000)
timer.start()
timer.stop()
timer.set_period_us(1000)
```

### UART
```python
uart = hal.get_uart(0, baudrate=115200)
uart.write(b"data")
data = uart.read(10)
available = uart.available()
```

---

## ⏱️ Scheduler API

### إنشاء مهمة
```python
def my_task():
    print("مهمة تشغيل")

task_id = scheduler.create_task(
    name="my_task",
    function=my_task,
    priority=50,
    args=(),
    kwargs={}
)
```

### التحكم بالمهام
```python
scheduler.resume_task(task_id)     # استئناف
scheduler.suspend_task(task_id)    # تعليق
scheduler.terminate_task(task_id)  # إنهاء
```

### التشغيل
```python
scheduler.run(duration_s=10)  # تشغيل لمدة 10 ثوان
scheduler.stop()              # إيقاف
scheduler.tick()              # tick واحد
```

### الإحصائيات
```python
stats = scheduler.get_stats()      # معلومات الأداء
status = scheduler.dump_tasks()    # حالة المهام
```

---

## 💬 Language Engine API

### التجميع والتنفيذ
```python
code = "var x = 10; print(x);"
ast = engine.compile(code)
engine.execute(ast)
```

### الوصول للمتغيرات
```python
value = engine.variables["x"]
print(engine.variables)  # جميع المتغيرات
```

### الدوال المدمجة
```robot-os
print(value)     // طباعة
delay(ms)        // تأخير
```

---

## 🤖 Robot API

### إنشاء روبوت
```python
robot = Robot("MyRobot")
```

### إضافة المكونات
```python
robot.add_motor("left", pin=5, enable_pin=6)
robot.add_led("power", pin=13)
robot.add_sensor("distance", pin=2)
robot.add_servo("arm", pin=3)
```

### تحكم المحركات
```python
motor = robot.get_motor("left")
motor.forward(255)   # أمام بسرعة كاملة
motor.backward(128)  # خلف بنصف السرعة
motor.stop()         # إيقاف
```

### تحكم LED
```python
led = robot.get_led("power")
led.turn_on()
led.turn_off()
led.toggle()
led.blink(times=3, duration_ms=100)
```

### قراءة المستشعرات
```python
sensor = robot.get_sensor("distance")
value = sensor.read()  # قراءة القيمة
```

### تحكم Servo
```python
servo = robot.get_servo("arm")
servo.set_angle(90)    # تعيين زاوية (0-180)
servo.set_speed(50)    # تعيين السرعة
```

---

## 🧪 Test API

### تشغيل الاختبارات
```python
from tests.test_suite import run_all_tests
run_all_tests()
```

---

## 📊 المحاكاة الكاملة API

```python
from firmware.simulator.simulator import FirmwareSimulator

# إنشاء محاكاة
simulator = FirmwareSimulator()

# التهيئة
simulator.init()

# تشغيل برنامج
program = """
var x = 10;
print(x);
"""
simulator.run_program(program, duration_s=5)

# الإحصائيات
simulator.print_statistics()

# الإيقاف
simulator.deinit()
```

---

## 🎨 الثوابت والتعريفات

### PinMode
```python
from firmware.hal import PinMode
PinMode.INPUT
PinMode.OUTPUT
PinMode.INPUT_PULLUP
PinMode.ANALOG
```

### InterruptMode
```python
from firmware.hal import InterruptMode
InterruptMode.RISING
InterruptMode.FALLING
InterruptMode.CHANGE
```

### TaskState
```python
from firmware.core.scheduler import TaskState
TaskState.IDLE
TaskState.READY
TaskState.RUNNING
TaskState.BLOCKED
TaskState.TERMINATED
```

---

## 💡 أمثلة سريعة

### مثال 1: LED وميض
```python
from firmware.robot_api.robot import LED

led = LED(13)
led.blink(times=5, duration_ms=200)
```

### مثال 2: محرك بسيط
```python
from firmware.robot_api.robot import Motor

motor = Motor(5, enable_pin=6)
motor.forward(255)
import time
time.sleep(2)
motor.stop()
```

### مثال 3: برنامج لغة
```python
from firmware.lang.engine import LanguageEngine

engine = LanguageEngine()
code = """
for (var i = 0; i < 10; i = i + 1) {
    print(i);
}
"""
ast = engine.compile(code)
engine.execute(ast)
```

### مثال 4: روبوت متكامل
```python
from firmware.robot_api.robot import Robot

robot = Robot("ComplexBot")
robot.add_motor("main", 5, 6)
robot.add_led("status", 13)
robot.add_sensor("distance", 2)

motor = robot.get_motor("main")
motor.forward(200)

led = robot.get_led("status")
led.turn_on()

sensor = robot.get_sensor("distance")
dist = sensor.read()
```

---

## 🔍 معالجة الأخطاء

### محاولة/التقاط
```python
try:
    engine.compile("invalid code")
except SyntaxError as e:
    print(f"خطأ: {e}")
```

---

## 📚 مراجع إضافية

| الملف | الوصف |
|------|-------|
| [firmware/simulator/virtual_hw.py](../firmware/simulator/virtual_hw.py) | Virtual Hardware |
| [firmware/hal/manager.py](../firmware/hal/manager.py) | HAL Manager |
| [firmware/core/scheduler.py](../firmware/core/scheduler.py) | Scheduler |
| [firmware/lang/engine.py](../firmware/lang/engine.py) | Language Engine |
| [firmware/robot_api/robot.py](../firmware/robot_api/robot.py) | Robot APIs |

---

## 💾 الحفظ والتحميل

### حفظ حالة الروبوت
```python
import json
state = {
    "motors": {},
    "leds": {},
    "variables": engine.variables
}
```

---

## 📊 الأداء والإحصائيات

### قياس الأداء
```python
scheduler.get_stats()  # CPU usage, ticks, etc.
hw.performance_stats   # GPIO writes/reads, UART bytes
```

---

## 🚀 نصائح الأداء

1. استخدم أولويات المهام بحكمة
2. تقليل عدد المهام إذا أمكن
3. تجنب العمليات الثقيلة في المهام
4. استخدم تأخيرات مناسبة

---

## 🎓 المراجع والموارد

- [QUICKSTART.md](QUICKSTART.md) - البدء السريع
- [ARCHITECTURE.md](../docs/ARCHITECTURE.md) - التصميم
- [examples/](../examples/) - أمثلة عملية

---

**استمتع باستخدام API! 💻**
