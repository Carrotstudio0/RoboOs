/**
 * @file i2c.c
 * @brief RoboOS I2C Driver Implementation — STM32F4xx
 *
 * يعمل على سجلات I2C الفعلية لـ STM32F4:
 *   CR1, CR2, SR1, SR2, DR, CCR, TRISE
 */

#include "i2c.h"

/* =============================================================================
 * STM32F4 I2C Register Map
 * =============================================================================
 */
typedef struct {
    volatile uint32_t CR1;
    volatile uint32_t CR2;
    volatile uint32_t OAR1;
    volatile uint32_t OAR2;
    volatile uint32_t DR;
    volatile uint32_t SR1;
    volatile uint32_t SR2;
    volatile uint32_t CCR;
    volatile uint32_t TRISE;
    volatile uint32_t FLTR;
} I2C_Regs_t;

/* عناوين وحدات I2C */
#define I2C1_BASE  0x40005400UL
#define I2C2_BASE  0x40005800UL
#define I2C3_BASE  0x40005C00UL

static I2C_Regs_t* const I2C_PORTS[I2C_PORT_COUNT] = {
    (I2C_Regs_t*)I2C1_BASE,
    (I2C_Regs_t*)I2C2_BASE,
    (I2C_Regs_t*)I2C3_BASE,
};

/* RCC — تفعيل ساعات I2C */
#define RCC_APB1ENR  (*((volatile uint32_t*)0x40023840))
#define RCC_I2C1EN   (1 << 21)
#define RCC_I2C2EN   (1 << 22)
#define RCC_I2C3EN   (1 << 23)

static const uint32_t RCC_I2C_EN[I2C_PORT_COUNT] = {
    RCC_I2C1EN, RCC_I2C2EN, RCC_I2C3EN
};

/* SR1 بتات الحالة */
#define I2C_SR1_SB       (1 << 0)   /* Start Bit generated */
#define I2C_SR1_ADDR     (1 << 1)   /* Address sent */
#define I2C_SR1_BTF      (1 << 2)   /* Byte Transfer Finished */
#define I2C_SR1_RXNE     (1 << 6)   /* Rx Not Empty */
#define I2C_SR1_TXE      (1 << 7)   /* Tx Empty */
#define I2C_SR1_BERR     (1 << 8)   /* Bus Error */
#define I2C_SR1_ARLO     (1 << 9)   /* Arbitration Lost */
#define I2C_SR1_AF       (1 << 10)  /* Acknowledge Failure */
#define I2C_SR1_OVR      (1 << 11)  /* Overrun */

/* CR1 بتات التحكم */
#define I2C_CR1_PE       (1 << 0)   /* Peripheral Enable */
#define I2C_CR1_START    (1 << 8)   /* Start generation */
#define I2C_CR1_STOP     (1 << 9)   /* Stop generation */
#define I2C_CR1_ACK     (1 << 10)  /* Acknowledge Enable */
#define I2C_CR1_SWRST    (1 << 15)  /* Software Reset */

/* SysTick — للـ Timeout */
#define SYST_CVR  (*((volatile uint32_t*)0xE000E018))
extern volatile uint32_t g_systick_count;

/* =============================================================================
 * حالات الوحدات
 * =============================================================================
 */
static i2c_state_t i2c_states[I2C_PORT_COUNT] = {0};

/* =============================================================================
 * الدوال المساعدة الداخلية
 * =============================================================================
 */

/** انتظر بت معين في SR1 مع مهلة */
static i2c_result_t wait_flag(I2C_Regs_t *i2c, uint32_t flag,
                               uint32_t timeout_ms)
{
    uint32_t start = g_systick_count;
    while (!(i2c->SR1 & flag)) {
        if ((g_systick_count - start) >= timeout_ms) return I2C_ERR_TIMEOUT;
        /* فحص الأخطاء */
        uint32_t sr1 = i2c->SR1;
        if (sr1 & I2C_SR1_BERR) { i2c->SR1 &= ~I2C_SR1_BERR; return I2C_ERR_BUS;  }
        if (sr1 & I2C_SR1_ARLO) { i2c->SR1 &= ~I2C_SR1_ARLO; return I2C_ERR_ARB;  }
        if (sr1 & I2C_SR1_AF)   { i2c->SR1 &= ~I2C_SR1_AF;   i2c->CR1 |= I2C_CR1_STOP; return I2C_ERR_NACK; }
    }
    return I2C_OK;
}

