# معمار نظام التشغيل الخفيف
## Embedded Firmware Architecture Documentation

### نظرة عامة

هذا المشروع يحتوي على نظام تشغيل خفيف مخصص للروبوتات، مبني على Python مع لغة برمجة مخصصة قريبة من الهاردوير.

### الطبقات الرئيسية (Layers)

```
┌─────────────────────────────────┐
│   User Programs                 │
│   (برامج المستخدم)             │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│   Robot APIs                    │
│   (واجهات برمجة الروبوت)       │
│   - Motor, LED, Sensor, Servo  │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│   Custom Language Engine        │
│   (محرك اللغة المخصصة)         │
│   - Lexer, Parser, Executor    │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│   Firmware Core                 │
│   (نواة النظام الثابت)          │
│   - Scheduler (جدولة المهام)   │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│   HAL (Hardware Abstraction)    │
│   (طبقة الاستخلاص)             │
│   - GPIO, Timer, UART, PWM, ADC│
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│   Virtual Hardware Layer        │
│   (محاكى الهاردوير)            │
│   - Virtual Pins, Virtual UART  │
│   - Virtual Timers, Memory      │
└─────────────────────────────────┘
```

### المكونات الرئيسية

#### 1. Virtual Hardware Layer (`firmware/simulator/`)
**الهدف**: محاكاة الهاردوير على الكمبيوتر

الملفات:
- `virtual_hw.py` - محاكى الهاردوير الكامل
  - `VirtualPin` - دبوس افتراضي
  - `VirtualUART` - منفذ تسلسلي افتراضي
  - `VirtualTimer` - مؤقت افتراضي
  - `VirtualHardware` - مديرة الهاردوير الكاملة

الميزات:
- قراءة/كتابة رقمية وتناظرية
- محاكاة UART
- سجل الأحداث
- إحصائيات الأداء

#### 2. HAL (Hardware Abstraction Layer) (`firmware/hal/`)
**الهدف**: تجريد الهاردوير لسهولة النقل

الملفات:
- `__init__.py` - توابع الهاردوير الأساسية
  - `GPIO` - إدارة الدبابيس
  - `Timer` - المؤقتات
  - `UART` - الاتصال التسلسلي
  - `PWM` - تعديل عرض النبضة
  - `ADC` - تحويل رقمي/تناظري

- `manager.py` - مديرة HAL العامة
  - `HALManager` - مديرة جميع الموارد
  - `get_hal()` - الحصول على النسخة العامة

الميزات:
- إدارة مركزية للموارد
- دعم أجهزة متعددة
- سهل التوسع

#### 3. Firmware Core (`firmware/core/`)
**الهدف**: نواة النظام الخفيفة

الملفات:
- `scheduler.py` - جدولة المهام
  - `Task` - تعريف المهمة
  - `Scheduler` - محكم المهام
  
الميزات:
- جدولة بدون نظام تشغيل
- Round Robin مع الأولويات
- تبديل السياق
- إحصائيات CPU

#### 4. Custom Language Engine (`firmware/lang/`)
**الهدف**: لغة برمجة مخصصة قريبة من الهاردوير

الملفات:
- `engine.py` - محرك اللغة الكامل

المكونات:
1. **Lexer** (محلل الرموز)
   - تحويل النص إلى رموز
   - دعم الكلمات المفتاحية
   - دعم العمليات والفواصل

2. **Parser** (محلل البناء)
   - تحويل الرموز إلى AST (شجرة بناء الجملة)
   - تحليل التعريفات والعمليات
   - دعم البنى التحكمية

3. **Executor** (المنفذ)
   - تنفيذ البرامج
   - إدارة المتغيرات
   - دعم الدوال

الكلمات المفتاحية:
- `var` - التعريف عن متغير
- `if` - شرط
- `while` - حلقة while
- `for` - حلقة for
- `func` - دالة
- `return` - إرجاع قيمة
- `motor`, `sensor`, `led` - مكونات الروبوت

#### 5. Robot APIs (`firmware/robot_api/`)
**الهدف**: واجهات برمجة الروبوت العالية المستوى

