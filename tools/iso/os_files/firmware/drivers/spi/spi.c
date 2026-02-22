/**
 * @file spi.c
 * @brief RoboOS SPI Driver Implementation — STM32F4xx
 */

#include "spi.h"

/* =============================================================================
 * STM32F4 SPI Register Map
 * =============================================================================
 */
typedef struct {
    volatile uint32_t CR1;
    volatile uint32_t CR2;
    volatile uint32_t SR;
    volatile uint32_t DR;
    volatile uint32_t CRCPR;
    volatile uint32_t RXCRCR;
    volatile uint32_t TXCRCR;
    volatile uint32_t I2SCFGR;
    volatile uint32_t I2SPR;
} SPI_Regs_t;

#define SPI1_BASE   0x40013000UL
#define SPI2_BASE   0x40003800UL
#define SPI3_BASE   0x40003C00UL

static SPI_Regs_t* const SPI_PORTS[SPI_PORT_COUNT] = {
    (SPI_Regs_t*)SPI1_BASE,
    (SPI_Regs_t*)SPI2_BASE,
    (SPI_Regs_t*)SPI3_BASE,
};

/* RCC Clocks */
#define RCC_APB1ENR  (*((volatile uint32_t*)0x40023840))
#define RCC_APB2ENR  (*((volatile uint32_t*)0x40023844))
#define RCC_SPI1EN   (1 << 12)  /* APB2 */
#define RCC_SPI2EN   (1 << 14)  /* APB1 */
#define RCC_SPI3EN   (1 << 15)  /* APB1 */

/* CR1 Bits */
#define SPI_CR1_CPHA     (1 << 0)
#define SPI_CR1_CPOL     (1 << 1)
#define SPI_CR1_MSTR     (1 << 2)
#define SPI_CR1_BR_SHIFT  3
#define SPI_CR1_SPE      (1 << 6)
#define SPI_CR1_LSBFIRST (1 << 7)
#define SPI_CR1_SSI      (1 << 8)
#define SPI_CR1_SSM      (1 << 9)
#define SPI_CR1_RXONLY   (1 << 10)
#define SPI_CR1_DFF      (1 << 11)  /* 16-bit frame */
#define SPI_CR1_BIDIOE   (1 << 14)
#define SPI_CR1_BIDIMODE (1 << 15)

/* SR Bits */
#define SPI_SR_RXNE  (1 << 0)
#define SPI_SR_TXE   (1 << 1)
#define SPI_SR_MODF  (1 << 5)
#define SPI_SR_OVR   (1 << 6)
#define SPI_SR_BSY   (1 << 7)

extern volatile uint32_t g_systick_count;

/* =============================================================================
 * spi_init
 * =============================================================================
 */
spi_result_t spi_init(const spi_config_t *cfg)
{
    if (!cfg || cfg->port >= SPI_PORT_COUNT) return SPI_ERR_TIMEOUT;

    SPI_Regs_t *spi = SPI_PORTS[cfg->port];

    /* تفعيل الساعة */
    if (cfg->port == SPI_PORT_1) {
        RCC_APB2ENR |= RCC_SPI1EN;
    } else {
        RCC_APB1ENR |= (cfg->port == SPI_PORT_2) ? RCC_SPI2EN : RCC_SPI3EN;
    }

    /* تعطيل SPI قبل التهيئة */
    spi->CR1 = 0;

    /* بناء CR1 */
    uint32_t cr1 = 0;
    cr1 |= SPI_CR1_MSTR;                               /* Master Mode */
    cr1 |= (cfg->mode & 0x3) ? (cfg->mode & 1 ? SPI_CR1_CPHA : SPI_CR1_CPOL) : 0;
    if (cfg->mode & 1) cr1 |= SPI_CR1_CPHA;
    if (cfg->mode & 2) cr1 |= SPI_CR1_CPOL;
    cr1 |= ((uint32_t)cfg->baud << SPI_CR1_BR_SHIFT);  /* Baud Rate */
    if (cfg->first_bit == SPI_FIRSTBIT_LSB) cr1 |= SPI_CR1_LSBFIRST;
    if (cfg->data_size == SPI_DATASIZE_16BIT) cr1 |= SPI_CR1_DFF;
    if (cfg->nss_software) cr1 |= SPI_CR1_SSM | SPI_CR1_SSI;

    spi->CR1 = cr1;
    spi->CR1 |= SPI_CR1_SPE;  /* تفعيل SPI */

    return SPI_OK;
}

/* =============================================================================
 * spi_wait_ready
 * =============================================================================
 */
spi_result_t spi_wait_ready(spi_port_t port, uint32_t timeout_ms)
{
    SPI_Regs_t *spi = SPI_PORTS[port];
    uint32_t start = g_systick_count;
    while (spi->SR & SPI_SR_BSY) {
        if ((g_systick_count - start) >= timeout_ms) return SPI_ERR_TIMEOUT;
    }
    return SPI_OK;
}

