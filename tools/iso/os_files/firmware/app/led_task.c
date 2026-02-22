/**
 * @file led_task.c
 * @brief LED Heartbeat + System Status Task
 */

#include "led_task.h"
#include "../kernel/scheduler.h"

/* Bit-Band helper من peripheral_asm.s */
extern void asm_gpio_bit_write(uint32_t gpio_odr_addr, uint32_t pin, uint32_t val);
extern const char* scheduler_check_stack_overflow(void);

/* GPIO GPIOD Registers */
#define GPIOD_MODER  (*((volatile uint32_t*)(LED_GPIO_PORT_BASE + 0x00)))
#define GPIOD_ODR    (*((volatile uint32_t*)(LED_GPIO_PORT_BASE + 0x14)))
#define RCC_AHB1ENR  (*((volatile uint32_t*)0x40023830))
#define RCC_GPIODEN  (1 << 3)

static void led_gpio_init(void)
{
    /* تفعيل ساعة GPIOD */
    RCC_AHB1ENR |= RCC_GPIODEN;
    /* ضبط PD12-PD15 كـ Output */
    GPIOD_MODER &= ~(0xFF << 24);       /* مسح */
    GPIOD_MODER |=  (0x55 << 24);       /* 01 = General Purpose Output لكل pin */
}

static void led_set(uint32_t pin, uint32_t val)
{
    /* استخدم Bit-Band الذري من الأسمبلي */
    asm_gpio_bit_write(LED_GPIO_PORT_BASE + 0x14, pin, val);
}

/* =============================================================================
 * led_task_entry — تعمل كـ Heartbeat
 * =============================================================================
 */
void led_task_entry(void)
{
    led_gpio_init();

    uint32_t tick = 0;

    for (;;) {
        tick++;

        /* Heartbeat: وميض LED الأخضر كل 500ms */
        led_set(LED_GREEN_PIN, tick & 1);

        /* فحص Stack Overflow */
        const char *overflow = scheduler_check_stack_overflow();
        if (overflow) {
            /* نمط طوارئ: وميض أحمر سريع */
            led_set(LED_RED_PIN, 1);
            task_sleep_ms(100);
            led_set(LED_RED_PIN, 0);
            task_sleep_ms(100);
            continue;
        }

        /* توضح الألوان حسب حالة النظام كل ثانية */
        if ((tick % 2) == 0) {
            led_set(LED_BLUE_PIN, 1);    /* نظام يعمل */
            task_sleep_ms(50);
            led_set(LED_BLUE_PIN, 0);
        }

        task_sleep_ms(500);
    }
}