الملفات:
- `robot.py` - واجهات الروبوت

الفئات:
- `Motor` - التحكم بالمحركات
- `LED` - التحكم بمصابيح LED
- `Sensor` - قراءة المستشعرات
- `ServoMotor` - التحكم بزوايا Servo
- `Robot` - تجميع جميع المكونات

#### 6. Simulator (`firmware/simulator/`)
**الهدف**: محاكاة كاملة للنظام

الملفات:
- `simulator.py` - المحاكاة الرئيسية
  - `FirmwareSimulator` - المحاكى الكامل

الميزات:
- تكامل جميع الطبقات
- تشغيل البرامج
- إحصائيات شاملة

### قافية البيانات

#### يعمل البرنامج كالتالي:

1. **التحميل والتجميع**
   - تحميل كود المستخدم
   - تحليل لغوي (Lexical Analysis)
   - تحليل نحوي (Parsing)

2. **التنفيذ**
   - إنشاء مهام
   - جدولة الأولويات
   - تنفيذ المهام

3. **التفاعل مع الهاردوير**
   - طلبات من Robot APIs
   - مرور عبر HAL
   - محاكاة في Virtual Hardware

4. **المراقبة والإحصائيات**
   - سجل الأحداث
   - قياس الأداء
   - استهلاك الموارد

### أمثلة الاستخدام

#### مثال 1: برنامج بسيط
```python
from firmware.robot_api.robot import Robot, LED

robot = Robot("MyBot")
robot.add_led("status", pin=13)
led = robot.get_led("status")
led.turn_on()
```

#### مثال 2: برنامج باللغة المخصصة
```
var counter = 0;
for (var i = 0; i < 10; i = i + 1) {
    var counter = counter + 1;
}
print(counter);
```

#### مثال 3: محاكاة كاملة
```python
from firmware.simulator.simulator import FirmwareSimulator

simulator = FirmwareSimulator()
simulator.init()
simulator.run_program(code)
simulator.print_statistics()
simulator.deinit()
```

### نقل المشروع لـ MCU

#### الخطوات:
1. **تجميع لـ C/C++**: تحويل الأجزاء الأساسية لـ C
2. **نقل MicroPython**: استخدام MicroPython على الـ MCU
3. **دمج HAL**: تحديث طبقة HAL للـ MCU المحدد
4. **الاختبار**: اختبار على الهاردوير الفعلي

#### MCU المدعومة (قادمة):
- ESP32
- STM32F4
- STM32H7
- nRF52840

### الملفات والمجلدات

```
os/
├── firmware/
│   ├── simulator/       # محاكى الهاردوير
│   ├── hal/             # Hardware Abstraction Layer
│   ├── core/            # Scheduler
│   ├── lang/            # Language Engine
│   ├── robot_api/       # Robot APIs
│   └── __init__.py
├── examples/            # أمثلة
├── tests/               # الاختبارات
├── build.py             # مدير البناء
├── requirements.txt     # المتطلبات
├── CMakeLists.txt       # بناء C/C++
└── README.md            # التوثيق الأساسي
```

### المتطلبات

- Python 3.8+
- Git
- Build tools (GCC, CMake) - للنقل لاحقاً

### التثبيت

```bash
# تثبيت المتطلبات
pip install -r requirements.txt

# بناء النظام
python build.py

# تشغيل الاختبارات
python tests/test_suite.py

# تشغيل مثال
python examples/motor_control.py
```

### الخطوات التالية

1. ✅ المرحلة 1: إعداد البيئة
2. ✅ المرحلة 2: بناء Runtime أساسي
3. ✅ المرحلة 3: بناء HAL و Virtual Hardware
4. ⏳ المرحلة 4: تطوير MicroPython للنظام
5. ⏳ المرحلة 5: نقل لـ MCU
6. ⏳ المرحلة 6: توثيق شاملة

### المرجعيات

- [MicroPython](https://micropython.org/)
- [ESP32](https://www.espressif.com/)
- [STM32](https://www.st.com/)
- [Python AST](https://docs.python.org/3/library/ast.html)
