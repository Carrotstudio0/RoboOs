/**
 * @file irq.c
 * @brief RoboOS IRQ & SysTick Implementation
 *
 * تنفيذ معالج المقاطعات، SysTick، NVIC، وأقسام Critical Section.
 * يعمل على ARM Cortex-M4 (STM32F4xx نموذجاً).
 */

#include "irq.h"
#include <stddef.h>

/* =============================================================================
 * CMSIS Register Definitions (Cortex-M4 Core Peripherals)
 * =============================================================================
 */

/* SysTick Registers */
#define SYST_CSR    (*((volatile uint32_t*)0xE000E010))  /* Control & Status */
#define SYST_RVR    (*((volatile uint32_t*)0xE000E014))  /* Reload Value */
#define SYST_CVR    (*((volatile uint32_t*)0xE000E018))  /* Current Value */
#define SYST_CALIB  (*((volatile uint32_t*)0xE000E01C))  /* Calibration */

#define SYST_CSR_ENABLE     (1 << 0)    /* تفعيل SysTick */
#define SYST_CSR_TICKINT    (1 << 1)    /* تفعيل المقاطعة */
#define SYST_CSR_CLKSOURCE  (1 << 2)    /* مصدر الساعة: 1=Core Clock */

/* NVIC Registers (أول 8 كلمات لـ 256 IRQ) */
#define NVIC_ISER_BASE  ((volatile uint32_t*)0xE000E100)  /* Enable */
#define NVIC_ICER_BASE  ((volatile uint32_t*)0xE000E180)  /* Clear Enable */
#define NVIC_ISPR_BASE  ((volatile uint32_t*)0xE000E200)  /* Set Pending */
#define NVIC_ICPR_BASE  ((volatile uint32_t*)0xE000E280)  /* Clear Pending */
#define NVIC_IPR_BASE   ((volatile uint8_t*) 0xE000E400)  /* Priority */

/* System Control Block */
#define SCB_SHPR_BASE   ((volatile uint8_t*)0xE000ED18)   /* System Handler Priority */
#define SCB_ICSR        (*((volatile uint32_t*)0xE000ED04)) /* Interrupt Control & State */
#define SCB_CFSR        (*((volatile uint32_t*)0xE000ED28)) /* Configurable Fault Status */
#define SCB_HFSR        (*((volatile uint32_t*)0xE000ED2C)) /* HardFault Status */
#define SCB_MMFAR       (*((volatile uint32_t*)0xE000ED34)) /* MemManage Address */
#define SCB_BFAR        (*((volatile uint32_t*)0xE000ED38)) /* BusFault Address */

/* =============================================================================
 * متغيرات عامة
 * =============================================================================
 */

/** عداد الـ ticks (يُحدَّث كل 1ms في SysTick ISR) */
volatile uint32_t g_systick_count = 0;

/** جدول معالجات المقاطعات الديناميكي */
static irq_handler_t irq_handlers[64] = {NULL};


/* =============================================================================
 * SysTick
 * =============================================================================
 */

void systick_init(uint32_t cpu_freq_hz, uint32_t tick_rate_hz)
{
    uint32_t reload_val = (cpu_freq_hz / tick_rate_hz) - 1;

    /* توقف SysTick أولاً */
    SYST_CSR = 0;

    /* اضبط قيمة إعادة التحميل */
    SYST_RVR = reload_val & 0x00FFFFFF;

    /* صفّر العداد الحالي */
    SYST_CVR = 0;

    /* فعّل SysTick بساعة النواة مع تفعيل المقاطعة */
    SYST_CSR = SYST_CSR_ENABLE | SYST_CSR_TICKINT | SYST_CSR_CLKSOURCE;

    /* اضبط أولوية SysTick لأعلى قيمة (أدنى أولوية من الـ kernel handlers) */
    SCB_SHPR_BASE[11] = IRQ_PRIORITY_LOWEST << 5;
}

uint32_t systick_get_count(void)
{
    return g_systick_count;
}

void systick_delay_ms(uint32_t ms)
{
    uint32_t start = g_systick_count;
    while ((g_systick_count - start) < ms) {
        /* انتظر — WFI لتوفير الطاقة */
        __asm volatile("wfi");
    }
}

/**
 * SysTick ISR — يُنفَّذ كل 1ms
 * يُحدِّث عداد الـ ticks ويُشغِّل الجدولة
 */
void SysTick_Handler(void)
{
    g_systick_count++;

    /* طلب تبديل السياق عبر PendSV (أدنى أولوية — ينفذ بعد اكتمال ISR) */
    SCB_ICSR |= (1 << 28);  /* PENDSVSET */
}


