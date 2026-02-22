/**
 * @file i2c.h
 * @brief RoboOS I2C Driver — ARM Cortex-M4 (STM32F4xx)
 *
 * يدعم:
 *   - Master Read/Write (7-bit & 10-bit addressing)
 *   - DMA-based transfers
 *   - Multi-master arbitration ← يُعالج بالأسمبلي
 *   - Timeout-safe blocking calls
 */

#ifndef ROBOOS_I2C_H
#define ROBOOS_I2C_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* =============================================================================
 * Definitions
 * =============================================================================
 */

/** أرقام وحدات I2C المتاحة */
typedef enum {
    I2C_PORT_1 = 0,   /* I2C1: PB6(SCL) PB7(SDA) */
    I2C_PORT_2 = 1,   /* I2C2: PB10(SCL) PB11(SDA) */
    I2C_PORT_3 = 2,   /* I2C3: PA8(SCL) PC9(SDA) */
    I2C_PORT_COUNT
} i2c_port_t;

/** سرعات I2C */
typedef enum {
    I2C_SPEED_STANDARD  = 100000,   /* 100 kHz — Standard Mode */
    I2C_SPEED_FAST      = 400000,   /* 400 kHz — Fast Mode */
    I2C_SPEED_FAST_PLUS = 1000000,  /* 1 MHz   — Fast Mode Plus */
} i2c_speed_t;

/** نتائج العمليات */
typedef enum {
    I2C_OK          =  0,
    I2C_ERR_BUSY    = -1,  /* الخط مشغول */
    I2C_ERR_NACK    = -2,  /* الجهاز لم يرد */
    I2C_ERR_TIMEOUT = -3,  /* انتهاء المهلة */
    I2C_ERR_ARB     = -4,  /* خسارة التحكيم (Multi-master) */
    I2C_ERR_BUS     = -5,  /* خطأ في الخط */
} i2c_result_t;

/** إعدادات I2C */
typedef struct {
    i2c_port_t  port;
    i2c_speed_t speed;
    uint32_t    timeout_ms;     /* مهلة انتظار الرد */
    bool        use_dma;        /* استخدام DMA للنقل الكبير */
    uint8_t     own_address;    /* عنوان الجهاز (Slave Mode) */
} i2c_config_t;

/** حالة I2C (تُملأ بمعالج المقاطعة) */
typedef struct {
    volatile bool     busy;
    volatile i2c_result_t last_result;
    volatile uint32_t bytes_transferred;
} i2c_state_t;


/* =============================================================================
 * Core API
 * =============================================================================
 */

/**
 * @brief تهيئة وحدة I2C
 */
i2c_result_t i2c_init(const i2c_config_t *cfg);

/**
 * @brief كتابة بيانات لجهاز Slave
 * @param port       وحدة I2C
 * @param dev_addr   عنوان الجهاز (7-bit)
 * @param data       مؤشر البيانات
 * @param len        عدد البايتات
 */
i2c_result_t i2c_write(i2c_port_t port, uint8_t dev_addr,
                        const uint8_t *data, size_t len);

/**
 * @brief قراءة بيانات من جهاز Slave
 */
i2c_result_t i2c_read(i2c_port_t port, uint8_t dev_addr,
                       uint8_t *buf, size_t len);

/**
 * @brief كتابة سجل ثم قراءة منه (الأكثر شيوعاً مع Sensors)
 * @param reg_addr   عنوان السجل
 * @param reg_len    حجم عنوان السجل (1 أو 2 بايت)
 */
i2c_result_t i2c_write_read(i2c_port_t port, uint8_t dev_addr,
                             const uint8_t *reg_addr, size_t reg_len,
                             uint8_t *buf, size_t read_len);

/**
 * @brief فحص وجود جهاز على الخط (ACK probe)
 * @return true إذا رد الجهاز
 */
bool i2c_device_ready(i2c_port_t port, uint8_t dev_addr, uint32_t trials);

/**
 * @brief إيقاف وحدة I2C وتحرير الـ pins
 */
void i2c_deinit(i2c_port_t port);

/**
 * @brief إعادة تهيئة I2C بعد خطأ في الخط (Bus recovery)
 * يُولِّد 9 نبضات SCL يدوياً لتحرير Slave عالق
 */
i2c_result_t i2c_bus_recovery(i2c_port_t port);

/**
 * @brief قراءة حالة وحدة I2C
 */
const i2c_state_t* i2c_get_state(i2c_port_t port);


/* =============================================================================
 * High-Level Sensor Helpers
 * =============================================================================
 */

/** اقرأ بايت واحد من سجل معين */
static inline i2c_result_t i2c_read_reg8(i2c_port_t port, uint8_t dev,
                                          uint8_t reg, uint8_t *val)
{
    return i2c_write_read(port, dev, &reg, 1, val, 1);
}

/** اكتب قيمة لسجل معين */
static inline i2c_result_t i2c_write_reg8(i2c_port_t port, uint8_t dev,
                                           uint8_t reg, uint8_t val)
{
    uint8_t buf[2] = {reg, val};
    return i2c_write(port, dev, buf, 2);
}

/** اقرأ كلمة 16-bit (Big-Endian) من سجل */
i2c_result_t i2c_read_reg16_be(i2c_port_t port, uint8_t dev,
                                uint8_t reg, uint16_t *val);


/* =============================================================================
 * معالجات المقاطعات (تُعرَّف في irq_vectors)
 * =============================================================================
 */
void I2C1_EV_IRQHandler(void);
void I2C1_ER_IRQHandler(void);
void I2C2_EV_IRQHandler(void);
void I2C2_ER_IRQHandler(void);

#ifdef __cplusplus
}
#endif

#endif /* ROBOOS_I2C_H */
