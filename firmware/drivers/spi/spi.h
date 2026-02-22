/**
 * @file spi.h
 * @brief RoboOS SPI Driver — ARM Cortex-M4 (STM32F4xx)
 *
 * يدعم:
 *   - SPI Master & Slave
 *   - Full-Duplex / Half-Duplex / Simplex
 *   - NSS Hardware & Software
 *   - DMA-accelerated large transfers
 *   - 8-bit & 16-bit data frames
 */

#ifndef ROBOOS_SPI_H
#define ROBOOS_SPI_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* =============================================================================
 * Types & Enumerations
 * =============================================================================
 */

typedef enum {
    SPI_PORT_1 = 0,   /* SPI1: PA5(CLK) PA6(MISO) PA7(MOSI) */
    SPI_PORT_2 = 1,   /* SPI2: PB13(CLK) PB14(MISO) PB15(MOSI) */
    SPI_PORT_3 = 2,   /* SPI3: PC10(CLK) PC11(MISO) PC12(MOSI) */
    SPI_PORT_COUNT
} spi_port_t;

/** وضع SPI (Clock Polarity + Phase) */
typedef enum {
    SPI_MODE_0 = 0,  /* CPOL=0, CPHA=0 — الأكثر شيوعاً */
    SPI_MODE_1 = 1,  /* CPOL=0, CPHA=1 */
    SPI_MODE_2 = 2,  /* CPOL=1, CPHA=0 */
    SPI_MODE_3 = 3,  /* CPOL=1, CPHA=1 */
} spi_mode_t;

/** معدل Baud Rate = fPCLK / prescaler */
typedef enum {
    SPI_BAUD_DIV_2   = 0,  /* APB / 2   → 42 MHz اقصى */
    SPI_BAUD_DIV_4   = 1,  /* APB / 4   → 21 MHz */
    SPI_BAUD_DIV_8   = 2,  /* APB / 8   → 10.5 MHz */
    SPI_BAUD_DIV_16  = 3,  /* APB / 16  → 5.25 MHz */
    SPI_BAUD_DIV_32  = 4,  /* APB / 32  → 2.6 MHz */
    SPI_BAUD_DIV_64  = 5,  /* APB / 64  → 1.3 MHz */
    SPI_BAUD_DIV_128 = 6,  /* APB / 128 → 656 kHz */
    SPI_BAUD_DIV_256 = 7,  /* APB / 256 → 328 kHz */
} spi_baud_div_t;

typedef enum {
    SPI_DATASIZE_8BIT  = 0,
    SPI_DATASIZE_16BIT = 1,
} spi_datasize_t;

typedef enum {
    SPI_FIRSTBIT_MSB = 0,
    SPI_FIRSTBIT_LSB = 1,
} spi_firstbit_t;

typedef enum {
    SPI_OK          =  0,
    SPI_ERR_TIMEOUT = -1,
    SPI_ERR_OVR     = -2,  /* Overrun */
    SPI_ERR_MODF    = -3,  /* Mode Fault (NSS) */
    SPI_ERR_CRC     = -4,
} spi_result_t;

/** إعدادات SPI الكاملة */
typedef struct {
    spi_port_t      port;
    spi_mode_t      mode;
    spi_baud_div_t  baud;
    spi_datasize_t  data_size;
    spi_firstbit_t  first_bit;
    bool            nss_software;   /* true = NSS يدوي بـ GPIO */
    bool            use_dma;
    uint32_t        timeout_ms;
} spi_config_t;


/* =============================================================================
 * API
 * =============================================================================
 */

/**
 * @brief تهيئة SPI
 */
spi_result_t spi_init(const spi_config_t *cfg);

/**
 * @brief إرسال بيانات فقط (Tx-only)
 */
spi_result_t spi_transmit(spi_port_t port, const uint8_t *data,
                           size_t len, uint32_t timeout_ms);

/**
 * @brief استقبال بيانات فقط (Rx-only — يُرسل 0xFF كـ dummy clock)
 */
spi_result_t spi_receive(spi_port_t port, uint8_t *buf,
                          size_t len, uint32_t timeout_ms);

/**
 * @brief Full-Duplex: إرسال واستقبال في نفس الوقت
 * @param tx_data  بيانات للإرسال (يمكن NULL لإرسال 0xFF)
 * @param rx_buf   مخزن الاستقبال (يمكن NULL للتجاهل)
 */
spi_result_t spi_transfer(spi_port_t port,
                           const uint8_t *tx_data, uint8_t *rx_buf,
                           size_t len, uint32_t timeout_ms);

/**
 * @brief إرسال واستقبال كلمة 8-bit واحدة (مباشر — بدون DMA)
 * @return البايت المستقبَل
 */
uint8_t spi_transfer_byte(spi_port_t port, uint8_t tx_byte);

/**
 * @brief إرسال واستقبال كلمة 16-bit
 */
uint16_t spi_transfer_word(spi_port_t port, uint16_t tx_word);

/**
 * @brief إيقاف SPI
 */
void spi_deinit(spi_port_t port);

/**
 * @brief انتظار اكتمال العملية (Wait for BSY flag to clear)
 */
spi_result_t spi_wait_ready(spi_port_t port, uint32_t timeout_ms);

/**
 * @brief DMA-based transmit (غير محجوبة — Interrupt على الانتهاء)
 */
spi_result_t spi_transmit_dma(spi_port_t port, const uint8_t *data,
                               size_t len, void (*callback)(void));

/**
 * @brief DMA-based full duplex
 */
spi_result_t spi_transfer_dma(spi_port_t port,
                               const uint8_t *tx, uint8_t *rx,
                               size_t len, void (*callback)(void));


/* =============================================================================
 * NSS (Chip Select) Helpers
 * =============================================================================
 */

/** تنشيط Chip Select (منخفض) */
void spi_cs_assert(uint32_t gpio_pin);

/** إلغاء تنشيط Chip Select (مرتفع) */
void spi_cs_deassert(uint32_t gpio_pin);


/* =============================================================================
 * IRQ Handlers
 * =============================================================================
 */
void SPI1_IRQHandler(void);
void SPI2_IRQHandler(void);
void SPI3_IRQHandler(void);

#ifdef __cplusplus
}
#endif

#endif /* ROBOOS_SPI_H */
