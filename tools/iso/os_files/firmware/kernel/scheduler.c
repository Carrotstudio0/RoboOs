/**
 * @file scheduler.c
 * @brief RoboOS RTOS Kernel Implementation
 *
 * يعمل جنباً مع context_switch.s (PendSV) وirq.c (SysTick).
 * يتبع معيار ARM CMSIS-RTOS.
 */

#include "scheduler.h"
#include "irq.h"
#include <string.h>

/* بالـ hal_asm.s */
extern uint32_t hal_enter_critical(void);
extern void     hal_exit_critical(uint32_t saved);
extern void     hal_dsb(void);
extern void     hal_isb(void);
extern void     hal_wfi(void);

/* بالـ context_switch.s */
extern uint32_t* task_create_stack(uint32_t *stack_top, void (*entry)(void));

/* SCB_ICSR لتفعيل PendSV */
#define SCB_ICSR  (*((volatile uint32_t*)0xE000ED04))
#define PENDSVSET (1 << 28)

/* =============================================================================
 * Static State
 * =============================================================================
 */

/* TCB pool ثابت — لا malloc */
static TCB_t   s_tcb_pool[RTOS_MAX_TASKS];
static uint8_t s_tcb_count = 0;
static TCB_t  *s_task_list = NULL;       /* قائمة مترابطة بكل المهام */
static uint32_t s_tick_count = 0;
static uint32_t s_total_runtime = 0;

/* Idle Task Stack */
static uint32_t s_idle_stack[256];

/* =============================================================================
 * Global: g_current_tcb — يقرأها context_switch.s
 * =============================================================================
 */
TCB_t *volatile g_current_tcb = NULL;

/* =============================================================================
 * Idle Task — يعمل عندما لا توجد مهام جاهزة
 * =============================================================================
 */
static void idle_task_entry(void)
{
    for (;;) {
        hal_wfi();   /* أدخل وضع Sleep لتوفير الطاقة */
    }
}

/* =============================================================================
 * scheduler_init
 * =============================================================================
 */
void scheduler_init(void)
{
    memset(s_tcb_pool, 0, sizeof(s_tcb_pool));
    s_tcb_count = 0;
    s_task_list = NULL;
    g_current_tcb = NULL;

    /* أضف Idle Task دائماً */
    task_create("idle", idle_task_entry, TASK_PRIORITY_IDLE,
                s_idle_stack, sizeof(s_idle_stack));
}

/* =============================================================================
 * task_create
 * =============================================================================
 */
TCB_t* task_create(const char *name, void (*entry)(void),
                   uint8_t priority, uint32_t *stack, size_t stack_size)
{
    if (s_tcb_count >= RTOS_MAX_TASKS) return NULL;
    if (stack_size < RTOS_MIN_STACK_BYTES) return NULL;

    uint32_t saved = hal_enter_critical();

    TCB_t *tcb = &s_tcb_pool[s_tcb_count++];
    memset(tcb, 0, sizeof(TCB_t));

    /* اسم المهمة */
    strncpy(tcb->name, name, sizeof(tcb->name) - 1);
    tcb->priority    = priority;
    tcb->state       = TASK_READY;
    tcb->stack_base  = (uint32_t)stack;
    tcb->stack_size  = (uint32_t)stack_size;

    /* تهيئة Stack Frame الأولي (من context_switch.s) */
    uint32_t *stack_top = stack + (stack_size / sizeof(uint32_t));

    /* ضع حارس Stack عند القاعدة للكشف عن Overflow */
    stack[0] = 0xDEADBEEF;

    tcb->stack_ptr = task_create_stack(stack_top, entry);

    /* أضف للقائمة المترابطة */
    tcb->next = s_task_list;
    s_task_list = tcb;

    hal_exit_critical(saved);
    return tcb;
}

/* =============================================================================
 * scheduler_get_next_tcb — يُستدعى من PendSV_Handler في context_switch.s
 * =============================================================================
 */
