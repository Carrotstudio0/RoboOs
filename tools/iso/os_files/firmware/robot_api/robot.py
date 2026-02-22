"""
Robot APIs
واجهات برمجة تطبيقات الروبوت
"""

from firmware.hal.manager import get_hal
from firmware.simulator.virtual_hw import get_virtual_hardware
from typing import Callable, Optional

class Motor:
    """محرك"""
    
    def __init__(self, pin: int, enable_pin: Optional[int] = None):
        self.pin = pin
        self.enable_pin = enable_pin
        self.direction = 0  # 0: توقف، 1: أمام، -1: خلف
        self.speed = 0  # 0-255
        self.hal = get_hal()
        self.hw = get_virtual_hardware()
        
        # تهيئة الأطراف
        gpio = self.hal.get_gpio(pin)
        gpio.set_mode(self._pin_mode_from_string("OUTPUT"))
        
        if enable_pin:
            pwm = self.hal.get_pwm(enable_pin)
    
    def _pin_mode_from_string(self, mode_str):
        """تحويل نص إلى PinMode"""
        from firmware.hal import PinMode
        return PinMode[mode_str]
    
    def forward(self, speed: int = 255):
        """تحريك للأمام"""
        self.speed = min(max(speed, 0), 255)
        self.direction = 1
        self.hw.digital_write(self.pin, 1)
        if self.enable_pin:
            self.hw.analog_write(self.enable_pin, self.speed)
        print(f"[MOTOR] تحريك المحرك {self.pin} للأمام (السرعة: {self.speed})")
    
    def backward(self, speed: int = 255):
        """تحريك للخلف"""
        self.speed = min(max(speed, 0), 255)
        self.direction = -1
        self.hw.digital_write(self.pin, 0)
        if self.enable_pin:
            self.hw.analog_write(self.enable_pin, self.speed)
        print(f"[MOTOR] تحريك المحرك {self.pin} للخلف (السرعة: {self.speed})")
    
    def stop(self):
        """إيقاف محرك"""
        self.speed = 0
        self.direction = 0
        self.hw.digital_write(self.pin, 0)
        if self.enable_pin:
            self.hw.analog_write(self.enable_pin, 0)
        print(f"[MOTOR] إيقاف المحرك {self.pin}")

class LED:
    """مصباح LED"""
    
    def __init__(self, pin: int):
        self.pin = pin
        self.on = False
        self.hal = get_hal()
        self.hw = get_virtual_hardware()
        
        # تهيئة الطرف
        gpio = self.hal.get_gpio(pin)
        gpio.set_mode(self._pin_mode_from_string("OUTPUT"))
    
    def _pin_mode_from_string(self, mode_str):
        """تحويل نص إلى PinMode"""
        from firmware.hal import PinMode
        return PinMode[mode_str]
    
    def turn_on(self):
        """إضاءة LED"""
        self.on = True
        self.hw.digital_write(self.pin, 1)
        print(f"[LED] إضاءة مصباح {self.pin}")
    
    def turn_off(self):
        """إطفاء LED"""
        self.on = False
        self.hw.digital_write(self.pin, 0)
        print(f"[LED] إطفاء مصباح {self.pin}")
    
    def toggle(self):
        """تبديل الحالة"""
        if self.on:
            self.turn_off()
        else:
            self.turn_on()
    
    def blink(self, times: int = 3, duration_ms: int = 100):
        """وميض"""
        import time
        for _ in range(times):
            self.turn_on()
            time.sleep(duration_ms / 1000)
            self.turn_off()
            time.sleep(duration_ms / 1000)

