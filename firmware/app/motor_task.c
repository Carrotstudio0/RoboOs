/**
 * @file motor_task.c
 * @brief Motor Control via PWM — RTOS Task
 *
 * يقرأ g_imu_data كل 20ms ويحسب قيم PWM للمحركين.
 * يطبق خوارزمية balance بسيطة بناءً على زاوية الميل.
 */

#include "motor_task.h"
#include "sensor_task.h"
#include "../kernel/scheduler.h"

/* ASM Math للـ PID */
extern int32_t asm_pid_update(int32_t error, int32_t *pid_state);
extern int32_t asm_clamp(int32_t val, int32_t min, int32_t max);

/* TIM4 Registers (APB1 @ 84MHz → Timer @ 168MHz مع prescaler) */
#define TIM4_BASE   0x40000800UL
#define TIM4_CR1    (*((volatile uint32_t*)(TIM4_BASE + 0x00)))
#define TIM4_PSC    (*((volatile uint32_t*)(TIM4_BASE + 0x28)))
#define TIM4_ARR    (*((volatile uint32_t*)(TIM4_BASE + 0x2C)))
#define TIM4_CCR1   (*((volatile uint32_t*)(TIM4_BASE + 0x34)))
#define TIM4_CCR2   (*((volatile uint32_t*)(TIM4_BASE + 0x38)))
#define TIM4_CCMR1  (*((volatile uint32_t*)(TIM4_BASE + 0x18)))
#define TIM4_CCER   (*((volatile uint32_t*)(TIM4_BASE + 0x20)))
#define RCC_APB1ENR (*((volatile uint32_t*)0x40023840))
#define RCC_TIM4EN  (1 << 2)

/* GPIOD ODR لـ Direction Pins */
#define GPIOD_ODR   (*((volatile uint32_t*)0x40020C14))

/* =============================================================================
 * تهيئة PWM على TIM4
 * =============================================================================
 */
static void pwm_init(void)
{
    /* تفعيل TIM4 */
    RCC_APB1ENR |= RCC_TIM4EN;

    /* Prescaler: 168MHz / (167+1) = 1 MHz timer clock */
    TIM4_PSC = 167;

    /* Auto-Reload: period = 1000 → 1 kHz PWM frequency */
    TIM4_ARR = 999;

    /* CH1 & CH2: PWM Mode 1 (OC1M = 110) */
    TIM4_CCMR1 = (6 << 4) | (6 << 12);  /* OC1M=110, OC2M=110 */
    TIM4_CCER  = (1 << 0) | (1 << 4);   /* CC1E, CC2E */

    /* ابدأ بـ 0% */
    TIM4_CCR1 = 0;
    TIM4_CCR2 = 0;

    /* تفعيل Timer */
    TIM4_CR1 = 1;
}

/* =============================================================================
 * motor_set_speed
 * =============================================================================
 */
void motor_set_speed(motor_id_t id, int8_t speed_percent)
{
    /* clamp لـ -100..100 */
    if (speed_percent >  100) speed_percent =  100;
    if (speed_percent < -100) speed_percent = -100;

    /* اتجاه الحركة */
    uint8_t forward = (speed_percent >= 0);
    uint32_t duty = (uint32_t)(forward ? speed_percent : -speed_percent);
    duty = (duty * 999) / 100;  /* تحويل % → CCR value */

    if (id == MOTOR_LEFT) {
        /* Direction pin */
        if (forward) GPIOD_ODR |= (1 << MOTOR_LEFT_DIR_PIN);
        else         GPIOD_ODR &= ~(1 << MOTOR_LEFT_DIR_PIN);
        TIM4_CCR1 = duty;
    } else {
        if (forward) GPIOD_ODR |= (1 << MOTOR_RIGHT_DIR_PIN);
        else         GPIOD_ODR &= ~(1 << MOTOR_RIGHT_DIR_PIN);
        TIM4_CCR2 = duty;
    }
}

void motor_stop_all(void)
{
    TIM4_CCR1 = 0;
    TIM4_CCR2 = 0;
}

/* =============================================================================
 * motor_task_entry — Balance + Forward Control كل 20ms (50Hz)
 * =============================================================================
 */
void motor_task_entry(void)
{
    /* PID State: {Kp, Ki, Kd, integral, prev_error} (Q16.16) */
    int32_t pid_state[5] = {
        (int32_t)(2.0f * 65536),   /* Kp = 2.0 */
        (int32_t)(0.1f * 65536),   /* Ki = 0.1 */
        (int32_t)(0.5f * 65536),   /* Kd = 0.5 */
        0,                          /* integral */
        0,                          /* prev_error */
    };

    /* انتظر بيانات الحساس */
    task_sleep_ms(200);
    pwm_init();

    for (;;) {
        /* اقرأ زاوية الميل من IMU */
        float ax = (float)g_imu_data.accel_x;
        float az = (float)g_imu_data.accel_z;

        /* زاوية الميل تقريبياً (بدون atan2) */
        /* error = target_angle - current_angle ≈ ax/az * some_factor */
        int32_t error_q16 = (int32_t)(ax * 65536.0f);

        /* PID بالأسمبلي */
        int32_t output = asm_pid_update(error_q16, pid_state);
        output = asm_clamp(output >> 11, -100, 100);

        /* تطبيق على المحركين */
        motor_set_speed(MOTOR_LEFT,  (int8_t)output);
        motor_set_speed(MOTOR_RIGHT, (int8_t)output);

        task_sleep_ms(20);  /* 50 Hz control loop */
    }
}
