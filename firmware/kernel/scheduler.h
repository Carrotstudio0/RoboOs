/**
 * @file scheduler.h
 * @brief RoboOS RTOS Kernel — Task & TCB Management
 *
 * هذا هو قلب الـ RTOS الحقيقي:
 *   - TCB (Task Control Block): كل مهمة لها stack منفصل + حالة + أولوية
 *   - context_switch.s يقرأ g_current_tcb و g_next_tcb مباشرة
 *   - SysTick → PendSV → scheduler_get_next_tcb() → تبديل السياق
 */

#ifndef ROBOOS_SCHEDULER_H
#define ROBOOS_SCHEDULER_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* =============================================================================
 * Constants
 * =============================================================================
 */

#define RTOS_MAX_TASKS          16      /* أقصى عدد مهام */
#define RTOS_MIN_STACK_BYTES    512     /* أصغر stack مسموح */
#define RTOS_DEFAULT_STACK_BYTES 2048   /* Stack افتراضي */
#define RTOS_TICK_RATE_HZ       1000    /* 1ms per tick */
#define RTOS_CPU_FREQ_HZ        168000000UL

/* أولويات المهام (كبير = أعلى) */
#define TASK_PRIORITY_IDLE      0
#define TASK_PRIORITY_LOW       1
#define TASK_PRIORITY_NORMAL    5
#define TASK_PRIORITY_HIGH      8
#define TASK_PRIORITY_REALTIME  15

/* =============================================================================
 * Task States
 * =============================================================================
 */

typedef enum {
    TASK_READY     = 0,
    TASK_RUNNING   = 1,
    TASK_BLOCKED   = 2,
    TASK_SLEEPING  = 3,
    TASK_SUSPENDED = 4,
    TASK_TERMINATED= 5,
} task_state_t;

/* =============================================================================
 * Task Control Block (TCB)
 * =============================================================================
 */

/**
 * IMPORTANT: stack_ptr دائماً أول عضو في الـ struct.
 * context_switch.s يفترض هذا الموضع ويصل إليه بـ offset 0.
 */
typedef struct TCB {
    uint32_t        *stack_ptr;         /* [offset=0x00] PSP المحفوظ — يجب أن يبقى أول عضو */
    /* -------------------------------------------------------------------- */
    char             name[16];          /* اسم المهمة للـ Debug */
    uint8_t          priority;          /* الأولوية (0-15) */
    task_state_t     state;
    uint32_t         sleep_until_tick;  /* تيك الاستيقاظ إذا كانت نائمة */
    uint32_t         run_count;         /* عدد مرات التنفيذ */
    uint32_t         total_runtime_us;  /* وقت التنفيذ الكلي */
    uint32_t         stack_base;        /* قاعدة الـ Stack للكشف عن Overflow */
    uint32_t         stack_size;        /* حجم الـ Stack */
    struct TCB      *next;              /* القائمة المترابطة */
} TCB_t;

/* =============================================================================
 * Global Scheduler State (يُصدَّر لـ context_switch.s)
 * =============================================================================
 */

/** المهمة الحالية — يقرأها context_switch.s مباشرة */
extern TCB_t *volatile g_current_tcb;

/* =============================================================================
 * Scheduler API
 * =============================================================================
 */

/**
 * @brief تهيئة النواة (يُستدعى مرة واحدة من main)
 */
void scheduler_init(void);

/**
 * @brief إنشاء مهمة جديدة
 * @param name        اسم للـ Debug
 * @param entry       نقطة دخول المهمة (void (*)(void))
 * @param priority    الأولوية
 * @param stack       مؤشر إلى ذاكرة الـ Stack
 * @param stack_size  حجم الـ Stack بالبايت
 * @return مؤشر الـ TCB الجديد (NULL عند الفشل)
 */
TCB_t* task_create(const char *name, void (*entry)(void),
                   uint8_t priority, uint32_t *stack, size_t stack_size);

/**
 * @brief بدء تشغيل الجدولة — لا تعود أبداً
 * يُفعِّل SysTick، يحمل PSP أول مهمة، ينتقل لـ Thread Mode
 */
void scheduler_start(void);

/**
 * @brief احصل على TCB التالي — يُستدعى من PendSV_Handler (context_switch.s)
 */
TCB_t* scheduler_get_next_tcb(void);

/**
 * @brief تأخير مهمة بعدد من الـ ticks
 */
void task_sleep_ticks(uint32_t ticks);

/**
 * @brief تأخير بالميلي-ثانية
 */
void task_sleep_ms(uint32_t ms);

/**
 * @brief تنازُل طوعي عن المعالج
 */
void task_yield(void);

/**
 * @brief فحص تجاوز Stack لكل المهام
 * @return اسم المهمة التي تجاوزت، أو NULL
 */
const char* scheduler_check_stack_overflow(void);

/**
 * @brief الحصول على إحصائيات المهام
 */
typedef struct {
    const char  *name;
    task_state_t state;
    uint8_t      priority;
    uint32_t     run_count;
    uint32_t     stack_used_bytes;
    uint32_t     stack_free_bytes;
    float        cpu_percent;
} task_stats_t;

uint8_t scheduler_get_stats(task_stats_t *buf, uint8_t max_tasks);

/**
 * @brief إجمالي ticks منذ بدء التشغيل
 */
uint32_t scheduler_get_tick_count(void);

/* =============================================================================
 * Mutex
 * =============================================================================
 */

typedef struct {
    volatile uint32_t   lock;   /* 0=حر, 1=مقفل — يُعدَّل بـ LDREX/STREX */
    TCB_t              *owner;
    const char         *name;
} mutex_t;

void mutex_init(mutex_t *m, const char *name);
bool mutex_lock(mutex_t *m, uint32_t timeout_ms);
void mutex_unlock(mutex_t *m);
bool mutex_trylock(mutex_t *m);

/* =============================================================================
 * Semaphore
 * =============================================================================
 */

typedef struct {
    volatile int32_t    count;
    int32_t             max_count;
    const char         *name;
} semaphore_t;

void sem_init(semaphore_t *s, int32_t init_count, int32_t max_count, const char *name);
bool sem_take(semaphore_t *s, uint32_t timeout_ms);
void sem_give(semaphore_t *s);
void sem_give_from_isr(semaphore_t *s);

#ifdef __cplusplus
}
#endif

#endif /* ROBOOS_SCHEDULER_H */
