"""
Hardware Abstraction Layer (HAL)
طبقة الاستخلاص من الهاردوير
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional

class PinMode(Enum):
    """أنماط تشغيل الدبابيس"""
    INPUT = 0
    OUTPUT = 1
    INPUT_PULLUP = 2
    ANALOG = 3

class InterruptMode(Enum):
    """أنماط المقاطعات"""
    RISING = 1
    FALLING = 2
    CHANGE = 3

class HardwareInterface(ABC):
    """واجهة الهاردوير الأساسية"""
    
    @abstractmethod
    def init(self):
        """تهيئة الهاردوير"""
        pass
    
    @abstractmethod
    def deinit(self):
        """إيقاف الهاردوير"""
        pass

class GPIO(HardwareInterface):
    """وحدة GPIO (General Purpose Input/Output)"""
    
    def __init__(self, pin: int):
        self.pin = pin
        self.mode = None
        self.digital_value = 0
        self.analog_value = 0
        self._callbacks = {}
    
    def init(self):
        print(f"[GPIO] تهيئة الدبوس {self.pin}")
    
    def deinit(self):
        print(f"[GPIO] إيقاف الدبوس {self.pin}")
    
    def set_mode(self, mode: PinMode):
        """تعيين نمط الدبوس"""
        self.mode = mode
        print(f"[GPIO] وضع الدبوس {self.pin} => {mode.name}")
    
    def digital_write(self, value: int):
        """كتابة قيمة رقمية"""
        if self.mode != PinMode.OUTPUT:
            raise RuntimeError("الدبوس ليس في وضع OUTPUT")
        print(f"[GPIO] كتابة {value} على الدبوس {self.pin}")
    
    def digital_read(self) -> int:
        """قراءة قيمة رقمية"""
        return self.digital_value
    
    def analog_write(self, value: int):
        """PWM كتابة"""
        print(f"[GPIO] كتابة PWM {value} على الدبوس {self.pin}")
    
    def analog_read(self) -> int:
        """قراءة تناظرية"""
        return 0  # محاكاة
    
    def attach_interrupt(self, mode: InterruptMode, callback):
        """تعليق دالة مقاطعة"""
        self._callbacks[mode] = callback
        print(f"[GPIO] تعليق مقاطعة {mode.name} على الدبوس {self.pin}")
    
    def detach_interrupt(self):
        """فصل المقاطعة"""
        self._callbacks.clear()

class Timer(HardwareInterface):
    """وحدة المؤقت"""
    
    def __init__(self, timer_id: int, frequency_hz: int = 1000000):
        self.id = timer_id
        self.frequency = frequency_hz
        self.running = False
        self._callbacks = []
    
    def init(self):
        print(f"[Timer] تهيئة المؤقت {self.id} @ {self.frequency} Hz")
    
    def deinit(self):
        print(f"[Timer] إيقاف المؤقت {self.id}")
    
    def start(self):
        """بدء المؤقت"""
        self.running = True
        print(f"[Timer] بدء المؤقत {self.id}")
    
    def stop(self):
        """إيقاف المؤقت"""
        self.running = False
        print(f"[Timer] إيقاف المؤقت {self.id}")
    
    def set_period_us(self, period_us: int):
        """تعيين فترة المؤقت"""
        print(f"[Timer] تعيين الفترة {period_us} µs للمؤقت {self.id}")
    
    def attach_callback(self, callback):
        """تعليق دالة معاودة النداء"""
        self._callbacks.append(callback)

class UART(HardwareInterface):
    """وحدة الاتصال التسلسلي UART"""
    
    def __init__(self, uart_id: int, baudrate: int = 115200):
        self.id = uart_id
        self.baudrate = baudrate
        self.buffer = bytearray()
    
    def init(self):
        print(f"[UART] تهيئة UART{self.id} @ {self.baudrate} baud")
    
    def deinit(self):
        print(f"[UART] إيقاف UART{self.id}")
    
    def write(self, data: bytes):
        """كتابة بيانات"""
        print(f"[UART] إرسال {len(data)} بايت على UART{self.id}")
    
    def read(self, num_bytes: int = -1) -> bytes:
        """قراءة البيانات"""
        return b""  # محاكاة
    
    def available(self) -> int:
        """عدد البايتات المتاحة"""
        return 0

class PWM(HardwareInterface):
    """وحدة PWM (Pulse Width Modulation)"""
    
    def __init__(self, pin: int, frequency_hz: int = 1000):
        self.pin = pin
        self.frequency = frequency_hz
        self.duty = 0
    
    def init(self):
        print(f"[PWM] تهيئة PWM على الدبوس {self.pin} @ {self.frequency} Hz")
    
    def deinit(self):
        print(f"[PWM] إيقاف PWM على الدبوس {self.pin}")
    
    def set_duty(self, duty_percent: float):
        """تعيين دورة العمل"""
        self.duty = duty_percent
        print(f"[PWM] تعيين الدبوس {self.pin} إلى {duty_percent}%")
    
    def set_frequency(self, frequency_hz: int):
        """تعيين التردد"""
        self.frequency = frequency_hz
        print(f"[PWM] تعيين تردد الدبوس {self.pin} إلى {frequency_hz} Hz")

class ADC(HardwareInterface):
    """وحدة تحويل رقمي/تناظري"""
    
    def __init__(self, adc_id: int, resolution_bits: int = 12):
        self.id = adc_id
        self.resolution = resolution_bits
        self.max_value = (1 << resolution_bits) - 1
    
    def init(self):
        print(f"[ADC] تهيئة ADC{self.id} ({self.resolution} bits)")
    
    def deinit(self):
        print(f"[ADC] إيقاف ADC{self.id}")
    
    def read(self) -> int:
        """قراءة من ADC"""
        return 0
    
    def read_voltage(self, vref: float = 3.3) -> float:
        """قراءة الجهد"""
        return 0.0
