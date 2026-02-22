/**
 * @file adc.c
 * @brief RoboOS ADC Driver Implementation — STM32F4xx
 */

#include "adc.h"

/* =============================================================================
 * STM32F4 ADC Register Map
 * =============================================================================
 */
typedef struct {
    volatile uint32_t SR;
    volatile uint32_t CR1;
    volatile uint32_t CR2;
    volatile uint32_t SMPR1;  /* قنوات 10-18 */
    volatile uint32_t SMPR2;  /* قنوات 0-9 */
    volatile uint32_t JOFR[4];
    volatile uint32_t HTR;
    volatile uint32_t LTR;
    volatile uint32_t SQR1;
    volatile uint32_t SQR2;
    volatile uint32_t SQR3;
    volatile uint32_t JSQR;
    volatile uint32_t JDR[4];
    volatile uint32_t DR;
} ADC_Regs_t;

/* Common Registers (مشترك بين ADC1-3) */
typedef struct {
    volatile uint32_t CSR;
    volatile uint32_t CCR;
    volatile uint32_t CDR;
} ADC_Common_t;

#define ADC1_BASE    0x40012000UL
#define ADC2_BASE    0x40012100UL
#define ADC3_BASE    0x40012200UL
#define ADC_CMN_BASE 0x40012300UL

static ADC_Regs_t* const ADC_PORTS[ADC_PORT_COUNT] = {
    (ADC_Regs_t*)ADC1_BASE,
    (ADC_Regs_t*)ADC2_BASE,
    (ADC_Regs_t*)ADC3_BASE,
};
static ADC_Common_t* const ADC_COMMON = (ADC_Common_t*)ADC_CMN_BASE;

/* RCC */
#define RCC_APB2ENR  (*((volatile uint32_t*)0x40023844))
#define RCC_ADC1EN   (1 << 8)
#define RCC_ADC2EN   (1 << 9)
#define RCC_ADC3EN   (1 << 10)
static const uint32_t RCC_ADC_EN[ADC_PORT_COUNT] = {RCC_ADC1EN, RCC_ADC2EN, RCC_ADC3EN};

/* SR Bits */
#define ADC_SR_EOC   (1 << 1)   /* End Of Conversion */
#define ADC_SR_OVR   (1 << 5)   /* Overrun */
#define ADC_SR_AWD   (1 << 0)   /* Analog Watchdog */

/* CR2 Bits */
#define ADC_CR2_ADON    (1 << 0)   /* ADC ON */
#define ADC_CR2_CONT    (1 << 1)   /* Continuous */
#define ADC_CR2_DMA     (1 << 8)   /* DMA enable */
#define ADC_CR2_DDS     (1 << 9)   /* DMA disable selection */
#define ADC_CR2_EOCS    (1 << 10)  /* EOC per conversion */
#define ADC_CR2_SWSTART (1 << 30)  /* Start conversion */

/* CR1 Bits */
#define ADC_CR1_SCAN    (1 << 8)   /* Scan mode */
#define ADC_CR1_AWDEN   (1 << 23)  /* Analog Watchdog enable */
#define ADC_CR1_EOCIE   (1 << 5)   /* EOC Interrupt enable */

/* CCR Common Register */
#define ADC_CCR_TSVREFE (1 << 23)  /* Temp sensor + Vref إذا */
#define ADC_CCR_VBATE   (1 << 22)  /* VBAT */
#define ADC_CCR_ADCPRE_DIV4 (1 << 16) /* ADCCLK = PCLK2 / 4 = 21 MHz */

extern volatile uint32_t g_systick_count;

/* DMA Callbacks */
static void (*adc_dma_callbacks[ADC_PORT_COUNT])(uint16_t*) = {NULL};
static uint16_t *adc_dma_bufs[ADC_PORT_COUNT] = {NULL};

/* =============================================================================
 * Helper: ضبط Sample Time لقناة
 * =============================================================================
 */
static void set_sample_time(ADC_Regs_t *adc, adc_channel_t ch, adc_sampletime_t st)
{
    if (ch >= 10) {
        uint32_t shift = ((uint32_t)ch - 10) * 3;
        adc->SMPR1 &= ~(0x7 << shift);
        adc->SMPR1 |= ((uint32_t)st << shift);
    } else {
        uint32_t shift = (uint32_t)ch * 3;
        adc->SMPR2 &= ~(0x7 << shift);
        adc->SMPR2 |= ((uint32_t)st << shift);
    }
}

