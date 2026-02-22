"""
Virtual Hardware Layer
محاكى الهاردوير الافتراضي
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum
import time
import threading
from queue import Queue

@dataclass
class VirtualPin:
    """دبوس افتراضي"""
    pin_number: int
    mode: str = "INPUT"
    digital_value: int = 0
    analog_value: int = 0
    callbacks: Dict = field(default_factory=dict)
    
    def __repr__(self):
        return f"Pin({self.pin_number}): mode={self.mode}, digital={self.digital_value}, analog={self.analog_value}"

@dataclass
class VirtualUART:
    """منفذ تسلسلي افتراضي"""
    uart_id: int
    baudrate: int = 115200
    tx_buffer: Queue = field(default_factory=Queue)
    rx_buffer: Queue = field(default_factory=Queue)
    
    def __repr__(self):
        return f"UART{self.uart_id}@{self.baudrate}baud"

@dataclass
class VirtualTimer:
    """مؤقت افتراضي"""
    timer_id: int
    frequency_hz: int
    callbacks: List = field(default_factory=list)
    is_running: bool = False
    
    def __repr__(self):
        return f"Timer{self.timer_id}@{self.frequency_hz}Hz"

class VirtualHardware:
    """محاكى الهاردوير الكامل"""
    
    def __init__(self):
        self.pins: Dict[int, VirtualPin] = {}
        self.uarts: Dict[int, VirtualUART] = {}
        self.timers: Dict[int, VirtualTimer] = {}
        self.memory: bytearray = bytearray(65536)  # 64KB RAM محاكاة
        self.running = False
        self._lock = threading.RLock()
        self.event_log: List[str] = []
        self.performance_stats = {
            "pin_writes": 0,
            "pin_reads": 0,
            "uart_bytes": 0,
            "timer_ticks": 0,
        }
    
    def init_pin(self, pin: int, mode: str = "INPUT"):
        """تهيئة دبوس"""
        with self._lock:
            self.pins[pin] = VirtualPin(pin, mode)
            self.log_event(f"[PIN] تهيئة الدبوس {pin} كـ {mode}")
    
    def digital_write(self, pin: int, value: int):
        """كتابة رقمية"""
        with self._lock:
            if pin not in self.pins:
                self.init_pin(pin, "OUTPUT")
            self.pins[pin].digital_value = value
            self.performance_stats["pin_writes"] += 1
            self.log_event(f"[GPIO] كتابة {value} على الدبوس {pin}")
    
    def digital_read(self, pin: int) -> int:
        """قراءة رقمية"""
        with self._lock:
            if pin not in self.pins:
                self.init_pin(pin, "INPUT")
            self.performance_stats["pin_reads"] += 1
            return self.pins[pin].digital_value
    
    def analog_write(self, pin: int, value: int):
        """كتابة تناظرية (PWM)"""
        with self._lock:
            if pin not in self.pins:
                self.init_pin(pin, "PWM")
            self.pins[pin].analog_value = value
            self.log_event(f"[PWM] كتابة {value} على الدبوس {pin}")
    
    def analog_read(self, pin: int) -> int:
        """قراءة تناظرية"""
        with self._lock:
            if pin not in self.pins:
                self.init_pin(pin, "ANALOG")
            return self.pins[pin].analog_value
    
    def init_uart(self, uart_id: int, baudrate: int = 115200):
        """تهيئة UART"""
        with self._lock:
            self.uarts[uart_id] = VirtualUART(uart_id, baudrate)
            self.log_event(f"[UART] تهيئة UART{uart_id} @ {baudrate} baud")
    
    def uart_write(self, uart_id: int, data: bytes):
        """كتابة بيانات UART"""
        with self._lock:
            if uart_id not in self.uarts:
                self.init_uart(uart_id)
            self.uarts[uart_id].tx_buffer.put(data)
            self.performance_stats["uart_bytes"] += len(data)
            self.log_event(f"[UART] إرسال {len(data)} بايت على UART{uart_id}")
    
    def uart_read(self, uart_id: int, num_bytes: int = -1) -> bytes:
        """قراءة بيانات UART"""
        with self._lock:
            if uart_id not in self.uarts:
                self.init_uart(uart_id)
            if self.uarts[uart_id].rx_buffer.empty():
                return b""
            return self.uarts[uart_id].rx_buffer.get()
    
    def init_timer(self, timer_id: int, frequency_hz: int):
        """تهيئة مؤقت"""
        with self._lock:
            self.timers[timer_id] = VirtualTimer(timer_id, frequency_hz)
            self.log_event(f"[TIMER] تهيئة Timer{timer_id} @ {frequency_hz} Hz")
    
    def start_timer(self, timer_id: int):
        """بدء مؤقت"""
        with self._lock:
            if timer_id in self.timers:
                self.timers[timer_id].is_running = True
                self.log_event(f"[TIMER] بدء Timer{timer_id}")
    
    def stop_timer(self, timer_id: int):
        """إيقاف مؤقت"""
        with self._lock:
            if timer_id in self.timers:
                self.timers[timer_id].is_running = False
                self.log_event(f"[TIMER] إيقاف Timer{timer_id}")
    
    def memory_write(self, address: int, data: bytes):
        """كتابة الذاكرة"""
        with self._lock:
            for i, byte in enumerate(data):
                if address + i < len(self.memory):
                    self.memory[address + i] = byte
            self.log_event(f"[MEM] كتابة {len(data)} بايت @ 0x{address:04X}")
    
    def memory_read(self, address: int, num_bytes: int) -> bytes:
        """قراءة الذاكرة"""
        with self._lock:
            return bytes(self.memory[address:address + num_bytes])
    
    def log_event(self, message: str):
        """تسجيل حدث"""
        timestamp = time.time()
        event = f"[{timestamp:.3f}] {message}"
        self.event_log.append(event)
    
    def get_pin_state(self, pin: int) -> Optional[VirtualPin]:
        """الحصول على حالة الدبوس"""
        with self._lock:
            return self.pins.get(pin)
    
    def dump_state(self) -> str:
        """طباعة حالة كاملة للنظام"""
        with self._lock:
            output = []
            output.append("=== حالة النظام الافتراضي ===\n")
            
            output.append("📍 الدبابيس:")
            for pin_num, pin in sorted(self.pins.items()):
                output.append(f"  {pin}")
            
            output.append("\n🔌 UART:")
            for uart_id, uart in sorted(self.uarts.items()):
                output.append(f"  {uart}")
            
            output.append("\n⏱️  المؤقتات:")
            for timer_id, timer in sorted(self.timers.items()):
                status = "▶️ تشغيل" if timer.is_running else "⏸️ متوقف"
                output.append(f"  {timer} {status}")
            
            output.append("\n📊 الإحصائيات:")
            output.append(f"  كتابات GPIO: {self.performance_stats['pin_writes']}")
            output.append(f"  قراءات GPIO: {self.performance_stats['pin_reads']}")
            output.append(f"  بايتات UART: {self.performance_stats['uart_bytes']}")
            
            return "\n".join(output)
    
    def get_event_log(self, limit: int = 20) -> List[str]:
        """الحصول على سجل الأحداث"""
        with self._lock:
            return self.event_log[-limit:]

# نسخة عامة من محاكى الهاردوير
_virtual_hw = None

def get_virtual_hardware() -> VirtualHardware:
    """الحصول على نسخة محاكى الهاردوير"""
    global _virtual_hw
    if _virtual_hw is None:
        _virtual_hw = VirtualHardware()
    return _virtual_hw

def init_simulator():
    """تهيئة المحاكى"""
    hw = get_virtual_hardware()
    hw.running = True
    hw.log_event("[SIM] تهيئة محاكى الهاردوير")

def deinit_simulator():
    """إيقاف المحاكى"""
    hw = get_virtual_hardware()
    hw.running = False
    hw.log_event("[SIM] إيقاف محاكى الهاردوير")
