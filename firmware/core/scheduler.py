"""
Firmware Core - Lightweight Scheduler
النواة الخفيفة للنظام مع جدولة المهام
"""

from enum import Enum
from typing import Callable, Dict, List, Optional
from dataclasses import dataclass
import time
import threading

class TaskState(Enum):
    """حالات المهمة"""
    IDLE = 0
    READY = 1
    RUNNING = 2
    BLOCKED = 3
    TERMINATED = 4

@dataclass
class Task:
    """مهمة (Task)"""
    task_id: int
    name: str
    priority: int
    function: Callable
    args: tuple = ()
    kwargs: dict = None
    state: TaskState = TaskState.IDLE
    stack_size: int = 4096  # بايتات
    execution_count: int = 0
    total_time_us: int = 0
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}

class Scheduler:
    """جدولة حقيقية بدون أنظمة تشغيل ثقيلة"""
    
    def __init__(self, tick_rate_hz: int = 1000):
        self.tasks: Dict[int, Task] = {}
        self.ready_queue: List[int] = []  # قائمة بـ IDs المهام الجاهزة
        self.tick_rate = tick_rate_hz
        self.tick_period_us = 1_000_000 // tick_rate_hz
        self.current_task_id = None
        self.total_ticks = 0
        self.running = False
        self._task_counter = 0
        self._lock = threading.RLock()
        self.context_switches = 0
        self.idle_time_us = 0
    
    def create_task(self, 
                   name: str,
                   function: Callable,
                   priority: int = 50,
                   args: tuple = (),
                   kwargs: dict = None) -> int:
        """إنشاء مهمة جديدة"""
        with self._lock:
            task_id = self._task_counter
            self._task_counter += 1
            
            task = Task(
                task_id=task_id,
                name=name,
                priority=priority,
                function=function,
                args=args,
                kwargs=kwargs or {}
            )
            
            self.tasks[task_id] = task
            self.ready_queue.append(task_id)
            task.state = TaskState.READY
            
            print(f"[SCHED] إنشاء مهمة '{name}' (ID={task_id}, Priority={priority})")
            return task_id
    
    def resume_task(self, task_id: int):
        """استئناف مهمة"""
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.state in [TaskState.IDLE, TaskState.BLOCKED]:
                    task.state = TaskState.READY
                    if task_id not in self.ready_queue:
                        self.ready_queue.append(task_id)
    
    def suspend_task(self, task_id: int):
        """تعليق مهمة"""
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.state = TaskState.BLOCKED
                if task_id in self.ready_queue:
                    self.ready_queue.remove(task_id)
    
    def terminate_task(self, task_id: int):
        """إنهاء مهمة"""
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.state = TaskState.TERMINATED
                if task_id in self.ready_queue:
                    self.ready_queue.remove(task_id)
    
    def _select_next_task(self) -> Optional[int]:
        """اختيار المهمة التالية (Round Robin مع الأولويات)"""
        if not self.ready_queue:
            return None
        
        # ترتيب حسب الأولوية ثم الوقت
        sorted_queue = sorted(
            self.ready_queue,
            key=lambda tid: (-self.tasks[tid].priority, self.tasks[tid].execution_count)
        )
        
        return sorted_queue[0]
    
    def tick(self):
        """tick واحد من الساعة"""
        with self._lock:
            self.total_ticks += 1
            
            # اختيار المهمة التالية
            next_task_id = self._select_next_task()
            
            if next_task_id is None:
                # لا توجد مهام جاهزة - وقت خامل
                self.idle_time_us += self.tick_period_us
                return
            
            # تبديل السياق إذا لزم الأمر
            if next_task_id != self.current_task_id:
                self.context_switches += 1
                self.current_task_id = next_task_id
            
            # تنفيذ المهمة
            task = self.tasks[next_task_id]
            task.state = TaskState.RUNNING
            
            try:
                start_time = time.perf_counter_ns()
                task.function(*task.args, **task.kwargs)
                end_time = time.perf_counter_ns()
                
                elapsed_us = (end_time - start_time) // 1000
                task.total_time_us += elapsed_us
                task.execution_count += 1
                
            except Exception as e:
                print(f"[SCHED] خطأ في المهمة '{task.name}': {e}")
                task.state = TaskState.TERMINATED
            
            task.state = TaskState.READY
    
    def run(self, duration_s: float = None):
        """تشغيل الجدولة"""
        self.running = True
        print(f"[SCHED] بدء التشغيل @ {self.tick_rate} Hz")
        
        start_time = time.time()
        
        try:
            while self.running:
                self.tick()
                
                if duration_s and (time.time() - start_time) > duration_s:
                    break
                
                # محاكاة تأخير الساعة
                time.sleep(self.tick_period_us / 1_000_000)
        
        except KeyboardInterrupt:
            print("[SCHED] تم الإيقاف من قبل المستخدم")
        finally:
            self.running = False
    
    def stop(self):
        """إيقاف الجدولة"""
        self.running = False
    
    def get_stats(self) -> Dict:
        """الحصول على الإحصائيات"""
        with self._lock:
            total_tasks = len(self.tasks)
            running_tasks = sum(1 for t in self.tasks.values() if t.state != TaskState.TERMINATED)
            
            return {
                "total_ticks": self.total_ticks,
                "context_switches": self.context_switches,
                "idle_time_us": self.idle_time_us,
                "total_tasks": total_tasks,
                "running_tasks": running_tasks,
                "cpu_usage_percent": (100 - (self.idle_time_us / (self.total_ticks * self.tick_period_us)) * 100) if self.total_ticks > 0 else 0
            }
    
    def dump_tasks(self) -> str:
        """عرض حالة جميع المهام"""
        with self._lock:
            output = []
            output.append("=== حالة المهام ===\n")
            
            for task_id, task in sorted(self.tasks.items()):
                status = task.state.name
                output.append(f"ID={task_id:2d} | '{task.name:20s}' | Pri={task.priority:3d} | "
                            f"State={status:10s} | Runs={task.execution_count:4d} | "
                            f"Time={task.total_time_us:8d}µs")
            
            full_output = "\n".join(output)
            return full_output

# نسخة عامة من الجدولة
_scheduler_instance = None

def get_scheduler(tick_rate_hz: int = 1000) -> Scheduler:
    """الحصول على نسخة الجدولة"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = Scheduler(tick_rate_hz)
    return _scheduler_instance
