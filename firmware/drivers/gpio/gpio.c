/**
 * GPIO Driver Implementation
 * تطبيق وحدة GPIO
 */

#include "../../include/gpio.h"
#include <string.h>
#include <stdio.h>

/* Configuration */
#define MAX_GPIO_PINS 40
#define GPIO_POOL_SIZE 128

/* GPIO State Structure */
typedef struct {
    gpio_handler_t handlers[MAX_GPIO_PINS];
    int pin_count;
    bool initialized;
} gpio_state_t;

/* Global state */
static gpio_state_t gpio_state = {0};

/**
 * Initialize GPIO driver
 */
int gpio_init(void)
{
    if (gpio_state.initialized) {
        return 0;
    }
    
    memset(&gpio_state, 0, sizeof(gpio_state_t));
    gpio_state.pin_count = 0;
    gpio_state.initialized = true;
    
    printf("[GPIO] Driver initialized successfully\n");
    return 0;
}

/**
 * Deinitialize GPIO driver
 */
int gpio_deinit(void)
{
    if (!gpio_state.initialized) {
        return -1;
    }
    
    memset(&gpio_state, 0, sizeof(gpio_state_t));
    gpio_state.initialized = false;
    
    printf("[GPIO] Driver deinitialized\n");
    return 0;
}

/**
 * Configure a GPIO pin
 */
int gpio_configure(const gpio_config_t *config)
{
    if (!gpio_state.initialized || !config) {
        return -1;
    }
    
    /* Check if pin already exists */
    for (int i = 0; i < gpio_state.pin_count; i++) {
        if (gpio_state.handlers[i].pin == config->pin) {
            /* Update existing handler */
            gpio_state.handlers[i].mode = config->mode;
            printf("[GPIO] Pin %d reconfigured to mode %d\n", config->pin, config->mode);
            return 0;
        }
    }
    
    /* Add new handler */
    if (gpio_state.pin_count >= MAX_GPIO_PINS) {
        printf("[GPIO] Error: Maximum GPIO pins (%d) reached\n", MAX_GPIO_PINS);
        return -1;
    }
    
    gpio_handler_t *handler = &gpio_state.handlers[gpio_state.pin_count];
    handler->pin = config->pin;
    handler->mode = config->mode;
    handler->level = GPIO_LEVEL_LOW;
    handler->pwm_duty = 0;
    handler->analog_value = 0;
    
    gpio_state.pin_count++;
    
    printf("[GPIO] Pin %d configured as mode %d\n", config->pin, config->mode);
    return 0;
}

/**
 * Write digital value to GPIO pin
 */
int gpio_digital_write(uint8_t pin, gpio_level_t level)
{
    gpio_handler_t *handler = gpio_get_handler(pin);
    
    if (!handler) {
        printf("[GPIO] Error: Pin %d not configured\n", pin);
        return -1;
    }
    
    if (handler->mode != GPIO_MODE_OUTPUT && handler->mode != GPIO_MODE_PWM) {
        printf("[GPIO] Error: Pin %d not in output mode\n", pin);
        return -1;
    }
    
    handler->level = level;
    printf("[GPIO] Pin %d set to %s\n", pin, level ? "HIGH" : "LOW");
    
    /* Hardware implementation would go here */
    /* For real MCU: PORTX |= (1 << pin) or PORTX &= ~(1 << pin) */
    
    return 0;
}

/**
 * Read digital value from GPIO pin
 */
int gpio_digital_read(uint8_t pin, gpio_level_t *level)
{
    gpio_handler_t *handler = gpio_get_handler(pin);
    
    if (!handler || !level) {
        return -1;
    }
    
    if (handler->mode != GPIO_MODE_INPUT && 
        handler->mode != GPIO_MODE_INPUT_PULLUP &&
        handler->mode != GPIO_MODE_OUTPUT) {
        printf("[GPIO] Error: Pin %d cannot be read\n", pin);
        return -1;
    }
    
    *level = handler->level;
    printf("[GPIO] Pin %d read: %d\n", pin, handler->level);
    
    /* Hardware implementation would go here */
    /* For real MCU: *level = (PINX & (1 << pin)) ? GPIO_LEVEL_HIGH : GPIO_LEVEL_LOW; */
    
    return 0;
}

