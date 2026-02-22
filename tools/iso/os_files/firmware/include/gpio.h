/**
 * GPIO Driver Header File
 * وحدة التحكم بالدبابيس
 */

#ifndef GPIO_H
#define GPIO_H

#include <stdint.h>
#include <stdbool.h>

/* Pin Modes */
typedef enum {
    GPIO_MODE_INPUT = 0,
    GPIO_MODE_OUTPUT = 1,
    GPIO_MODE_INPUT_PULLUP = 2,
    GPIO_MODE_ANALOG = 3,
    GPIO_MODE_PWM = 4
} gpio_mode_t;

/* Pin Levels */
typedef enum {
    GPIO_LEVEL_LOW = 0,
    GPIO_LEVEL_HIGH = 1
} gpio_level_t;

/* Interrupt Modes */
typedef enum {
    GPIO_INT_RISING = 1,
    GPIO_INT_FALLING = 2,
    GPIO_INT_CHANGE = 3
} gpio_int_mode_t;

/* GPIO Configuration Structure */
typedef struct {
    uint8_t pin;
    gpio_mode_t mode;
    bool interrupt_enabled;
    gpio_int_mode_t int_mode;
    void (*handler)(uint8_t);  /* Callback function */
} gpio_config_t;

/* GPIO Handler Structure */
typedef struct {
    uint8_t pin;
    gpio_mode_t mode;
    gpio_level_t level;
    uint8_t pwm_duty;
    uint16_t analog_value;
} gpio_handler_t;

/* Prototypes */

/**
 * Initialize GPIO driver
 * تهيئة وحدة GPIO
 */
int gpio_init(void);

/**
 * Deinitialize GPIO driver
 * إيقاف وحدة GPIO
 */
int gpio_deinit(void);

/**
 * Configure a GPIO pin
 * تكوين دبوس GPIO
 * @param config GPIO configuration
 * @return 0 on success, -1 on error
 */
int gpio_configure(const gpio_config_t *config);

/**
 * Write digital value to GPIO pin
 * كتابة رقمية على الدبوس
 * @param pin Pin number
 * @param level Pin level (HIGH/LOW)
 * @return 0 on success, -1 on error
 */
int gpio_digital_write(uint8_t pin, gpio_level_t level);

/**
 * Read digital value from GPIO pin
 * قراءة رقمية من الدبوس
 * @param pin Pin number
 * @param level Pointer to store the result
 * @return 0 on success, -1 on error
 */
int gpio_digital_read(uint8_t pin, gpio_level_t *level);

/**
 * Write PWM value to GPIO pin
 * كتابة PWM على الدبوس
 * @param pin Pin number
 * @param duty Duty cycle (0-255)
 * @return 0 on success, -1 on error
 */
int gpio_pwm_write(uint8_t pin, uint8_t duty);

/**
 * Read analog value from GPIO pin
 * قراءة تناظرية من الدبوس
 * @param pin Pin number (ADC pin)
 * @param value Pointer to store the result (0-1023)
 * @return 0 on success, -1 on error
 */
int gpio_analog_read(uint8_t pin, uint16_t *value);

/**
 * Attach interrupt handler
 * تعليق دالة المقاطعة
 * @param pin Pin number
 * @param mode Interrupt mode
 * @param handler Callback function
 * @return 0 on success, -1 on error
 */
int gpio_attach_interrupt(uint8_t pin, gpio_int_mode_t mode, void (*handler)(uint8_t));

/**
 * Detach interrupt handler
 * فصل دالة المقاطعة
 * @param pin Pin number
 * @return 0 on success, -1 on error
 */
int gpio_detach_interrupt(uint8_t pin);

/**
 * Get GPIO handler for a pin
 * الحصول على معالج الـ GPIO
 * @param pin Pin number
 * @return Pointer to GPIO handler, NULL if not found
 */
gpio_handler_t* gpio_get_handler(uint8_t pin);

/**
 * Get total number of configured pins
 * عدد الدبابيس المكونة
 * @return Number of pins
 */
int gpio_get_pin_count(void);

#endif /* GPIO_H */
