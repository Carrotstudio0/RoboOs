# 📖 فهرس المشروع الشامل
## Robot Embedded Firmware System - Complete Index

---

## 📚 المستندات الأساسية

| المستند | الوصف | الحالة |
|---------|-------|--------|
| [README.md](README.md) | دليل المشروع الرئيسي | ✅ |
| [BUILD_REPORT.md](BUILD_REPORT.md) | تقرير البناء الكامل | ✅ |
| [QUICKSTART.md](QUICKSTART.md) | دليل البدء السريع | ✅ |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | معمار النظام التفصيلي | ✅ |

---

## 🏗️ مكونات النظام الرئيسية

### 1. **Virtual Hardware Layer**
```
📁 firmware/simulator/
```

**الملفات:**
- [`virtual_hw.py`](firmware/simulator/virtual_hw.py) - محاكى الهاردوير الكامل
- [`simulator.py`](firmware/simulator/simulator.py) - المحاكاة الرئيسية

**الفئات الرئيسية:**
- `VirtualPin` - دبوس افتراضي
- `VirtualUART` - منفذ تسلسلي افتراضي
- `VirtualTimer` - مؤقت افتراضي
- `VirtualHardware` - مديرة الهاردوير

**الوظائف:**
```python
# الحصول على محاكى الهاردوير
hw = get_virtual_hardware()

# تهيئة دبوس
hw.init_pin(13, "OUTPUT")

# كتابة رقمية
hw.digital_write(13, 1)

# قراءة
value = hw.digital_read(13)
```

---

### 2. **Hardware Abstraction Layer (HAL)**
```
📁 firmware/hal/
```

**الملفات:**
- [`__init__.py`](firmware/hal/__init__.py) - الواجهات الأساسية
- [`manager.py`](firmware/hal/manager.py) - مديرة الموارد

**الفئات المتاحة:**
- `GPIO` - إدارة الدبابيس
- `Timer` - المؤقتات
- `UART` - الاتصال التسلسلي
- `PWM` - تعديل عرض النبضة
- `ADC` - تحويل رقمي/تناظري
- `HALManager` - مديرة الموارد

**مثال الاستخدام:**
```python
from firmware.hal.manager import get_hal

hal = get_hal()
gpio = hal.get_gpio(13)
gpio.set_mode(PinMode.OUTPUT)
gpio.digital_write(1)
```

---

### 3. **Firmware Core - Scheduler**
```
📁 firmware/core/
```

**الملفات:**
- [`scheduler.py`](firmware/core/scheduler.py) - جدولة المهام

**الفئات الرئيسية:**
- `Task` - تعريف المهمة
- `TaskState` - حالات المهمة
- `Scheduler` - محكم المهام

**مثال:**
```python
from firmware.core.scheduler import get_scheduler

sched = get_scheduler()

def my_task():
    print("تشغيل مهمة")

task_id = sched.create_task("test", my_task, priority=50)
sched.run(duration_s=10)
```

---

### 4. **Custom Language Engine**
```
📁 firmware/lang/
```

**الملفات:**
- [`engine.py`](firmware/lang/engine.py) - المحرك الكامل

**الفئات:**
- `Lexer` - محلل الرموز
- `Parser` - محلل البناء
- `LanguageEngine` - محرك التنفيذ

**الكلمات المفتاحية:**
- `var` - متغيرات: `var x = 10;`
- `if` - شرط: `if (x > 5) { ... }`
- `while` - حلقة: `while (x > 0) { ... }`
- `for` - حلقة: `for (var i = 0; i < 10; i = i + 1) { ... }`
- `func` - دالة: `func name() { ... }`
- `print` - طباعة: `print("Hello");`
- `delay` - تأخير: `delay(100);`

**مثال:**
```python
from firmware.lang.engine import LanguageEngine

engine = LanguageEngine()
code = """
var sum = 0;
for (var i = 1; i <= 10; i = i + 1) {
    var sum = sum + i;
}
"""
ast = engine.compile(code)
engine.execute(ast)
print(engine.variables["sum"])  # 55
```

---

### 5. **Robot APIs**
```
📁 firmware/robot_api/
```

**الملفات:**
- [`robot.py`](firmware/robot_api/robot.py) - API الروبوت

**الفئات:**
- `Motor` - التحكم بالمحركات
- `LED` - مصابيح LED
- `Sensor` - المستشعرات
- `ServoMotor` - محركات محدودة
- `Robot` - تجميع المكونات

**مثال:**
```python
from firmware.robot_api.robot import Robot

robot = Robot("MyBot")

# إضافة مكونات
robot.add_motor("main", pin=5, enable_pin=6)
robot.add_led("status", pin=13)
robot.add_sensor("distance", pin=2)

# التحكم
motor = robot.get_motor("main")
motor.forward(255)  # الأمام بسرعة كاملة
motor.backward(128)  # للخلف بنصف السرعة
motor.stop()  # إيقاف

led = robot.get_led("status")
led.turn_on()
led.blink(3, 100)  # وميض 3 مرات
```

---

## 🧪 الاختبارات

```
📁 tests/
```

**الملفات:**
- [`test_suite.py`](tests/test_suite.py) - مجموعة الاختبارات (14 اختبار)

**الاختبارات المتاحة:**
1. ✅ HAL GPIO
2. ✅ HAL PWM
3. ✅ HAL UART
4. ✅ Virtual Hardware
5. ✅ Virtual UART
6. ✅ Scheduler Creation
7. ✅ Scheduler Execution
8. ✅ Language Lexer
9. ✅ Language Parser
10. ✅ Language Execution
11. ✅ Language Control Flow
12. ✅ Robot Creation
13. ✅ Robot Motor Control
14. ✅ Firmware Simulator

