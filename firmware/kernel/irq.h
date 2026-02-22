/**
 * @file irq.h
 * @brief RoboOS Interrupt & System Tick Management
 *
 * واجهة معالج المقاطعات ودعم السيستم تيك لنواة RoboOS.
 * يعمل هذا الملف جنباً مع ملفات الأسمبلي (isr_vectors.s, context_switch.s).
 */

#ifndef ROBOOS_IRQ_H
#define ROBOOS_IRQ_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* =============================================================================
 * أنواع وثوابت
 * =============================================================================
 */

/** أولوية المقاطعة: أعلى قيمة = أعلى أولوية */
typedef uint8_t irq_priority_t;

#define IRQ_PRIORITY_HIGHEST    0
#define IRQ_PRIORITY_CRITICAL   1
#define IRQ_PRIORITY_HIGH       2
#define IRQ_PRIORITY_NORMAL     4
#define IRQ_PRIORITY_LOW        6
#define IRQ_PRIORITY_LOWEST     7

/** نوع دالة معالج المقاطعة */
typedef void (*irq_handler_t)(void);

/** أرقام IRQ المدعومة */
typedef enum {
    IRQ_SYSTICK    = -1,    /* SysTick — توليد RTOS ticks */
    IRQ_PENDSV     = -2,    /* PendSV  — تبديل السياق */
    IRQ_SVC        = -3,    /* SVC     — System Calls */
    IRQ_USART1     = 37,
    IRQ_USART2     = 38,
    IRQ_TIM2       = 28,
    IRQ_TIM3       = 29,
    IRQ_TIM4       = 30,
    IRQ_SPI1       = 35,
    IRQ_SPI2       = 36,
    IRQ_I2C1_EV    = 31,
    IRQ_ADC        = 18,
    IRQ_EXTI0      = 6,
    IRQ_EXTI1      = 7,
    IRQ_EXTI2      = 8,
    IRQ_EXTI3      = 9,
    IRQ_EXTI4      = 10,
} irq_num_t;


/* =============================================================================
 * SysTick — مؤقت النواة
 * =============================================================================
 */

/**
 * @brief تهيئة SysTick
 * @param cpu_freq_hz  تردد المعالج بالهرتز
 * @param tick_rate_hz عدد الـ ticks في الثانية (عادةً 1000 = 1ms)
 */
void systick_init(uint32_t cpu_freq_hz, uint32_t tick_rate_hz);

/** عداد الـ ticks العام (يُحدَّث في كل interrupt) */
volatile uint32_t g_systick_count;

/** @brief قراءة عداد الـ ticks الحالي */
uint32_t systick_get_count(void);

/** @brief تأخير بالميلي-ثانية */
void systick_delay_ms(uint32_t ms);

/** @brief معالج الـ SysTick (يُستدعى من ISR) */
void SysTick_Handler(void);


/* =============================================================================
 * NVIC — Nested Vectored Interrupt Controller
 * =============================================================================
 */

/**
 * @brief تفعيل مقاطعة
 * @param irq      رقم المقاطعة
 * @param priority الأولوية (0 = أعلى)
 */
void irq_enable(irq_num_t irq, irq_priority_t priority);

/**
 * @brief تعطيل مقاطعة
 */
void irq_disable(irq_num_t irq);

/**
 * @brief تسجيل معالج لمقاطعة معينة
 */
void irq_register_handler(irq_num_t irq, irq_handler_t handler);

/**
 * @brief مسح علامة المقاطعة (Pending Flag)
 */
void irq_clear_pending(irq_num_t irq);

/**
 * @brief ضبط أولوية المقاطعة
 */
void irq_set_priority(irq_num_t irq, irq_priority_t priority);


/* =============================================================================
 * Critical Section — حماية الأقسام الحرجة
 * =============================================================================
 */

/** @brief دخول قسم حرج (تعطيل مقاطعات + إرجاع الحالة السابقة) */
uint32_t irq_enter_critical(void);

/** @brief خروج من قسم حرج (استعادة الحالة السابقة) */
void irq_exit_critical(uint32_t saved_state);

/* ماكرو للاستخدام المريح */
#define CRITICAL_SECTION_ENTER() uint32_t __irq_save = irq_enter_critical()
#define CRITICAL_SECTION_EXIT()  irq_exit_critical(__irq_save)


/* =============================================================================
 * Fault Handlers — تشخيص الأعطال
 * =============================================================================
 */

/** معلومات الـ HardFault لأغراض التشخيص */
typedef struct {
    uint32_t r0, r1, r2, r3, r12;
    uint32_t lr, pc, xpsr;
    uint32_t cfsr;   /* Configurable Fault Status Register */
    uint32_t hfsr;   /* HardFault Status Register */
    uint32_t mmfar;  /* MemManage Fault Address Register */
    uint32_t bfar;   /* BusFault Address Register */
} fault_info_t;

/** @brief معالج HardFault — يملأ fault_info ويوقف النظام */
void HardFault_Handler(void);

/** @brief طباعة معلومات الخطأ عبر UART للتشخيص */
void fault_dump(const fault_info_t *info);

#ifdef __cplusplus
}
#endif

#endif /* ROBOOS_IRQ_H */