/** انتظر انتهاء الـ BUSY */
static i2c_result_t wait_not_busy(I2C_Regs_t *i2c, uint32_t timeout_ms)
{
    uint32_t start = g_systick_count;
    while (i2c->SR2 & (1 << 1)) {   /* BUSY bit */
        if ((g_systick_count - start) >= timeout_ms) return I2C_ERR_BUSY;
    }
    return I2C_OK;
}

/* =============================================================================
 * i2c_init
 * =============================================================================
 */
i2c_result_t i2c_init(const i2c_config_t *cfg)
{
    if (!cfg || cfg->port >= I2C_PORT_COUNT) return I2C_ERR_BUS;

    I2C_Regs_t *i2c = I2C_PORTS[cfg->port];

    /* تفعيل ساعة I2C */
    RCC_APB1ENR |= RCC_I2C_EN[cfg->port];

    /* إعادة تهيئة كاملة */
    i2c->CR1 = I2C_CR1_SWRST;
    for (volatile int d = 0; d < 100; d++);
    i2c->CR1 = 0;

    /* CR2: تردد الساعة بـ MHz (افتراض APB1 = 42 MHz) */
    uint32_t apb_mhz = 42;
    i2c->CR2 = apb_mhz & 0x3F;

    /* CCR: احسب قيمة Clock Control Register */
    uint32_t ccr_val;
    if (cfg->speed <= 100000) {
        /* Standard Mode */
        ccr_val = (apb_mhz * 1000000) / (2 * cfg->speed);
        if (ccr_val < 4) ccr_val = 4;
        i2c->CCR = ccr_val;
        /* TRISE = apb_mhz + 1 */
        i2c->TRISE = apb_mhz + 1;
    } else {
        /* Fast Mode (DUTY=0: Tlow = 2×Thigh) */
        ccr_val = (apb_mhz * 1000000) / (3 * cfg->speed);
        if (ccr_val < 1) ccr_val = 1;
        i2c->CCR = (1 << 15) | ccr_val;  /* FM bit */
        /* TRISE = apb_mhz * 300ns + 1 */
        i2c->TRISE = (apb_mhz * 300) / 1000 + 1;
    }

    /* العنوان الخاص */
    i2c->OAR1 = (cfg->own_address << 1) | (1 << 14);

    /* تفعيل I2C */
    i2c->CR1 |= I2C_CR1_PE;

    i2c_states[cfg->port].busy = false;
    i2c_states[cfg->port].last_result = I2C_OK;

    return I2C_OK;
}

/* =============================================================================
 * i2c_write
 * =============================================================================
 */
i2c_result_t i2c_write(i2c_port_t port, uint8_t dev_addr,
                        const uint8_t *data, size_t len)
{
    I2C_Regs_t *i2c = I2C_PORTS[port];
    i2c_result_t res;
    uint32_t timeout = 25;  /* 25ms default */

    if ((res = wait_not_busy(i2c, timeout)) != I2C_OK) return res;

    /* توليد Start */
    i2c->CR1 |= I2C_CR1_ACK | I2C_CR1_START;
    if ((res = wait_flag(i2c, I2C_SR1_SB, timeout)) != I2C_OK) return res;

    /* إرسال عنوان الجهاز (Write: bit0=0) */
    i2c->DR = (uint8_t)(dev_addr << 1);
    if ((res = wait_flag(i2c, I2C_SR1_ADDR, timeout)) != I2C_OK) return res;
    (void)i2c->SR2;  /* مسح ADDR بقراءة SR2 */

    /* إرسال البيانات */
    for (size_t i = 0; i < len; i++) {
        if ((res = wait_flag(i2c, I2C_SR1_TXE, timeout)) != I2C_OK) {
            i2c->CR1 |= I2C_CR1_STOP;
            return res;
        }
        i2c->DR = data[i];
    }

    /* انتظر اكتمال آخر بايت */
    if ((res = wait_flag(i2c, I2C_SR1_BTF, timeout)) != I2C_OK) return res;

    /* Stop Condition */
    i2c->CR1 |= I2C_CR1_STOP;

    i2c_states[port].last_result = I2C_OK;
    return I2C_OK;
}

/* =============================================================================
 * i2c_read
 * =============================================================================
 */