TCB_t* scheduler_get_next_tcb(void)
{
    /* ابحث عن المهمة READY ذات أعلى أولوية */
    TCB_t *best = NULL;
    TCB_t *t = s_task_list;

    /* حدِّث حالات النوم */
    while (t) {
        if (t->state == TASK_SLEEPING && s_tick_count >= t->sleep_until_tick) {
            t->state = TASK_READY;
        }
        t = t->next;
    }

    /* اختر الأعلى أولوية */
    t = s_task_list;
    while (t) {
        if (t->state == TASK_READY || t->state == TASK_RUNNING) {
            if (!best || t->priority > best->priority) {
                best = t;
            }
        }
        t = t->next;
    }

    /* إحصائيات */
    if (g_current_tcb && g_current_tcb->state == TASK_RUNNING) {
        g_current_tcb->state = TASK_READY;
    }
    if (best) {
        best->state = TASK_RUNNING;
        best->run_count++;
    }

    return best ? best : s_task_list;  /* fallback: idle */
}

/* =============================================================================
 * scheduler_start — لا تعود أبداً
 * =============================================================================
 */
void scheduler_start(void)
{
    /* اضبط PendSV و SysTick لأدنى أولوية */
    irq_set_priority(IRQ_PENDSV, 7);    /* Priority 7 = أدنى */
    irq_set_priority(IRQ_SYSTICK, 6);

    /* تهيئة SysTick @ 1kHz */
    systick_init(RTOS_CPU_FREQ_HZ, RTOS_TICK_RATE_HZ);

    /* اختر المهمة الأولى */
    g_current_tcb = scheduler_get_next_tcb();

    /* انتقل لـ Thread Mode + PSP
     * [1] ضع PSP = top of first task's stack
     * [2] اضبط CONTROL.SPSEL = 1 (استخدم PSP في Thread Mode)
     * [3] اقفز لدالة المهمة الأولى
     */
    __asm volatile(
        "ldr  r0, =g_current_tcb      \n"
        "ldr  r0, [r0]                \n"  /* r0 = TCB* */
        "ldr  r0, [r0, #0]            \n"  /* r0 = TCB->stack_ptr */
        /* استعِد r4-r11 من Stack */
        "ldmia r0!, {r4-r11}          \n"
        /* ضع PSP */
        "msr  psp, r0                 \n"
        "isb                          \n"
        /* CONTROL = 0x03 → Thread+PSP+unprivileged */
        "mov  r0, #0x03               \n"
        "msr  control, r0             \n"
        "isb                          \n"
        /* تفعيل المقاطعات */
        "cpsie i                      \n"
        /* EXC_RETURN = 0xFFFFFFFD → Thread Mode با PSP */
        "ldr  lr, =0xFFFFFFFD         \n"
        "bx   lr                      \n"
        ::: "r0", "r4", "r5", "r6", "r7", "r8", "r9", "r10", "r11", "lr"
    );
    /* هنا لا نصل أبداً */
    for(;;);
}

/* =============================================================================
 * SysTick_Handler — يُستدعى كل 1ms
 * =============================================================================
 */
void SysTick_Handler(void)
{
    s_tick_count++;

    /* طلب PendSV لتبديل السياق */
    SCB_ICSR = PENDSVSET;
    hal_dsb();
}

/* =============================================================================
 * task_sleep_ms / task_sleep_ticks
 * =============================================================================
 */
void task_sleep_ticks(uint32_t ticks)
{
    uint32_t saved = hal_enter_critical();
    if (g_current_tcb) {
        g_current_tcb->sleep_until_tick = s_tick_count + ticks;
        g_current_tcb->state = TASK_SLEEPING;
    }
    hal_exit_critical(saved);

    /* طلب تبديل السياق فوراً */
    SCB_ICSR = PENDSVSET;
    hal_dsb();
    __asm volatile("isb");
}

void task_sleep_ms(uint32_t ms)
{
    task_sleep_ticks(ms);
}

/* =============================================================================
 * task_yield
 * =============================================================================
 */
void task_yield(void)
{
    SCB_ICSR = PENDSVSET;
    hal_dsb();
    __asm volatile("isb");
}

/* =============================================================================
 * scheduler_check_stack_overflow
 * =============================================================================
 */