/* =============================================================================
 * spi_transfer_byte — قلب العملية: Full duplex بايت واحد
 * =============================================================================
 */
uint8_t spi_transfer_byte(spi_port_t port, uint8_t tx_byte)
{
    SPI_Regs_t *spi = SPI_PORTS[port];

    /* انتظر فراغ Tx */
    while (!(spi->SR & SPI_SR_TXE));
    *((volatile uint8_t*)&spi->DR) = tx_byte;

    /* انتظر وصول Rx */
    while (!(spi->SR & SPI_SR_RXNE));
    return *((volatile uint8_t*)&spi->DR);
}

/* =============================================================================
 * spi_transfer_word — 16-bit
 * =============================================================================
 */
uint16_t spi_transfer_word(spi_port_t port, uint16_t tx_word)
{
    SPI_Regs_t *spi = SPI_PORTS[port];
    while (!(spi->SR & SPI_SR_TXE));
    spi->DR = tx_word;
    while (!(spi->SR & SPI_SR_RXNE));
    return (uint16_t)spi->DR;
}

/* =============================================================================
 * spi_transmit
 * =============================================================================
 */
spi_result_t spi_transmit(spi_port_t port, const uint8_t *data,
                           size_t len, uint32_t timeout_ms)
{
    uint32_t start = g_systick_count;
    for (size_t i = 0; i < len; i++) {
        if ((g_systick_count - start) >= timeout_ms) return SPI_ERR_TIMEOUT;
        spi_transfer_byte(port, data[i]);
    }
    return spi_wait_ready(port, timeout_ms);
}

/* =============================================================================
 * spi_receive
 * =============================================================================
 */
spi_result_t spi_receive(spi_port_t port, uint8_t *buf,
                          size_t len, uint32_t timeout_ms)
{
    uint32_t start = g_systick_count;
    for (size_t i = 0; i < len; i++) {
        if ((g_systick_count - start) >= timeout_ms) return SPI_ERR_TIMEOUT;
        buf[i] = spi_transfer_byte(port, 0xFF);
    }
    return SPI_OK;
}

/* =============================================================================
 * spi_transfer — Full Duplex
 * =============================================================================
 */
spi_result_t spi_transfer(spi_port_t port,
                           const uint8_t *tx_data, uint8_t *rx_buf,
                           size_t len, uint32_t timeout_ms)
{
    uint32_t start = g_systick_count;
    for (size_t i = 0; i < len; i++) {
        if ((g_systick_count - start) >= timeout_ms) return SPI_ERR_TIMEOUT;
        uint8_t tx = tx_data ? tx_data[i] : 0xFF;
        uint8_t rx = spi_transfer_byte(port, tx);
        if (rx_buf) rx_buf[i] = rx;
    }
    return SPI_OK;
}

/* =============================================================================
 * DMA Transfers (Stubs — تحتاج ضبط DMA Channels حسب الـ MCU)
 * =============================================================================
 */
spi_result_t spi_transmit_dma(spi_port_t port, const uint8_t *data,
                               size_t len, void (*callback)(void))
{
    /* في نظام حقيقي: يهيئ DMA Stream + تفعيل SPI_CR2 TXDMAEN */
    /* هنا: fallback للـ blocking */
    (void)callback;
    return spi_transmit(port, data, len, 100);
}

spi_result_t spi_transfer_dma(spi_port_t port,
                               const uint8_t *tx, uint8_t *rx,
                               size_t len, void (*callback)(void))
{
    (void)callback;
    return spi_transfer(port, tx, rx, len, 100);
}

/* =============================================================================
 * CS Helpers (يستخدم GPIO register مباشرة)
 * =============================================================================
 */
#define GPIOA_ODR  (*((volatile uint32_t*)0x40020014))
#define GPIOB_ODR  (*((volatile uint32_t*)0x40020414))

void spi_cs_assert(uint32_t gpio_pin)   { /* اضبط pin منخفضاً */ (void)gpio_pin; }
void spi_cs_deassert(uint32_t gpio_pin) { /* اضبط pin مرتفعاً */ (void)gpio_pin; }

/* =============================================================================
 * Deinit
 * =============================================================================
 */
void spi_deinit(spi_port_t port)
{
    SPI_Regs_t *spi = SPI_PORTS[port];
    spi->CR1 &= ~SPI_CR1_SPE;
    if (port == SPI_PORT_1) RCC_APB2ENR &= ~RCC_SPI1EN;
    else if (port == SPI_PORT_2) RCC_APB1ENR &= ~RCC_SPI2EN;
    else RCC_APB1ENR &= ~RCC_SPI3EN;
}

/* IRQ Stubs */
void SPI1_IRQHandler(void) {}
void SPI2_IRQHandler(void) {}
void SPI3_IRQHandler(void) {}