/* =============================================================================
 * adc_init
 * =============================================================================
 */
adc_result_t adc_init(const adc_config_t *cfg)
{
    if (!cfg || cfg->port >= ADC_PORT_COUNT) return ADC_ERR_CONFIG;

    ADC_Regs_t *adc = ADC_PORTS[cfg->port];

    /* تفعيل الساعة */
    RCC_APB2ENR |= RCC_ADC_EN[cfg->port];

    /* ضبط Prescaler: ADCCLK = APB2 / 4 */
    ADC_COMMON->CCR = ADC_CCR_ADCPRE_DIV4;

    /* إيقاف ADC للتهيئة */
    adc->CR2 = 0;

    /* الدقة */
    adc->CR1 = (uint32_t)cfg->resolution << 24;

    /* Scan mode */
    if (cfg->scan_mode) adc->CR1 |= ADC_CR1_SCAN;

    /* EOC interrupt */
    if (cfg->end_of_conv_irq) adc->CR1 |= ADC_CR1_EOCIE;

    /* Continuous mode */
    if (cfg->continuous) adc->CR2 |= ADC_CR2_CONT;

    /* DMA */
    if (cfg->use_dma) adc->CR2 |= ADC_CR2_DMA | ADC_CR2_DDS;

    /* EOC per conversion */
    adc->CR2 |= ADC_CR2_EOCS;

    /* ضبط تسلسل القنوات */
    uint32_t num = cfg->num_channels > 16 ? 16 : cfg->num_channels;
    adc->SQR1 = ((num - 1) << 20);  /* L[3:0] = عدد القنوات - 1 */

    for (uint32_t i = 0; i < num; i++) {
        const adc_channel_config_t *ch_cfg = &cfg->channels[i];
        set_sample_time(adc, ch_cfg->channel, ch_cfg->sample_time);

        /* وضع القناة في التسلسل */
        uint8_t rank = ch_cfg->rank > 0 ? ch_cfg->rank - 1 : i;
        if (rank < 6) {
            adc->SQR3 |= ((uint32_t)ch_cfg->channel << (rank * 5));
        } else if (rank < 12) {
            adc->SQR2 |= ((uint32_t)ch_cfg->channel << ((rank - 6) * 5));
        } else {
            adc->SQR1 |= ((uint32_t)ch_cfg->channel << ((rank - 12) * 5));
        }
    }

    /* Analog Watchdog */
    if (cfg->use_watchdog) {
        adc->CR1 |= ADC_CR1_AWDEN | ((uint32_t)cfg->watchdog_channel << 0);
        adc->HTR = cfg->watchdog_high & 0xFFF;
        adc->LTR = cfg->watchdog_low  & 0xFFF;
    }

    /* تفعيل ADC */
    adc->CR2 |= ADC_CR2_ADON;

    /* انتظر استقرار ADC (≤ 3µs) */
    extern void hal_delay_loops(uint32_t);
    hal_delay_loops(504);  /* ~3µs @ 168MHz */

    return ADC_OK;
}

/* =============================================================================
 * adc_read_channel — تحويل فوري لقناة واحدة
 * =============================================================================
 */
uint16_t adc_read_channel(adc_port_t port, adc_channel_t ch,
                           adc_sampletime_t sample_time)
{
    ADC_Regs_t *adc = ADC_PORTS[port];

    /* هيئ القناة */
    set_sample_time(adc, ch, sample_time);

    /* SQR3: قناة واحدة فقط */
    adc->SQR3 = (uint32_t)ch;
    adc->SQR1 = 0;  /* L=0 = قناة واحدة */

    /* مسح EOC وبدء التحويل */
    adc->SR &= ~ADC_SR_EOC;
    adc->CR2 |= ADC_CR2_SWSTART;

    /* انتظر النتيجة (timeout 10ms) */
    uint32_t start = g_systick_count;
    while (!(adc->SR & ADC_SR_EOC)) {
        if ((g_systick_count - start) >= 10) return 0xFFFF;
    }

    return (uint16_t)(adc->DR & 0xFFF);
}

