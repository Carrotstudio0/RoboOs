/**
 * UART Driver Implementation
 * تطبيق وحدة UART
 */

#include "../../include/uart.h"
#include <string.h>
#include <stdio.h>

/* UART State */
typedef struct {
    uart_handler_t handlers[UART_PORT_MAX];
    uart_ring_buffer_t rx_buffers[UART_PORT_MAX];
    bool initialized;
} uart_state_t;

/* Global state */
static uart_state_t uart_state = {0};

/**
 * Initialize UART driver
 */
int uart_init(void)
{
    if (uart_state.initialized) {
        return 0;
    }
    
    memset(&uart_state, 0, sizeof(uart_state_t));
    uart_state.initialized = true;
    
    printf("[UART] Driver initialized successfully\n");
    return 0;
}

/**
 * Deinitialize UART driver
 */
int uart_deinit(void)
{
    if (!uart_state.initialized) {
        return -1;
    }
    
    for (int i = 0; i < UART_PORT_MAX; i++) {
        uart_close(i);
    }
    
    memset(&uart_state, 0, sizeof(uart_state_t));
    uart_state.initialized = false;
    
    printf("[UART] Driver deinitialized\n");
    return 0;
}

/**
 * Configure UART port
 */
int uart_configure(const uart_config_t *config)
{
    if (!uart_state.initialized || !config || config->port >= UART_PORT_MAX) {
        return -1;
    }
    
    uart_handler_t *handler = &uart_state.handlers[config->port];
    handler->port = config->port;
    handler->baud = config->baud;
    
    printf("[UART] Port %d configured: baud=%d, data=%d, stop=%d, parity=%d\n",
           config->port, config->baud, config->data_bits, 
           config->stop_bits, config->parity);
    
    return 0;
}

/**
 * Open UART port
 */
int uart_open(uart_port_t port)
{
    if (!uart_state.initialized || port >= UART_PORT_MAX) {
        return -1;
    }
    
    uart_handler_t *handler = &uart_state.handlers[port];
    if (handler->enabled) {
        return 0;  /* Already open */
    }
    
    handler->enabled = true;
    handler->tx_count = 0;
    handler->rx_count = 0;
    
    /* Initialize RX buffer */
    uart_ring_buffer_t *rb = &uart_state.rx_buffers[port];
    memset(rb, 0, sizeof(uart_ring_buffer_t));
    
    printf("[UART] Port %d opened\n", port);
    
    /* Hardware implementation would go here */
    /* For real MCU: Enable UART, set baud rate, etc. */
    
    return 0;
}

/**
 * Close UART port
 */
int uart_close(uart_port_t port)
{
    if (!uart_state.initialized || port >= UART_PORT_MAX) {
        return -1;
    }
    
    uart_handler_t *handler = &uart_state.handlers[port];
    if (!handler->enabled) {
        return 0;  /* Already closed */
    }
    
    handler->enabled = false;
    printf("[UART] Port %d closed\n", port);
    
    /* Hardware implementation would go here */
    
    return 0;
}

/**
 * Write data to UART
 */
int uart_write(uart_port_t port, const uint8_t *data, size_t length)
{
    if (!uart_state.initialized || port >= UART_PORT_MAX || !data) {
        return -1;
    }
    
    uart_handler_t *handler = &uart_state.handlers[port];
    if (!handler->enabled) {
        printf("[UART] Error: Port %d not open\n", port);
        return -1;
    }
    
    handler->tx_count += length;
    
    /* Send data (simulation) */
    printf("[UART%d] Sending %zu bytes: ", port, length);
    for (size_t i = 0; i < length && i < 32; i++) {
        printf("%02X ", data[i]);
    }
    if (length > 32) printf("...");
    printf("\n");
    
    /* Hardware implementation would go here */
    /* For real MCU: Send data byte by byte via UART peripheral */
    
    return (int)length;
}

/**
 * Write string to UART
 */
int uart_write_string(uart_port_t port, const char *str)
{
    if (!str) {
        return -1;
    }
    
    return uart_write(port, (const uint8_t *)str, strlen(str));
}

/**
 * Read data from UART
 */
int uart_read(uart_port_t port, uint8_t *buffer, size_t length)
{
    if (!uart_state.initialized || port >= UART_PORT_MAX || !buffer) {
        return -1;
    }
    
    uart_handler_t *handler = &uart_state.handlers[port];
    if (!handler->enabled) {
        return -1;
    }
    
    uart_ring_buffer_t *rb = &uart_state.rx_buffers[port];
    
    size_t bytes_read = 0;
    while (bytes_read < length && rb->count > 0) {
        buffer[bytes_read++] = rb->buffer[rb->tail];
        rb->tail = (rb->tail + 1) % UART_RX_BUFFER_SIZE;
        rb->count--;
    }
    
    if (bytes_read > 0) {
        handler->rx_count += bytes_read;
    }
    
    return (int)bytes_read;
}

/**
 * Get number of available bytes
 */
int uart_available(uart_port_t port)
{
    if (!uart_state.initialized || port >= UART_PORT_MAX) {
        return -1;
    }
    
    return (int)uart_state.rx_buffers[port].count;
}

/**
 * Flush RX buffer
 */
int uart_flush(uart_port_t port)
{
    if (!uart_state.initialized || port >= UART_PORT_MAX) {
        return -1;
    }
    
    uart_ring_buffer_t *rb = &uart_state.rx_buffers[port];
    memset(rb, 0, sizeof(uart_ring_buffer_t));
    
    printf("[UART] Port %d RX buffer flushed\n", port);
    return 0;
}

/**
 * Get UART handler
 */
uart_handler_t* uart_get_handler(uart_port_t port)
{
    if (!uart_state.initialized || port >= UART_PORT_MAX) {
        return NULL;
    }
    
    if (uart_state.handlers[port].enabled) {
        return &uart_state.handlers[port];
    }
    
    return NULL;
}

/**
 * Dump UART statistics
 */
void uart_dump_stats(void)
{
    printf("\n=== UART Statistics ===\n");
    printf("Initialized: %s\n\n", uart_state.initialized ? "YES" : "NO");
    
    for (int i = 0; i < UART_PORT_MAX; i++) {
        uart_handler_t *h = &uart_state.handlers[i];
        printf("UART%d: %s, Baud=%d, TX=%lu, RX=%lu\n",
               i, h->enabled ? "OPEN" : "CLOSED", h->baud, h->tx_count, h->rx_count);
    }
    printf("\n");
}

/**
 * Mock function for data reception (for testing)
 */
void uart_receive_byte(uart_port_t port, uint8_t byte)
{
    if (port >= UART_PORT_MAX) return;
    
    uart_ring_buffer_t *rb = &uart_state.rx_buffers[port];
    
    if (rb->count < UART_RX_BUFFER_SIZE) {
        rb->buffer[rb->head] = byte;
        rb->head = (rb->head + 1) % UART_RX_BUFFER_SIZE;
        rb->count++;
    }
}
