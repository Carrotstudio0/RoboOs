"""
Firmware Simulator - المحاكاة الرئيسية
"""

import sys
import time
from firmware.simulator.virtual_hw import get_virtual_hardware, init_simulator, deinit_simulator
from firmware.hal.manager import init_hal, deinit_hal, get_hal
from firmware.core.scheduler import get_scheduler
from firmware.lang.engine import LanguageEngine

class FirmwareSimulator:
    """محاكي البرنامج الثابت الكامل"""
    
    def __init__(self):
        self.virtual_hw = get_virtual_hardware()
        self.hal = get_hal()
        self.scheduler = get_scheduler(tick_rate_hz=1000)
        self.language_engine = LanguageEngine()
        self.running = False
    
    def init(self):
        """تهيئة المحاكاة"""
        print("[FW] تهيئة محاكي البرنامج الثابت\n")
        init_simulator()
        init_hal()
        print("[FW] تم التهيئة بنجاح!\n")
    
    def deinit(self):
        """إيقاف المحاكاة"""
        print("\n[FW] إيقاف البرنامج...")
        self.scheduler.stop()
        deinit_hal()
        deinit_simulator()
    
    def run_program(self, source_code: str, duration_s: float = 10):
        """تشغيل برنامج"""
        self.running = True
        
        try:
            # تجميع الكود
            print("[FW] تجميع الكود...")
            ast = self.language_engine.compile(source_code)
            
            # تنفيذ البرنامج
            print("[FW] تنفيذ البرنامج...\n")
            self.language_engine.execute(ast)
            
            # مراقبة النظام
            print("\n[FW] المحاكاة قيد التشغيل (اضغط Ctrl+C للإيقاف)...\n")
            start_time = time.time()
            
            while time.time() - start_time < duration_s and self.running:
                self.scheduler.tick()
                time.sleep(0.001)  # نوم صغير لتقليل استهلاك CPU
        
        except KeyboardInterrupt:
            print("\n[FW] تم الإيقاف من قبل المستخدم")
        finally:
            self.running = False
    
    def print_statistics(self):
        """طباعة الإحصائيات"""
        print("\n" + "="*60)
        print("📊 إحصائيات المحاكاة")
        print("="*60)
        
        # إحصائيات الجدولة
        sched_stats = self.scheduler.get_stats()
        print("\n⏱️  جدولة المهام:")
        for key, value in sched_stats.items():
            print(f"  {key}: {value}")
        
        # إحصائيات الهاردوير الافتراضي
        perf_stats = self.virtual_hw.performance_stats
        print("\n🔧 الأداء:")
        for key, value in perf_stats.items():
            print(f"  {key}: {value}")
        
        # حالة النظام
        print("\n" + self.virtual_hw.dump_state())
        
        # حالة المهام
        print("\n" + self.scheduler.dump_tasks())
        
        # سجل الأحداث
        print("\n📝 آخر الأحداث:")
        for event in self.virtual_hw.get_event_log(limit=10):
            print(f"  {event}")
        
        print("\n" + "="*60)

def main():
    """البرنامج الرئيسي"""
    
    # إنشاء المحاكاة
    simulator = FirmwareSimulator()
    simulator.init()
    
    # برنامج اختبار بسيط
    test_program = """
    var x = 0;
    var led_pin = 13;
    
    func main() {
        print("مرحباً بك في نظام التشغيل الخفيف!");
        
        for (var i = 0; i < 5; i = i + 1) {
            var value = i * 2;
            print("القيمة:");
            print(value);
        }
    }
    
    main();
    """
    
    # تشغيل البرنامج
    simulator.run_program(test_program, duration_s=5)
    
    # طباعة الإحصائيات
    simulator.print_statistics()
    
    # إيقاف
    simulator.deinit()
    
    print("\n✓ اكتملت المحاكاة بنجاح!")

if __name__ == "__main__":
    main()