/* =============================================================================
 * adc_read_voltage_mv
 * =============================================================================
 */
uint32_t adc_read_voltage_mv(adc_port_t port, adc_channel_t ch,
                               uint32_t vref_mv)
{
    uint16_t raw = adc_read_channel(port, ch, ADC_SAMPLETIME_56);
    return ((uint32_t)raw * vref_mv) / 4096;
}

/* =============================================================================
 * adc_read_scan — قراءة متعددة القنوات
 * =============================================================================
 */
adc_result_t adc_read_scan(adc_port_t port, uint16_t *buf,
                            size_t num_channels, uint32_t timeout_ms)
{
    ADC_Regs_t *adc = ADC_PORTS[port];
    uint32_t start = g_systick_count;

    adc->SR &= ~ADC_SR_EOC;
    adc->CR2 |= ADC_CR2_SWSTART;

    for (size_t i = 0; i < num_channels; i++) {
        while (!(adc->SR & ADC_SR_EOC)) {
            if ((g_systick_count - start) >= timeout_ms) return ADC_ERR_TIMEOUT;
        }
        adc->SR &= ~ADC_SR_EOC;
        buf[i] = (uint16_t)(adc->DR & 0xFFF);
    }
    return ADC_OK;
}

/* =============================================================================
 * adc_read_temperature — مستشعر الحرارة الداخلي
 * =============================================================================
 */
float adc_read_temperature(void)
{
    ADC_COMMON->CCR |= ADC_CCR_TSVREFE;
    uint16_t raw = adc_read_channel(ADC_PORT_1, ADC_CHANNEL_TEMP,
                                    ADC_SAMPLETIME_480);
    /* نموذج معايرة STM32F4: T = ((Vsense - V25) / Avg_Slope) + 25 */
    /* V25 ≈ 0.76V, Avg_Slope ≈ 2.5 mV/°C, Vref = 3.3V */
    float vsense_mv = ((float)raw * 3300.0f) / 4096.0f;
    float temp = ((vsense_mv - 760.0f) / 2.5f) + 25.0f;
    return temp;
}

/* =============================================================================
 * adc_read_vbat
 * =============================================================================
 */
float adc_read_vbat(void)
{
    ADC_COMMON->CCR |= ADC_CCR_VBATE;
    uint16_t raw = adc_read_channel(ADC_PORT_1, ADC_CHANNEL_VBAT,
                                    ADC_SAMPLETIME_480);
    /* VBAT مقسومة على 4 داخلياً */
    return ((float)raw * 3300.0f / 4096.0f) * 4.0f;
}

/* =============================================================================
 * adc_calibrate — معايرة ADC
 * =============================================================================
 */
adc_result_t adc_calibrate(adc_port_t port)
{
    /* STM32F4 ليس له calibration منفصل مثل F1
     * لكن يمكن معايرة Vref: قرأ VREFIN_CAL من ذاكرة المصنع */
    (void)port;
    return ADC_OK;
}

/* =============================================================================
 * adc_start_dma
 * =============================================================================
 */
adc_result_t adc_start_dma(adc_port_t port, uint16_t *buf,
                             size_t len, void (*callback)(uint16_t*))
{
    adc_dma_bufs[port] = buf;
    adc_dma_callbacks[port] = callback;
    /* In real system: configure DMA2 Stream0 Channel0 for ADC1 */
    /* Then enable ADC_CR2_DMA and start conversion */
    ADC_PORTS[port]->CR2 |= ADC_CR2_SWSTART;
    return ADC_OK;
}

void adc_stop(adc_port_t port)
{
    ADC_PORTS[port]->CR2 &= ~(ADC_CR2_CONT | ADC_CR2_SWSTART);
}

void adc_deinit(adc_port_t port)
{
    ADC_PORTS[port]->CR2 = 0;
    RCC_APB2ENR &= ~RCC_ADC_EN[port];
}

/* IRQ */
void ADC_IRQHandler(void)
{
    /* فحص Watchdog */
    for (int p = 0; p < ADC_PORT_COUNT; p++) {
        if (ADC_PORTS[p]->SR & ADC_SR_AWD) {
            ADC_PORTS[p]->SR &= ~ADC_SR_AWD;
        }
    }
}
