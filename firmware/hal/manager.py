"""
HAL Manager
مدير طبقة الاستخلاص من الهاردوير
"""

from typing import Dict, Optional
from . import GPIO, Timer, UART, PWM, ADC, PinMode, InterruptMode

class HALManager:
    """مديرة جميع موارد الهاردوير"""
    
    def __init__(self):
        self.gpios: Dict[int, GPIO] = {}
        self.timers: Dict[int, Timer] = {}
        self.uarts: Dict[int, UART] = {}
        self.pwms: Dict[int, PWM] = {}
        self.adcs: Dict[int, ADC] = {}
        self._initialized = False
    
    def init(self):
        """تهيئة جميع الموارد"""
        print("[HAL] تهيئة مديرة الهاردوير")
        self._initialized = True
    
    def deinit(self):
        """إيقاف جميع الموارد"""
        print("[HAL] إيقاف جميع موارد الهاردوير")
        for gpio in self.gpios.values():
            gpio.deinit()
        for timer in self.timers.values():
            timer.deinit()
        for uart in self.uarts.values():
            uart.deinit()
        self._initialized = False
    
    def get_gpio(self, pin: int) -> GPIO:
        """الحصول على GPIO أو إنشاء واحد جديد"""
        if pin not in self.gpios:
            self.gpios[pin] = GPIO(pin)
            self.gpios[pin].init()
        return self.gpios[pin]
    
    def get_timer(self, timer_id: int, frequency_hz: int = 1000000) -> Timer:
        """الحصول على Timer أو إنشاء واحد جديد"""
        if timer_id not in self.timers:
            self.timers[timer_id] = Timer(timer_id, frequency_hz)
            self.timers[timer_id].init()
        return self.timers[timer_id]
    
    def get_uart(self, uart_id: int, baudrate: int = 115200) -> UART:
        """الحصول على UART أو إنشاء واحد جديد"""
        if uart_id not in self.uarts:
            self.uarts[uart_id] = UART(uart_id, baudrate)
            self.uarts[uart_id].init()
        return self.uarts[uart_id]
    
    def get_pwm(self, pin: int, frequency_hz: int = 1000) -> PWM:
        """الحصول على PWM أو إنشاء واحد جديد"""
        if pin not in self.pwms:
            self.pwms[pin] = PWM(pin, frequency_hz)
            self.pwms[pin].init()
        return self.pwms[pin]
    
    def get_adc(self, adc_id: int, resolution_bits: int = 12) -> ADC:
        """الحصول على ADC أو إنشاء واحد جديد"""
        if adc_id not in self.adcs:
            self.adcs[adc_id] = ADC(adc_id, resolution_bits)
            self.adcs[adc_id].init()
        return self.adcs[adc_id]
    
    def release_gpio(self, pin: int):
        """تحرير GPIO"""
        if pin in self.gpios:
            self.gpios[pin].deinit()
            del self.gpios[pin]

# Global HAL instance
_hal_instance = None

def get_hal() -> HALManager:
    """الحصول على نسخة مديرة الهاردوير العامة"""
    global _hal_instance
    if _hal_instance is None:
        _hal_instance = HALManager()
        _hal_instance.init()
    return _hal_instance

def init_hal():
    """تهيئة HAL"""
    get_hal()

def deinit_hal():
    """إيقاف HAL"""
    global _hal_instance
    if _hal_instance:
        _hal_instance.deinit()
        _hal_instance = None
