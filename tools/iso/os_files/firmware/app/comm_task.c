/**
 * @file comm_task.c
 * @brief UART Logging & Debug Output — RTOS Task
 *
 * يطبع كل ثانية:
 *   - IMU data (Accel + Gyro + Temp)
 *   - RTOS task stats (CPU%, Stack usage)
 *   - System tick & uptime
 *
 * صيغة الإخراج (Telemetry Protocol):
 *   IMU:ax=+1.02,ay=-0.03,az=+0.98,gx=+0.1,gy=-0.2,gz=+0.0,T=25.3
 *   TASK:led,READY,0,500,1024,1024,0.3%
 *   TICK:12500
 */

#include "comm_task.h"
#include "sensor_task.h"
#include "../kernel/scheduler.h"

/* UART1 Registers STM32F4 */
#define USART1_BASE  0x40011000UL
#define USART1_SR    (*((volatile uint32_t*)(USART1_BASE + 0x00)))
#define USART1_DR    (*((volatile uint32_t*)(USART1_BASE + 0x04)))
#define USART1_TXE   (1 << 7)
#define USART1_TC    (1 << 6)

/* =============================================================================
 * uart_putchar — إرسال حرف واحد (حجب)
 * =============================================================================
 */
static void uart_putchar(char c)
{
    while (!(USART1_SR & USART1_TXE));
    USART1_DR = (uint32_t)c;
}

/* =============================================================================
 * uart_puts — إرسال سلسلة (بدون printf)
 * =============================================================================
 */
static void uart_puts(const char *s)
{
    while (*s) uart_putchar(*s++);
}

/* =============================================================================
 * uart_put_int — تحويل uint32 لنص وإرسال
 * =============================================================================
 */
static void uart_put_uint(uint32_t n)
{
    char buf[11];
    int i = 10;
    buf[i] = '\0';
    if (n == 0) { uart_putchar('0'); return; }
    while (n > 0 && i > 0) {
        buf[--i] = '0' + (n % 10);
        n /= 10;
    }
    uart_puts(&buf[i]);
}

/* =============================================================================
 * uart_put_float — طباعة float بدون printf (2 خانات عشرية)
 * =============================================================================
 */
static void uart_put_float(float f)
{
    if (f < 0) { uart_putchar('-'); f = -f; }
    else        { uart_putchar('+'); }
    uint32_t intpart  = (uint32_t)f;
    uint32_t fracpart = (uint32_t)((f - (float)intpart) * 100.0f);
    uart_put_uint(intpart);
    uart_putchar('.');
    if (fracpart < 10) uart_putchar('0');
    uart_put_uint(fracpart);
}

/* =============================================================================
 * comm_task_entry — يُخرج بيانات كل ثانية
 * =============================================================================
 */
void comm_task_entry(void)
{
    /* انتظر استقرار النظام */
    task_sleep_ms(500);

    static const char *state_names[] = {
        "READY", "RUN", "BLOCK", "SLEEP", "SUSP", "TERM"
    };

    for (;;) {
        /* ---- بيانات IMU ------------------------------------------------- */
        uart_puts("\r\n--- RoboOS Telemetry ---\r\n");
        uart_puts("IMU:ax=");  uart_put_float(g_imu_data.accel_x);
        uart_puts(",ay=");     uart_put_float(g_imu_data.accel_y);
        uart_puts(",az=");     uart_put_float(g_imu_data.accel_z);
        uart_puts(",gx=");     uart_put_float(g_imu_data.gyro_x);
        uart_puts(",gy=");     uart_put_float(g_imu_data.gyro_y);
        uart_puts(",gz=");     uart_put_float(g_imu_data.gyro_z);
        uart_puts(",T=");      uart_put_float(g_imu_data.temp_c);
        uart_puts("\r\n");

        /* ---- إحصائيات المهام -------------------------------------------- */
        task_stats_t stats[8];
        uint8_t n = scheduler_get_stats(stats, 8);

        for (uint8_t i = 0; i < n; i++) {
            uart_puts("TASK:");
            uart_puts(stats[i].name);
            uart_putchar(',');
            uart_puts(state_names[(int)stats[i].state]);
            uart_putchar(',');
            uart_put_uint(stats[i].priority);
            uart_putchar(',');
            uart_put_uint(stats[i].run_count);
            uart_putchar(',');
            uart_put_uint(stats[i].stack_used_bytes);
            uart_putchar('/');
            uart_put_uint(stats[i].stack_used_bytes + stats[i].stack_free_bytes);
            uart_puts("B\r\n");
        }

        /* ---- System Tick ------------------------------------------------- */
        uart_puts("TICK:");
        uart_put_uint(scheduler_get_tick_count());
        uart_puts("\r\n");

        task_sleep_ms(1000);  /* 1 Hz logging */
    }
}
