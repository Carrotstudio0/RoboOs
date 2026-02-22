/**
 * @file adc.h
 * @brief RoboOS ADC Driver — ARM Cortex-M4 (STM32F4xx)
 *
 * يدعم:
 *   - Single conversion & Continuous mode
 *   - Scan mode (قراءة قنوات متعددة بالتسلسل)
 *   - DMA للقراءة المستمرة
 *   - Injected channels للقراءة الطارئة
 *   - Internal sensors (Temp, Vref, Vbat)
 *   - Watchdog تناظري للتنبيه عند تجاوز الحدود
 */

#ifndef ROBOOS_ADC_H
#define ROBOOS_ADC_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* =============================================================================
 * Types
 * =============================================================================
 */

typedef enum {
    ADC_PORT_1 = 0,   /* ADC1: 16 قناة */
    ADC_PORT_2 = 1,   /* ADC2: 16 قناة */
    ADC_PORT_3 = 2,   /* ADC3: 16 قناة */
    ADC_PORT_COUNT
} adc_port_t;

/** أرقام قنوات ADC */
typedef enum {
    ADC_CHANNEL_0  = 0,
    ADC_CHANNEL_1  = 1,
    ADC_CHANNEL_2  = 2,
    ADC_CHANNEL_3  = 3,
    ADC_CHANNEL_4  = 4,
    ADC_CHANNEL_5  = 5,
    ADC_CHANNEL_6  = 6,
    ADC_CHANNEL_7  = 7,
    ADC_CHANNEL_8  = 8,
    ADC_CHANNEL_9  = 9,
    ADC_CHANNEL_10 = 10,
    ADC_CHANNEL_11 = 11,
    ADC_CHANNEL_12 = 12,
    ADC_CHANNEL_13 = 13,
    ADC_CHANNEL_14 = 14,
    ADC_CHANNEL_15 = 15,
    ADC_CHANNEL_TEMP  = 16,   /* مستشعر الحرارة الداخلي */
    ADC_CHANNEL_VREF  = 17,   /* مرجع الجهد الداخلي (1.2V) */
    ADC_CHANNEL_VBAT  = 18,   /* VBAT / 4 لقياس البطارية */
} adc_channel_t;

/** دقة التحويل */
typedef enum {
    ADC_RESOLUTION_12BIT = 0,  /* 12-bit: 0..4095 */
    ADC_RESOLUTION_10BIT = 1,  /* 10-bit: 0..1023 */
    ADC_RESOLUTION_8BIT  = 2,  /* 8-bit:  0..255  */
    ADC_RESOLUTION_6BIT  = 3,  /* 6-bit:  0..63   */
} adc_resolution_t;

/** وقت أخذ العينة */
typedef enum {
    ADC_SAMPLETIME_3   = 0,   /* 3 دورات */
    ADC_SAMPLETIME_15  = 1,
    ADC_SAMPLETIME_28  = 2,
    ADC_SAMPLETIME_56  = 3,
    ADC_SAMPLETIME_84  = 4,
    ADC_SAMPLETIME_112 = 5,
    ADC_SAMPLETIME_144 = 6,
    ADC_SAMPLETIME_480 = 7,   /* 480 دورة — للمستشعرات البطيئة */
} adc_sampletime_t;

typedef enum {
    ADC_OK          =  0,
    ADC_ERR_TIMEOUT = -1,
    ADC_ERR_OVR     = -2,   /* Overrun — بيانات ضاعت */
    ADC_ERR_CONFIG  = -3,
} adc_result_t;

/** تهيئة قناة واحدة */
typedef struct {
    adc_channel_t    channel;
    adc_sampletime_t sample_time;
    uint8_t          rank;       /* ترتيب في Scan sequence (1-16) */
} adc_channel_config_t;

/** إعدادات ADC الكاملة */
typedef struct {
    adc_port_t           port;
    adc_resolution_t     resolution;
    bool                 continuous;        /* تحويل مستمر */
    bool                 scan_mode;         /* Scan متعدد القنوات */
    bool                 use_dma;           /* DMA للبيانات المستمرة */
    bool                 end_of_conv_irq;   /* مقاطعة عند نهاية التحويل */
    uint8_t              num_channels;
    adc_channel_config_t channels[16];
    /* Analog Watchdog */
    bool                 use_watchdog;
    adc_channel_t        watchdog_channel;
    uint16_t             watchdog_high;     /* حد أعلى */
    uint16_t             watchdog_low;      /* حد أدنى */
    void (*watchdog_cb)(adc_channel_t ch, uint16_t val);
} adc_config_t;


/* =============================================================================
 * API
 * =============================================================================
 */

/**
 * @brief تهيئة ADC
 */
adc_result_t adc_init(const adc_config_t *cfg);

/**
 * @brief تحويل فوري لقناة واحدة (حجب حتى الانتهاء)
 * @return القيمة الخام (0..4095 لـ 12-bit)
 */
uint16_t adc_read_channel(adc_port_t port, adc_channel_t ch,
                           adc_sampletime_t sample_time);

/**
 * @brief تحويل Scan لجميع القنوات المُهيأة → يملأ buf
 */
adc_result_t adc_read_scan(adc_port_t port, uint16_t *buf,
                            size_t num_channels, uint32_t timeout_ms);

/**
 * @brief تحويل فوري + تحويل القيمة لـ mV
 * @param vref_mv  جهد المرجع (عادةً 3300 mV)
 */
uint32_t adc_read_voltage_mv(adc_port_t port, adc_channel_t ch,
                              uint32_t vref_mv);

/**
 * @brief بدء التحويل المستمر عبر DMA
 * @param buf       مخزن النتائج (دوري — يُحدَّث تلقائياً)
 * @param callback  تُستدعى عند اكتمال كل دورة
 */
adc_result_t adc_start_dma(adc_port_t port, uint16_t *buf,
                             size_t len, void (*callback)(uint16_t*));

/**
 * @brief إيقاف التحويل المستمر
 */
void adc_stop(adc_port_t port);

/**
 * @brief قراءة درجة حرارة المعالج (°C)
 */
float adc_read_temperature(void);

/**
 * @brief قراءة جهد VBAT (مفيد لأنظمة البطارية)
 */
float adc_read_vbat(void);

/**
 * @brief معايرة ADC (تُجرى مرة واحدة بعد كل Power-On)
 */
adc_result_t adc_calibrate(adc_port_t port);

/**
 * @brief إيقاف ADC
 */
void adc_deinit(adc_port_t port);

/* IRQ */
void ADC_IRQHandler(void);

#ifdef __cplusplus
}
#endif

#endif /* ROBOOS_ADC_H */
