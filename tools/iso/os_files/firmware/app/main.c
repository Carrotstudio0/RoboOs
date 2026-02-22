/**
 * @file main.c
 * @brief RoboOS — Application Main Entry
 *
 * نقطة دخول النظام بعد boot.s:
 *   1. تهيئة الساعة والمحيطات الأساسية
 *   2. إنشاء مهام RTOS الرئيسية
 *   3. بدء الجدولة — لا تعود أبداً
 *
 * المهام:
 *   ┌─────────────────────────────────────────────┐
 *   │  led_task     — وميض LED كـ Heartbeat       │
 *   │  sensor_task  — قراءة MPU-6050 عبر I2C      │
 *   │  motor_task   — تحكم بالمحركات عبر PWM      │
 *   │  comm_task    — طباعة بيانات عبر UART       │
 *   │  idle_task    — WFI لتوفير الطاقة (تلقائي)  │
 *   └─────────────────────────────────────────────┘
 */

#include "scheduler.h"
#include "irq.h"
#include "../drivers/gpio/gpio.h"
#include "../drivers/uart/uart.h"
#include "../drivers/i2c/i2c.h"
#include "../drivers/adc/adc.h"
#include "../drivers/timer/timer.h"

/* ---- Headers للمهام -------------------------------------------------------- */
#include "led_task.h"
#include "sensor_task.h"
#include "motor_task.h"
#include "comm_task.h"

/* =============================================================================
 * Stack Allocations — static (لا malloc)
 * =============================================================================
 */
static uint32_t led_stack   [512  / 4];
static uint32_t sensor_stack[2048 / 4];
static uint32_t motor_stack [1024 / 4];
static uint32_t comm_stack  [1024 / 4];

/* =============================================================================
 * SystemInit — تهيئة ساعة MCU إلى 168 MHz
 * (يُشغَّل من boot.s قبل main)
 * =============================================================================
 */
void SystemInit(void)
{
    /* STM32F407: تفعيل HSE + PLL للوصول لـ 168 MHz
     * RCC Base = 0x40023800
     */
    volatile uint32_t *RCC_CR      = (volatile uint32_t*)0x40023800;
    volatile uint32_t *RCC_PLLCFGR = (volatile uint32_t*)0x40023804;
    volatile uint32_t *RCC_CFGR    = (volatile uint32_t*)0x40023808;
    volatile uint32_t *FLASH_ACR   = (volatile uint32_t*)0x40023C00;

    /* [1] تفعيل HSE (8 MHz crystal) */
    *RCC_CR |= (1 << 16);  /* HSEON */
    while (!(*RCC_CR & (1 << 17)));  /* انتظر HSERDY */

    /* [2] Flash Latency = 5 wait states (لـ 168MHz @ 3.3V) */
    *FLASH_ACR = (1 << 10) | (1 << 9) | 5;  /* ICEN | DCEN | LATENCY=5 */

    /* [3] تهيئة PLL: HSE/8 × 336 / 2 = 168 MHz */
    *RCC_PLLCFGR = (4   << 0)   |  /* PLLM = 4 (HSE=8MHz → 2MHz VCO input) */
                   (168 << 6)   |  /* PLLN = 168 (VCO = 336 MHz) */
                   (0   << 16)  |  /* PLLP = /2 → 168 MHz */
                   (1   << 22)  |  /* PLLSRC = HSE */
                   (7   << 24);    /* PLLQ = 7 (USB = 48 MHz) */

    /* [4] تفعيل PLL */
    *RCC_CR |= (1 << 24);  /* PLLON */
    while (!(*RCC_CR & (1 << 25)));  /* انتظر PLLRDY */

    /* [5] ضبط AHB/APB prescalers: AHB/1, APB1/4, APB2/2 */
    *RCC_CFGR = (0  << 4)  |  /* HPRE  = AHB/1 */
                (5  << 10) |  /* PPRE1 = APB1/4 → 42 MHz */
                (4  << 13);   /* PPRE2 = APB2/2 → 84 MHz */

    /* [6] تحويل ساعة النظام لـ PLL */
    *RCC_CFGR |= (2 << 0);  /* SW = PLL */
    while ((*RCC_CFGR & (3 << 2)) != (2 << 2));  /* انتظر SWS = PLL */
}

/* =============================================================================
 * هيئ UART للـ Debug logging
 * =============================================================================
 */
static void init_debug_uart(void)
{
    uart_config_t uart_cfg = {
        .port     = UART_PORT_1,
        .baudrate = 115200,
        .use_dma  = false,
    };
    uart_init(&uart_cfg);
}

/* =============================================================================
 * هيئ I2C لحساس IMU
 * =============================================================================
 */
static void init_i2c_bus(void)
{
    i2c_config_t i2c_cfg = {
        .port       = I2C_PORT_1,
        .speed      = I2C_SPEED_FAST,    /* 400 kHz */
        .timeout_ms = 10,
        .use_dma    = false,
    };
    i2c_init(&i2c_cfg);
}

/* =============================================================================
 * هيئ ADC لقراءة الحساسات التناظرية
 * =============================================================================
 */
static void init_adc(void)
{
    adc_config_t adc_cfg = {
        .port          = ADC_PORT_1,
        .resolution    = ADC_RESOLUTION_12BIT,
        .continuous    = false,
        .scan_mode     = true,
        .use_dma       = false,
        .num_channels  = 3,
        .channels = {
            {ADC_CHANNEL_0, ADC_SAMPLETIME_56, 1},  /* PA0 — IR Sensor */
            {ADC_CHANNEL_1, ADC_SAMPLETIME_56, 2},  /* PA1 — Battery   */
            {ADC_CHANNEL_2, ADC_SAMPLETIME_56, 3},  /* PA2 — Joystick  */
        },
    };
    adc_calibrate(ADC_PORT_1);
    adc_init(&adc_cfg);
}

/* =============================================================================
 * main — نقطة الدخول الحقيقية
 * =============================================================================
 */
int main(void)
{
    /* ---- 1. تهيئة المحيطات الأساسية ------------------------------------ */
    irq_enable(IRQ_USART1, IRQ_PRIORITY_NORMAL);
    init_debug_uart();
    init_i2c_bus();
    init_adc();

    /* ---- 2. تهيئة نواة RTOS -------------------------------------------- */
    scheduler_init();

    /* ---- 3. إنشاء المهام ----------------------------------------------- */
    task_create("led",    led_task_entry,    TASK_PRIORITY_LOW,
                led_stack,    sizeof(led_stack));

    task_create("sensor", sensor_task_entry, TASK_PRIORITY_HIGH,
                sensor_stack, sizeof(sensor_stack));

    task_create("motor",  motor_task_entry,  TASK_PRIORITY_NORMAL,
                motor_stack,  sizeof(motor_stack));

    task_create("comm",   comm_task_entry,   TASK_PRIORITY_LOW,
                comm_stack,   sizeof(comm_stack));

    /* ---- 4. بدء الجدولة — لا تعود ---------------------------------------- */
    scheduler_start();

    /* هنا لا نصل أبداً */
    for (;;) {
        __asm volatile("wfi");
    }
}