const char* scheduler_check_stack_overflow(void)
{
    TCB_t *t = s_task_list;
    while (t) {
        uint32_t *guard = (uint32_t*)t->stack_base;
        if (*guard != 0xDEADBEEF) {
            return t->name;
        }
        t = t->next;
    }
    return NULL;
}

/* =============================================================================
 * scheduler_get_stats
 * =============================================================================
 */
uint8_t scheduler_get_stats(task_stats_t *buf, uint8_t max_tasks)
{
    uint8_t count = 0;
    TCB_t *t = s_task_list;

    while (t && count < max_tasks) {
        /* احسب Stack usage: ابحث عن أبعد نقطة من القاعدة مملوءة */
        uint32_t *p = (uint32_t*)t->stack_base;
        uint32_t free_words = 0;
        while (*p == 0x00000000 || *p == 0xDEADBEEF) {
            free_words++;
            p++;
        }
        uint32_t stack_words = t->stack_size / 4;
        uint32_t used = (stack_words - free_words) * 4;
        uint32_t free = free_words * 4;

        buf[count].name            = t->name;
        buf[count].state           = t->state;
        buf[count].priority        = t->priority;
        buf[count].run_count       = t->run_count;
        buf[count].stack_used_bytes= used;
        buf[count].stack_free_bytes= free;
        buf[count].cpu_percent     = s_total_runtime ?
            ((float)t->total_runtime_us / s_total_runtime) * 100.0f : 0.0f;

        count++;
        t = t->next;
    }
    return count;
}

uint32_t scheduler_get_tick_count(void)
{
    return s_tick_count;
}

/* =============================================================================
 * Mutex
 * =============================================================================
 */

void mutex_init(mutex_t *m, const char *name)
{
    m->lock  = 0;
    m->owner = NULL;
    m->name  = name;
}

bool mutex_trylock(mutex_t *m)
{
    uint32_t result;
    __asm volatile(
        "ldrex   r0, [%1]      \n"  /* Load Exclusive */
        "cmp     r0, #0        \n"  /* هل حر؟ */
        "bne     1f            \n"  /* إذا مقفل → فشل */
        "movs    r0, #1        \n"
        "strex   %0, r0, [%1]  \n"  /* Store Exclusive */
        "b       2f            \n"
        "1: mov  %0, #1        \n"  /* فشل */
        "2:                    \n"
        : "=r"(result)
        : "r"(&m->lock)
        : "r0", "memory"
    );
    if (result == 0) {
        m->owner = g_current_tcb;
        return true;
    }
    return false;
}

bool mutex_lock(mutex_t *m, uint32_t timeout_ms)
{
    uint32_t deadline = scheduler_get_tick_count() + timeout_ms;
    while (!mutex_trylock(m)) {
        if (scheduler_get_tick_count() >= deadline) return false;
        task_yield();
    }
    return true;
}

void mutex_unlock(mutex_t *m)
{
    m->owner = NULL;
    __asm volatile("str %0, [%1]\n" :: "r"(0), "r"(&m->lock) : "memory");
}

/* =============================================================================
 * Semaphore
 * =============================================================================
 */

void sem_init(semaphore_t *s, int32_t init_count, int32_t max_count, const char *name)
{
    s->count     = init_count;
    s->max_count = max_count;
    s->name      = name;
}

bool sem_take(semaphore_t *s, uint32_t timeout_ms)
{
    uint32_t deadline = scheduler_get_tick_count() + timeout_ms;
    for (;;) {
        uint32_t saved = hal_enter_critical();
        if (s->count > 0) {
            s->count--;
            hal_exit_critical(saved);
            return true;
        }
        hal_exit_critical(saved);
        if (scheduler_get_tick_count() >= deadline) return false;
        task_yield();
    }
}

void sem_give(semaphore_t *s)
{
    uint32_t saved = hal_enter_critical();
    if (s->count < s->max_count) s->count++;
    hal_exit_critical(saved);
}

void sem_give_from_isr(semaphore_t *s)
{
    /* من داخل ISR: لا نستطيع yield — فقط رفع العدد */
    if (s->count < s->max_count) s->count++;
}