class Sensor:
    """مستشعر"""
    
    def __init__(self, pin: int, sensor_type: str = "digital"):
        self.pin = pin
        self.sensor_type = sensor_type
        self.value = 0
        self.hal = get_hal()
        self.hw = get_virtual_hardware()
        
        # تهيئة الطرف
        gpio = self.hal.get_gpio(pin)
        if sensor_type == "digital":
            gpio.set_mode(self._pin_mode_from_string("INPUT"))
        else:
            gpio.set_mode(self._pin_mode_from_string("ANALOG"))
    
    def _pin_mode_from_string(self, mode_str):
        """تحويل نص إلى PinMode"""
        from firmware.hal import PinMode
        return PinMode[mode_str]
    
    def read(self) -> int:
        """قراءة قيمة المستشعر"""
        if self.sensor_type == "digital":
            self.value = self.hw.digital_read(self.pin)
        else:
            self.value = self.hw.analog_read(self.pin)
        return self.value
    
    def attach_interrupt(self, callback: Callable):
        """تعليق دالة مقاطعة"""
        print(f"[SENSOR] تعليق مقاطعة على المستشعر {self.pin}")
        # سيتم تطبيقها لاحقاً
    
    def __repr__(self):
        return f"Sensor(pin={self.pin}, type={self.sensor_type}, value={self.value})"

class ServoMotor:
    """محرك محدود الحركة (Servo)"""
    
    def __init__(self, pin: int):
        self.pin = pin
        self.angle = 90  # الزاوية الافتراضية
        self.hal = get_hal()
        self.hw = get_virtual_hardware()
        
        # تهيئة PWM
        pwm = self.hal.get_pwm(pin, frequency_hz=50)  # 50Hz لـ Servo
    
    def set_angle(self, angle: int):
        """تعيين الزاوية"""
        self.angle = min(max(angle, 0), 180)
        # تحويل الزاوية إلى PWM duty cycle
        duty = (self.angle / 180) * 100
        self.hw.analog_write(self.pin, int(duty * 255 / 100))
        print(f"[SERVO] تعيين الزاوية {self.angle}° على الطرف {self.pin}")
    
    def set_speed(self, speed: int):
        """تعيين السرعة"""
        print(f"[SERVO] تعيين السرعة {speed} على الطرف {self.pin}")

class Robot:
    """روبوت - تجميع جميع المكونات"""
    
    def __init__(self, name: str = "Robot"):
        self.name = name
        self.motors = {}
        self.leds = {}
        self.sensors = {}
        self.servos = {}
    
    def add_motor(self, name: str, pin: int, enable_pin: Optional[int] = None):
        """إضافة محرك"""
        self.motors[name] = Motor(pin, enable_pin)
        print(f"[ROBOT] إضافة محرك '{name}'")
    
    def add_led(self, name: str, pin: int):
        """إضافة مصباح LED"""
        self.leds[name] = LED(pin)
        print(f"[ROBOT] إضافة مصباح '{name}'")
    
    def add_sensor(self, name: str, pin: int, sensor_type: str = "digital"):
        """إضافة مستشعر"""
        self.sensors[name] = Sensor(pin, sensor_type)
        print(f"[ROBOT] إضافة مستشعر '{name}'")
    
    def add_servo(self, name: str, pin: int):
        """إضافة servo motor"""
        self.servos[name] = ServoMotor(pin)
        print(f"[ROBOT] إضافة servo '{name}'")
    
    def get_motor(self, name: str) -> Motor:
        """الحصول على محرك"""
        return self.motors.get(name)
    
    def get_led(self, name: str) -> LED:
        """الحصول على مصباح"""
        return self.leds.get(name)
    
    def get_sensor(self, name: str) -> Sensor:
        """الحصول على مستشعر"""
        return self.sensors.get(name)
    
    def get_servo(self, name: str) -> ServoMotor:
        """الحصول على servo"""
        return self.servos.get(name)
    
    def info(self) -> str:
        """معلومات الروبوت"""
        output = []
        output.append(f"\n📦 معلومات الروبوت: {self.name}")
        output.append(f"  محركات: {list(self.motors.keys())}")
        output.append(f"  مصابيح: {list(self.leds.keys())}")
        output.append(f"  مستشعرات: {list(self.sensors.keys())}")
        output.append(f"  محركات محدودة: {list(self.servos.keys())}")
        return "\n".join(output)
