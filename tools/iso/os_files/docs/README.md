# Robot Firmware System
## نظام تشغيل خفيف مخصص للروبوت

نظام تشغيل مدمج (Embedded Firmware) مبني على Python مع لغة برمجة مخصصة قريبة من الهاردوير.

### الأهداف الرئيسية

✅ تشغيل لغة مخصصة مبنية على Python  
✅ تقليل استهلاك الذاكرة  
✅ جعل اللغة قريبة من الآلة (Low-Level Friendly)  
✅ تصميم النظام بسهولة نقل إلى MCU  
✅ محاكاة كاملة قبل استخدام الهاردوير  

### هيكل المشروع

```
firmware/
├── hal/                  # Hardware Abstraction Layer
├── core/                 # Lightweight Kernel Logic
├── runtime/              # MicroPython Runtime (Modified)
├── lang/                 # Custom Language Engine
├── robot_api/            # Robot APIs
└── simulator/            # Virtual Hardware Layer
```

### المراحل

**المرحلة 1**: إعداد البيئة ✅
**المرحلة 2**: بناء Runtime أساسي (قيد الإنجاز)
**المرحلة 3**: بناء HAL و Virtual Hardware
**المرحلة 4**: بناء Language Engine المخصص
**المرحلة 5**: نقل لـ MCU (ESP32/STM32)

### المتطلبات

- Python 3.8+
- Git
- Build tools (GCC, CMake)
- WSL2 (لـ Linux environment على Windows)

### التثبيت والتشغيل

```bash
# تثبيت المتطلبات
pip install -r requirements.txt

# بناء النظام
python build.py

# تشغيل المحاكاة
python simulator/run.py
```

### التطوير

راجع [ARCHITECTURE.md](docs/ARCHITECTURE.md) للمزيد عن تصميم النظام.
