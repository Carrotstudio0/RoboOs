# 🚀 دليل البدء السريع
## Quick Start Guide

---

## ⚙️ المتطلبات

- Python 3.8 أو أحدث
- Git
- نظام تشغيل Windows / Linux / macOS

---

## 📥 التثبيت والتشغيل

### 1️⃣ نسخ المشروع
```bash
cd Desktop
```

---

## 🏃 الخطوات الأولى

### **تشغيل مثال بسيط (Motor Control)**
```bash
cd os
python examples/motor_control.py
```

**النتيجة المتوقعة:**
```
🤖 مثال 1: التحكم بمحرك بسيط
==================================================
1️⃣  تحريك للأمام بسرعة كاملة
[MOTOR] تحريك المحرك 5 للأمام (السرعة: 255)

2️⃣  تحريك بسرعة وسطية (128/255)
[MOTOR] تحريك المحرك 5 للأمام (السرعة: 128)

3️⃣  تحريك للخلف
[MOTOR] تحريك المحرك 5 للخلف (السرعة: 200)

4️⃣  إيقاف المحرك
[MOTOR] إيقاف المحرك 5

✓ انتهى المثال
```

---

## 🎯 الأمثلة المتاحة

### **مثال 1: التحكم بمحرك**
```bash
python examples/motor_control.py
```
يعلمك كيفية:
- إنشاء روبوت
- إضافة محرك
- التحكم بالاتجاه والسرعة

### **مثال 2: مصابيح LED**
```bash
python examples/led_control.py
```
يعلمك كيفية:
- إضاءة وإطفاء المصابيح
- تبديل الحالة
- نمط الوميض

### **مثال 3: لغة البرمجة المخصصة**
```bash
python examples/language_demo.py
```
يعلمك كيفية:
- كتابة برامج باللغة المخصصة
- استخدام الحلقات
- العمليات الحسابية

### **مثال 4: محاكاة روبوت كاملة**
```bash
python examples/robot_simulation.py
```
يعلمك كيفية:
- تجميع مكونات متعددة
- تشغيل محاكاة كاملة
- عرض الإحصائيات

---

## 🧪 تشغيل الاختبارات

```bash
python main.py tests
```

سيقوم بتشغيل 14 اختبار لجميع المكونات:
- HAL (GPIO, PWM, UART)
- Virtual Hardware
- Scheduler
- Language Engine
- Robot APIs

---

## 📝 كتابة برنامج بسيط

### **مثال برنامج روبوت**

**ملف: my_robot.py**
```python
from firmware.robot_api.robot import Robot
from firmware.simulator.virtual_hw import get_virtual_hardware

# إنشاء روبوت
robot = Robot("MyRobot")

# إضافة مكونات
robot.add_motor("left", pin=5, enable_pin=6)
robot.add_motor("right", pin=10, enable_pin=11)
robot.add_led("power", pin=13)

# التحكم بالروبوت
left_motor = robot.get_motor("left")
right_motor = robot.get_motor("right")
power_led = robot.get_led("power")

# إضاءة مصباح الطاقة
power_led.turn_on()

# تحريك للأمام
left_motor.forward(200)
right_motor.forward(200)

# إيقاف
left_motor.stop()
right_motor.stop()
power_led.turn_off()
```

**التشغيل:**
```bash
python my_robot.py
```

---

## 💻 برنامج باللغة المخصصة

### **المثال:**
```robot-os
var x = 5;
var y = 10;
var sum = x + y;

print("النتيجة:");
print(sum);

for (var i = 0; i < 5; i = i + 1) {
    print("العداد:");
    print(i);
}
```

### **الكلمات المفتاحية:**

| الكلمة | الوصف | مثال |
|-------|-------|------|
| `var` | متغير | `var x = 10;` |
| `if` | شرط | `if (x > 5) { ... }` |
| `while` | حلقة while | `while (x > 0) { ... }` |
| `for` | حلقة for | `for (var i = 0; i < 10; i = i + 1) { ... }` |
| `func` | دالة | `func myFunc() { ... }` |
| `return` | إرجاع | `return x;` |
| `print` | طباعة | `print("Hello");` |

---

## 🏗️ البناء والتشغيل الشامل

```bash
# تشغيل جميع الأمثلة
python main.py examples

# تشغيل جميع الاختبارات
python main.py tests

# تشغيل المحاكاة
python main.py simulator

# تشغيل الكل
python main.py all
```

---

## 📂 هيكل المشروع

```
os/
├── firmware/              # نواة النظام
│   ├── simulator/         # محاكى الهاردوير
│   ├── hal/               # Hardware Abstraction Layer
│   ├── core/              # Scheduler
│   ├── lang/              # Language Engine
│   └── robot_api/         # Robot APIs
├── examples/              # أمثلة عملية
├── tests/                 # اختبارات
├── docs/                  # توثيق
│   └── ARCHITECTURE.md    # التصميم المعماري
├── main.py                # البرنامج الرئيسي
├── build.py               # مدير البناء
└── README.md              # دليل المشروع
```

---

## 🛠️ استكشاف المشاكل

### المشكلة: خطأ في الاستيراد
```
ModuleNotFoundError: No module named 'firmware'
```

**الحل:**
```bash
cd os
python examples/motor_control.py
```

تأكد من أنك داخل مجلد `os/`

---

### المشكلة: خطأ في الترميز
```
UnicodeEncodeError
```

**الحل:**
استخدم PowerShell أو استخدم UTF-8:
```bash
python -u main.py examples
```

---

## 📚 مراجع إضافية

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - معمار النظام الكامل
- [BUILD_REPORT.md](BUILD_REPORT.md) - تقرير البناء
- [README.md](../README.md) - مقدمة المشروع

---

## 💡 نصائح مفيدة

1. **ابدأ بالأمثلة البسيطة** - حاول motor_control.py أولاً
2. **اقرأ التوثيق** - معمار النظام موثق بشكل جيد
3. **اختبر الكود** - استخدم اختبارات مدمجة
4. **اعرض الإحصائيات** - شاهد كيف يعمل النظام

---

## 🎓 التعلم

### خطوات التعلم الموصى بها:

1. **أسبوع 1**: تشغيل الأمثلة وفهم البنية
2. **أسبوع 2**: كتابة برامج روبوت بسيطة
3. **أسبوع 3**: استخدام اللغة المخصصة
4. **أسبوع 4**: تطوير مشروع كامل

---

## 🚀 الخطوات التالية

- [ ] اقرأ معمار النظام
- [ ] اختبر جميع الأمثلة
- [ ] اكتب برنامج خاص بك
- [ ] ساهم في تطوير المشروع

---

**استمتع ببناء روبوتات رائعة! 🤖**