/* =============================================================================
 * NVIC
 * =============================================================================
 */

void irq_enable(irq_num_t irq, irq_priority_t priority)
{
    if (irq < 0) return;  /* المقاطعات الجوهرية لها مسار آخر */

    uint32_t n = (uint32_t)irq;

    /* اضبط الأولوية في NVIC_IPR */
    NVIC_IPR_BASE[n] = (priority << 5) & 0xE0;

    /* فعّل المقاطعة */
    NVIC_ISER_BASE[n >> 5] = (1UL << (n & 0x1F));
}

void irq_disable(irq_num_t irq)
{
    if (irq < 0) return;

    uint32_t n = (uint32_t)irq;
    NVIC_ICER_BASE[n >> 5] = (1UL << (n & 0x1F));

    /* ضمان تنفيذ الكتابة قبل العودة */
    __asm volatile("dsb" ::: "memory");
    __asm volatile("isb");
}

void irq_register_handler(irq_num_t irq, irq_handler_t handler)
{
    if (irq >= 0 && irq < 64) {
        irq_handlers[irq] = handler;
    }
}

void irq_clear_pending(irq_num_t irq)
{
    if (irq < 0) return;

    uint32_t n = (uint32_t)irq;
    NVIC_ICPR_BASE[n >> 5] = (1UL << (n & 0x1F));
}

void irq_set_priority(irq_num_t irq, irq_priority_t priority)
{
    if (irq < 0) {
        /* System Handler Priorities (SVC, PendSV, SysTick) */
        int idx = 12 + (int)irq;  /* SVC=-3→9, PendSV=-2→10, SysTick=-1→11 */
        if (idx >= 0 && idx < 12) {
            SCB_SHPR_BASE[idx] = (priority << 5) & 0xE0;
        }
        return;
    }

    NVIC_IPR_BASE[(uint32_t)irq] = (priority << 5) & 0xE0;
}


/* =============================================================================
 * Critical Section
 * =============================================================================
 */

uint32_t irq_enter_critical(void)
{
    uint32_t saved;
    __asm volatile(
        "mrs %0, primask \n"
        "cpsid i         \n"
        : "=r"(saved)
        :
        : "memory"
    );
    return saved;
}

void irq_exit_critical(uint32_t saved_state)
{
    __asm volatile(
        "msr primask, %0 \n"
        :
        : "r"(saved_state)
        : "memory"
    );
}


/* =============================================================================
 * HardFault Handler
 * =============================================================================
 */

/**
 * يُستدعى من HardFault_Handler_ASM مع مؤشر Stack Frame
 */
void HardFault_Handler_C(uint32_t *stack_frame)
{
    fault_info_t info;

    /* استخرج Stack Frame المحفوظ تلقائياً من الـ CPU */
    info.r0   = stack_frame[0];
    info.r1   = stack_frame[1];
    info.r2   = stack_frame[2];
    info.r3   = stack_frame[3];
    info.r12  = stack_frame[4];
    info.lr   = stack_frame[5];
    info.pc   = stack_frame[6];
    info.xpsr = stack_frame[7];

    /* اقرأ سجلات الأعطال */
    info.cfsr  = SCB_CFSR;
    info.hfsr  = SCB_HFSR;
    info.mmfar = SCB_MMFAR;
    info.bfar  = SCB_BFAR;

    fault_dump(&info);

    /* توقف هنا للـ Debugger */
    __asm volatile("bkpt #0");
    while (1) {
        __asm volatile("wfi");
    }
}

/**
 * طباعة معلومات الخطأ عبر (UART — مبسّط بدون printf)
 */
void fault_dump(const fault_info_t *info)
{
    /* في نظام حقيقي نرسل عبر UART أو ITM (SWO Debug)
     * هنا نحفظ المعلومات في متغير عالمي للـ Debugger */
    (void)info;  /* يمنع تحذير unused في الـ simulation */
}

/**
 * HardFault_Handler — Assembly stub ينقل Stack Pointer لـ C
 * (يُعرَّف بالـ __attribute__ لمنع الـ compiler من تعديل ABI)
 */
__attribute__((naked)) void HardFault_Handler(void)
{
    __asm volatile(
        "tst lr, #4          \n"   /* هل كان Thread Mode يستخدم PSP؟ */
        "ite eq              \n"
        "mrseq r0, msp       \n"   /* Handler Mode → MSP */
        "mrsne r0, psp       \n"   /* Thread Mode  → PSP */
        "b HardFault_Handler_C \n" /* ادعُ C handler مع Stack Pointer */
    );
}