/**
 * Write PWM value to GPIO pin
 */
int gpio_pwm_write(uint8_t pin, uint8_t duty)
{
    gpio_handler_t *handler = gpio_get_handler(pin);
    
    if (!handler) {
        printf("[GPIO] Error: Pin %d not configured\n", pin);
        return -1;
    }
    
    if (handler->mode != GPIO_MODE_PWM) {
        printf("[GPIO] Error: Pin %d not in PWM mode\n", pin);
        return -1;
    }
    
    handler->pwm_duty = duty;
    printf("[GPIO] Pin %d PWM duty set to %d%%\n", pin, (duty * 100) / 255);
    
    /* Hardware implementation would go here */
    /* For real MCU: Set PWM register */
    
    return 0;
}

/**
 * Read analog value from GPIO pin
 */
int gpio_analog_read(uint8_t pin, uint16_t *value)
{
    gpio_handler_t *handler = gpio_get_handler(pin);
    
    if (!handler || !value) {
        return -1;
    }
    
    if (handler->mode != GPIO_MODE_ANALOG) {
        printf("[GPIO] Error: Pin %d not in analog mode\n", pin);
        return -1;
    }
    
    *value = handler->analog_value;
    printf("[GPIO] Pin %d analog value: %d\n", pin, handler->analog_value);
    
    /* Hardware implementation would go here */
    /* For real MCU: Start ADC conversion and read result */
    
    return 0;
}

/**
 * Attach interrupt handler
 */
int gpio_attach_interrupt(uint8_t pin, gpio_int_mode_t mode, void (*handler)(uint8_t))
{
    gpio_handler_t *gpio_handler = gpio_get_handler(pin);
    
    if (!gpio_handler || !handler) {
        return -1;
    }
    
    printf("[GPIO] Interrupt attached to pin %d (mode %d)\n", pin, mode);
    
    /* Hardware implementation would go here */
    /* For real MCU: Configure EXTI and enable interrupt */
    
    return 0;
}

/**
 * Detach interrupt handler
 */
int gpio_detach_interrupt(uint8_t pin)
{
    gpio_handler_t *handler = gpio_get_handler(pin);
    
    if (!handler) {
        return -1;
    }
    
    printf("[GPIO] Interrupt detached from pin %d\n", pin);
    
    /* Hardware implementation would go here */
    
    return 0;
}

/**
 * Get GPIO handler for a pin
 */
gpio_handler_t* gpio_get_handler(uint8_t pin)
{
    if (!gpio_state.initialized) {
        return NULL;
    }
    
    for (int i = 0; i < gpio_state.pin_count; i++) {
        if (gpio_state.handlers[i].pin == pin) {
            return &gpio_state.handlers[i];
        }
    }
    
    return NULL;
}

/**
 * Get total number of configured pins
 */
int gpio_get_pin_count(void)
{
    return gpio_state.pin_count;
}

/**
 * Dump GPIO state for debugging
 */
void gpio_dump_state(void)
{
    printf("\n=== GPIO State ===\n");
    printf("Initialized: %s\n", gpio_state.initialized ? "YES" : "NO");
    printf("Total Pins: %d/%d\n\n", gpio_state.pin_count, MAX_GPIO_PINS);
    
    for (int i = 0; i < gpio_state.pin_count; i++) {
        gpio_handler_t *h = &gpio_state.handlers[i];
        printf("Pin %2d: Mode=%d, Level=%d, PWM_Duty=%d, Analog=%d\n",
               h->pin, h->mode, h->level, h->pwm_duty, h->analog_value);
    }
    printf("\n");
}