**التشغيل:**
```bash
python tests/test_suite.py
```

---

## 📝 الأمثلة

```
📁 examples/
```

| المثال | الملف | الوصف |
|--------|------|-------|
| Motor Control | [`motor_control.py`](examples/motor_control.py) | التحكم بمحرك بسيط |
| LED Control | [`led_control.py`](examples/led_control.py) | مصابيح LED والوميض |
| Language Demo | [`language_demo.py`](examples/language_demo.py) | برنامج باللغة المخصصة |
| Robot Simulation | [`robot_simulation.py`](examples/robot_simulation.py) | محاكاة روبوت كاملة |

**التشغيل:**
```bash
python main.py examples
```

---

## 🚀 البرنامج الرئيسي

**الملف:** [`main.py`](main.py)

**الأوامر:**
```bash
# تشغيل الأمثلة
python main.py examples

# تشغيل الاختبارات
python main.py tests

# تشغيل المحاكاة
python main.py simulator

# تشغيل الكل
python main.py all
```

---

## 📊 الإحصائيات والملاحظات

### حجم المشروع
- **ملفات Python**: 11
- **أسطر الكود**: ~3000+
- **اختبارات**: 14
- **أمثلة**: 4
- **توثيق**: 3 ملفات

### القدرات المدعومة
- ✅ محاكاة كاملة للهاردوير
- ✅ لغة برمجة مخصصة (Lexer, Parser, Executor)
- ✅ جدولة المهام
- ✅ تحكم بـ GPIO, PWM, UART, ADC, Timer
- ✅ Robot APIs عالية المستوى
- ✅ سجل الأحداث والإحصائيات

---

## 🛠️ أدوات المساعدة

### مدير البناء
**الملف:** [`build.py`](build.py)

```bash
python build.py
```

---

## 📋 الملفات الأساسية

| الملف | الحجم | الوصف |
|------|-------|-------|
| README.md | ~800 كلمة | دليل المشروع |
| ARCHITECTURE.md | ~2000 كلمة | التصميم المعماري |
| BUILD_REPORT.md | ~1500 كلمة | تقرير البناء |
| QUICKSTART.md | ~1200 كلمة | دليل البدء السريع |

---

## 🎯 الأهداف المحققة

| الهدف | الحالة | الملفات |
|-------|--------|---------|
| Virtual Hardware | ✅ | simulator/*.py |
| HAL | ✅ | hal/*.py |
| Scheduler | ✅ | core/scheduler.py |
| Language Engine | ✅ | lang/engine.py |
| Robot APIs | ✅ | robot_api/robot.py |
| Tests | ✅ | tests/test_suite.py |
| Examples | ✅ | examples/*.py |
| Documentation | ✅ | docs/*.md |

---

## 🔗 الروابط السريعة

### التطوير
- [معمار النظام](docs/ARCHITECTURE.md)
- [محاكى الهاردوير](firmware/simulator/virtual_hw.py)
- [محرك اللغة](firmware/lang/engine.py)

### الاستخدام
- [دليل البدء السريع](QUICKSTART.md)
- [أمثلة](examples/)
- [اختبارات](tests/test_suite.py)

### التوثيق
- [ملف README](README.md)
- [تقرير البناء](BUILD_REPORT.md)
- [المعمار](docs/ARCHITECTURE.md)

---

## 💻 متطلبات النظام

- Python 3.8+
- Git
- Windows / Linux / macOS

---

## 📞 الدعم والمساعدة

### إذا حصلت على خطأ:

1. **اقرأ رسالة الخطأ بعناية**
2. **تحقق من أنك في المجلد الصحيح**
3. **تأكد من Python وجميع المتطلبات**
4. **اقرأ [دليل البدء السريع](QUICKSTART.md)**

---

## 🎓 الموارد التعليمية

### للمبتدئين
1. ابدأ مع [QUICKSTART.md](QUICKSTART.md)
2. جرب الأمثلة في `examples/`
3. اقرأ التوثيق

### للمتقدمين
1. اقرأ [ARCHITECTURE.md](docs/ARCHITECTURE.md)
2. ادرس الكود المصدري
3. اختبر وطور

---

## 📈 خارطة الطريق المستقبلية

### المرحلة التالية (قريباً):
- [ ] تحسين محرك اللغة
- [ ] دمج MicroPython
- [ ] إضافة مزيد من المكتبات

### التطوير اللاحق (لاحقاً):
- [ ] نقل إلى ESP32
- [ ] نقل إلى STM32
- [ ] أداة debugger
- [ ] IDE بسيط

---

## ✨ ملاحظات مهمة

- 🎯 **التصميم المعياري**: كل مكون منفصل وسهل الصيانة
- 💾 **استهلاك الذاكرة منخفض**: النظام خفيف وكفء
- 🔧 **قابل للتوسع**: يسهل إضافة مكونات جديدة
- 📚 **موثق جيداً**: كل شيء موثق بشكل واضح
- 🧪 **مختبر بعناية**: 14 اختبار تغطي كل المكونات

---

## 🏆 الإنجازات

✅ تم البناء بنجاح!  
✅ جميع الاختبارات تنجح!  
✅ جميع الأمثلة تعمل!  
✅ النظام جاهز للاستخدام!  

---

**تم إنشاء هذا الفهرس للمساعدة في التنقل عبر المشروع.**

**استمتع باستكشاف النظام! 🚀**

---

*آخر تحديث: 22 فبراير 2026*  
*الإصدار: 1.0.0*  
*الحالة: جاهز للإنتاج ✅*
