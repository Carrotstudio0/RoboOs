/**
 * @file motor_task.h / motor_task.c
 * @brief Motor Control Task via PWM + GPIO
 * تتحكم في سرعة واتجاه محركات الروبوت بناء على بيانات IMU.
 */

#ifndef MOTOR_TASK_H
#define MOTOR_TASK_H

#include <stdint.h>

/* أرقام المحركات */
typedef enum {
    MOTOR_LEFT  = 0,
    MOTOR_RIGHT = 1,
    MOTOR_COUNT
} motor_id_t;

/** Speed: -100 (عكسي) → 0 (توقف) → +100 (أمام) */
void motor_set_speed(motor_id_t id, int8_t speed_percent);
void motor_stop_all(void);
void motor_task_entry(void);

/* STM32F407: TIM4 PWM لمحركات DC */
#define MOTOR_LEFT_PWM_PIN   6   /* PD6 — TIM4 CH1 */
#define MOTOR_RIGHT_PWM_PIN  7   /* PD7 — TIM4 CH2 */
#define MOTOR_LEFT_DIR_PIN   8   /* PD8 — Direction */
#define MOTOR_RIGHT_DIR_PIN  9   /* PD9 — Direction */

#endif
