/**
 * @file led_task.h + led_task.c
 * @brief LED Heartbeat Task — Proof of Life
 * مهمة وميض LED كحارس حياة للنظام (Heartbeat).
 * تومض كل 500ms → تقرأ حالة النظام → تغير السرعة إذا كان هناك خطأ.
 */

#ifndef LED_TASK_H
#define LED_TASK_H

void led_task_entry(void);

/* LED Pins — STM32F407 Discovery Board */
#define LED_GREEN_PIN   12   /* PD12 — Green LED */
#define LED_ORANGE_PIN  13   /* PD13 — Orange LED */
#define LED_RED_PIN     14   /* PD14 — Red LED */
#define LED_BLUE_PIN    15   /* PD15 — Blue LED */
#define LED_GPIO_PORT_BASE  0x40020C00UL  /* GPIOD */

#endif