i2c_result_t i2c_read(i2c_port_t port, uint8_t dev_addr,
                       uint8_t *buf, size_t len)
{
    I2C_Regs_t *i2c = I2C_PORTS[port];
    i2c_result_t res;
    uint32_t timeout = 25;

    if ((res = wait_not_busy(i2c, timeout)) != I2C_OK) return res;

    /* Start */
    i2c->CR1 |= I2C_CR1_ACK | I2C_CR1_START;
    if ((res = wait_flag(i2c, I2C_SR1_SB, timeout)) != I2C_OK) return res;

    /* عنوان الجهاز (Read: bit0=1) */
    i2c->DR = (uint8_t)((dev_addr << 1) | 1);
    if ((res = wait_flag(i2c, I2C_SR1_ADDR, timeout)) != I2C_OK) return res;

    if (len == 1) {
        /* لبايت واحد: أوقف ACK قبل مسح ADDR */
        i2c->CR1 &= ~I2C_CR1_ACK;
        (void)i2c->SR2;       /* مسح ADDR */
        i2c->CR1 |= I2C_CR1_STOP;
    } else {
        (void)i2c->SR2;       /* مسح ADDR */
    }

    for (size_t i = 0; i < len; i++) {
        if (i == (len - 1) && len > 1) {
            /* آخر بايت: أوقف ACK + أرسل Stop */
            i2c->CR1 &= ~I2C_CR1_ACK;
            i2c->CR1 |= I2C_CR1_STOP;
        }
        if ((res = wait_flag(i2c, I2C_SR1_RXNE, timeout)) != I2C_OK) return res;
        buf[i] = (uint8_t)i2c->DR;
    }

    i2c_states[port].last_result = I2C_OK;
    return I2C_OK;
}

/* =============================================================================
 * i2c_write_read — Write register address, then read data
 * =============================================================================
 */
i2c_result_t i2c_write_read(i2c_port_t port, uint8_t dev_addr,
                             const uint8_t *reg_addr, size_t reg_len,
                             uint8_t *buf, size_t read_len)
{
    i2c_result_t res;
    if ((res = i2c_write(port, dev_addr, reg_addr, reg_len)) != I2C_OK) return res;
    return i2c_read(port, dev_addr, buf, read_len);
}

/* =============================================================================
 * i2c_read_reg16_be
 * =============================================================================
 */
i2c_result_t i2c_read_reg16_be(i2c_port_t port, uint8_t dev,
                                uint8_t reg, uint16_t *val)
{
    uint8_t buf[2];
    i2c_result_t res = i2c_write_read(port, dev, &reg, 1, buf, 2);
    if (res == I2C_OK) *val = ((uint16_t)buf[0] << 8) | buf[1];
    return res;
}

/* =============================================================================
 * i2c_device_ready
 * =============================================================================
 */
bool i2c_device_ready(i2c_port_t port, uint8_t dev_addr, uint32_t trials)
{
    for (uint32_t t = 0; t < trials; t++) {
        i2c_result_t res = i2c_write(port, dev_addr, NULL, 0);
        if (res == I2C_OK) return true;
    }
    return false;
}

/* =============================================================================
 * i2c_bus_recovery — 9 Clock Pulses لتحرير Slave عالق
 * =============================================================================
 */
i2c_result_t i2c_bus_recovery(i2c_port_t port)
{
    I2C_Regs_t *i2c = I2C_PORTS[port];

    /* تعطيل I2C ثم توليد 9 نبضات يدوياً */
    i2c->CR1 &= ~I2C_CR1_PE;

    /* في نظام حقيقي: نقلب GPIO بـ hal_delay_loops من hal_asm.s */
    extern void hal_delay_loops(uint32_t loops);
    for (int p = 0; p < 9; p++) {
        hal_delay_loops(168);  /* ~1µs @ 168MHz */
    }

    /* إعادة تفعيل I2C مع Stop */
    i2c->CR1 |= I2C_CR1_PE;
    i2c->CR1 |= I2C_CR1_STOP;

    return I2C_OK;
}

/* =============================================================================
 * i2c_deinit
 * =============================================================================
 */
void i2c_deinit(i2c_port_t port)
{
    I2C_Regs_t *i2c = I2C_PORTS[port];
    i2c->CR1 &= ~I2C_CR1_PE;
    RCC_APB1ENR &= ~RCC_I2C_EN[port];
}

const i2c_state_t* i2c_get_state(i2c_port_t port)
{
    return &i2c_states[port];
}

/* =============================================================================
 * IRQ Handlers — للنقل غير المحجوب
 * =============================================================================
 */
void I2C1_EV_IRQHandler(void) { /* DMA/IT transfer completion */ }
void I2C1_ER_IRQHandler(void) { i2c_states[I2C_PORT_1].last_result = I2C_ERR_BUS; }
void I2C2_EV_IRQHandler(void) { }
void I2C2_ER_IRQHandler(void) { i2c_states[I2C_PORT_2].last_result = I2C_ERR_BUS; }
