/**
 * Timer Driver Header File
 * وحدة المؤقتات
 */

#ifndef TIMER_H
#define TIMER_H

#include <stdint.h>
#include <stdbool.h>

/* Timer Numbers */
typedef enum {
    TIMER_0 = 0,
    TIMER_1 = 1,
    TIMER_2 = 2,
    TIMER_MAX = 3
} timer_t;

/* Timer Modes */
typedef enum {
    TIMER_MODE_ONE_SHOT = 0,
    TIMER_MODE_PERIODIC = 1
} timer_mode_t;

/* Timer Prescaler */
typedef enum {
    TIMER_PRESCALE_1 = 1,
    TIMER_PRESCALE_8 = 8,
    TIMER_PRESCALE_64 = 64,
    TIMER_PRESCALE_256 = 256,
    TIMER_PRESCALE_1024 = 1024
} timer_prescale_t;

/* Timer Configuration */
typedef struct {
    timer_t timer;
    timer_mode_t mode;
    timer_prescale_t prescale;
    uint32_t period_us;  /* Period in microseconds */
    void (*callback)(timer_t);  /* Timer callback */
} timer_config_t;

/* Timer Handler */
typedef struct {
    timer_t timer;
    timer_mode_t mode;
    timer_prescale_t prescale;
    uint32_t period_us;
    bool enabled;
    uint32_t tick_count;
    uint32_t overflow_count;
} timer_handler_t;

/* Prototypes */

/**
 * Initialize timer driver
 * تهيئة وحدة المؤقتات
 */
int timer_init(void);

/**
 * Deinitialize timer driver
 * إيقاف وحدة المؤقتات
 */
int timer_deinit(void);

/**
 * Configure timer
 * تكوين مؤقت
 * @param config Timer configuration
 * @return 0 on success, -1 on error
 */
int timer_configure(const timer_config_t *config);

/**
 * Start timer
 * بدء مؤقت
 * @param timer Timer number
 * @return 0 on success, -1 on error
 */
int timer_start(timer_t timer);

/**
 * Stop timer
 * إيقاف مؤقت
 * @param timer Timer number
 * @return 0 on success, -1 on error
 */
int timer_stop(timer_t timer);

/**
 * Get timer value
 * الحصول على قيمة المؤقت
 * @param timer Timer number
 * @param value Pointer to store timer value
 * @return 0 on success, -1 on error
 */
int timer_get_value(timer_t timer, uint32_t *value);

/**
 * Set timer period
 * تعيين فترة المؤقت
 * @param timer Timer number
 * @param period_us Period in microseconds
 * @return 0 on success, -1 on error
 */
int timer_set_period(timer_t timer, uint32_t period_us);

/**
 * Get timer handler
 * الحصول على معالج المؤقت
 * @param timer Timer number
 * @return Pointer to timer handler, NULL if not found
 */
timer_handler_t* timer_get_handler(timer_t timer);

/**
 * Dump timer statistics
 * عرض إحصائيات المؤقتات
 */
void timer_dump_stats(void);

/**
 * Clock tick (should be called from interrupt)
 * نبضة الساعة
 */
void timer_tick(void);

#endif /* TIMER_H */
