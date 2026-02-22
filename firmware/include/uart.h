/**
 * UART Driver Header File
 * وحدة الاتصال التسلسلي
 */

#ifndef UART_H
#define UART_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/* UART Port Numbers */
typedef enum {
    UART_PORT_0 = 0,
    UART_PORT_1 = 1,
    UART_PORT_2 = 2,
    UART_PORT_MAX = 3
} uart_port_t;

/* UART Baud Rates */
typedef enum {
    UART_BAUD_9600 = 9600,
    UART_BAUD_19200 = 19200,
    UART_BAUD_38400 = 38400,
    UART_BAUD_57600 = 57600,
    UART_BAUD_115200 = 115200,
    UART_BAUD_230400 = 230400
} uart_baud_t;

/* UART Data Bits */
typedef enum {
    UART_DATA_BITS_8 = 8,
    UART_DATA_BITS_9 = 9
} uart_data_bits_t;

/* UART Stop Bits */
typedef enum {
    UART_STOP_BITS_1 = 1,
    UART_STOP_BITS_2 = 2
} uart_stop_bits_t;

/* UART Parity */
typedef enum {
    UART_PARITY_NONE = 0,
    UART_PARITY_EVEN = 1,
    UART_PARITY_ODD = 2
} uart_parity_t;

/* UART Configuration */
typedef struct {
    uart_port_t port;
    uart_baud_t baud;
    uart_data_bits_t data_bits;
    uart_stop_bits_t stop_bits;
    uart_parity_t parity;
    void (*rx_callback)(uint8_t);  /* Callback for received data */
} uart_config_t;

/* UART Handler */
typedef struct {
    uart_port_t port;
    uart_baud_t baud;
    bool enabled;
    uint32_t tx_count;
    uint32_t rx_count;
} uart_handler_t;

/* Ring Buffer for UART data */
#define UART_RX_BUFFER_SIZE 256
typedef struct {
    uint8_t buffer[UART_RX_BUFFER_SIZE];
    uint16_t head;
    uint16_t tail;
    uint16_t count;
} uart_ring_buffer_t;

/* Prototypes */

/**
 * Initialize UART driver
 * تهيئة وحدة UART
 */
int uart_init(void);

/**
 * Deinitialize UART driver
 * إيقاف وحدة UART
 */
int uart_deinit(void);

/**
 * Configure UART port
 * تكوين منفذ UART
 * @param config UART configuration
 * @return 0 on success, -1 on error
 */
int uart_configure(const uart_config_t *config);

/**
 * Open UART port
 * فتح منفذ UART
 * @param port UART port
 * @return 0 on success, -1 on error
 */
int uart_open(uart_port_t port);

/**
 * Close UART port
 * إغلاق منفذ UART
 * @param port UART port
 * @return 0 on success, -1 on error
 */
int uart_close(uart_port_t port);

/**
 * Write data to UART
 * كتابة بيانات على UART
 * @param port UART port
 * @param data Pointer to data buffer
 * @param length Number of bytes to write
 * @return Number of bytes written, or -1 on error
 */
int uart_write(uart_port_t port, const uint8_t *data, size_t length);

/**
 * Write string to UART
 * كتابة نص على UART
 * @param port UART port
 * @param str Null-terminated string
 * @return Number of bytes written, or -1 on error
 */
int uart_write_string(uart_port_t port, const char *str);

/**
 * Read data from UART
 * قراءة بيانات من UART
 * @param port UART port
 * @param buffer Pointer to data buffer
 * @param length Maximum number of bytes to read
 * @return Number of bytes read, or -1 on error
 */
int uart_read(uart_port_t port, uint8_t *buffer, size_t length);

/**
 * Get number of available bytes in RX buffer
 * عدد البايتات المتاحة في المستقبل
 * @param port UART port
 * @return Number of available bytes
 */
int uart_available(uart_port_t port);

/**
 * Flush RX buffer
 * مسح مخزن الاستقبال
 * @param port UART port
 * @return 0 on success, -1 on error
 */
int uart_flush(uart_port_t port);

/**
 * Get UART handler
 * الحصول على معالج UART
 * @param port UART port
 * @return Pointer to UART handler, NULL if not found
 */
uart_handler_t* uart_get_handler(uart_port_t port);

/**
 * Dump UART statistics
 * عرض إحصائيات UART
 */
void uart_dump_stats(void);

#endif /* UART_H */
