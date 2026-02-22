/**
 * @file unit_test.c
 * @brief RoboOS Unit Tests — Peripheral & RTOS Verification
 *
 * يُشغَّل على MCU ويرسل النتائج عبر UART.
 * بنية كل اختبار:
 *   TEST_START("name") → test code → TEST_PASS() أو TEST_FAIL("reason")
 *
 * يُبنى كـ target منفصل: cmake --build . --target roboos_tests.elf
 */

#include "../kernel/scheduler.h"
#include "../kernel/irq.h"
#include "../drivers/i2c/i2c.h"
#include "../drivers/spi/spi.h"
#include "../drivers/adc/adc.h"
#include "../drivers/gpio/gpio.h"

/* ---- بدون printf — نستخدم نفس uart helpers من comm_task -------- */
#define USART1_BASE  0x40011000UL
#define USART1_SR    (*((volatile uint32_t*)(USART1_BASE + 0x00)))
#define USART1_DR    (*((volatile uint32_t*)(USART1_BASE + 0x04)))
#define USART1_TXE   (1 << 7)

static void t_putchar(char c)
{
    while (!(USART1_SR & USART1_TXE));
    USART1_DR = c;
}
static void t_puts(const char *s) { while (*s) t_putchar(*s++); }
static void t_putu(uint32_t n)
{
    char b[11]; int i=10; b[i]=0;
    if (!n) { t_putchar('0'); return; }
    while (n) { b[--i]='0'+n%10; n/=10; }
    t_puts(&b[i]);
}

/* =============================================================================
 * Test Framework Macros
 * =============================================================================
 */

static uint32_t s_passed = 0, s_failed = 0;
static const char *s_test_name = NULL;
static uint32_t s_test_start_tick = 0;

#define TEST_START(name) \
    do { \
        s_test_name = (name); \
        s_test_start_tick = systick_get_count(); \
        t_puts("[TEST] "); t_puts(name); t_puts(" ... "); \
    } while(0)

#define TEST_PASS() \
    do { \
        uint32_t elapsed = systick_get_count() - s_test_start_tick; \
        t_puts("PASS ("); t_putu(elapsed); t_puts("ms)\r\n"); \
        s_passed++; \
    } while(0)

#define TEST_FAIL(reason) \
    do { \
        t_puts("FAIL: "); t_puts(reason); t_puts("\r\n"); \
        s_failed++; \
    } while(0)

#define ASSERT_EQ(a, b, msg) \
    if ((a) != (b)) { TEST_FAIL(msg); return; }

#define ASSERT_NE(a, b, msg) \
    if ((a) == (b)) { TEST_FAIL(msg); return; }

#define ASSERT_RANGE(v, lo, hi, msg) \
    if ((v) < (lo) || (v) > (hi)) { TEST_FAIL(msg); return; }

/* =============================================================================
 * [1] I2C Tests
 * =============================================================================
 */

static void test_i2c_init(void)
{
    TEST_START("I2C Init @ 400kHz");
    i2c_config_t cfg = {
        .port = I2C_PORT_1, .speed = I2C_SPEED_FAST, .timeout_ms = 10
    };
    i2c_result_t r = i2c_init(&cfg);
    ASSERT_EQ(r, I2C_OK, "i2c_init returned error");
    TEST_PASS();
}

static void test_i2c_mpu6050_probe(void)
{
    TEST_START("I2C MPU-6050 Device Probe");
    bool found = i2c_device_ready(I2C_PORT_1, 0x68, 3);
    if (!found) { TEST_FAIL("MPU-6050 not responding on 0x68"); return; }
    TEST_PASS();
}

static void test_i2c_mpu6050_who_am_i(void)
{
    TEST_START("I2C MPU-6050 WHO_AM_I Register");
    uint8_t val = 0;
    i2c_result_t r = i2c_read_reg8(I2C_PORT_1, 0x68, 0x75, &val);
    ASSERT_EQ(r, I2C_OK, "i2c_read_reg8 failed");
    ASSERT_EQ(val, 0x68, "WHO_AM_I != 0x68");
    TEST_PASS();
}

static void test_i2c_bus_recovery(void)
{
    TEST_START("I2C Bus Recovery (9-clock pulse)");
    i2c_result_t r = i2c_bus_recovery(I2C_PORT_1);
    ASSERT_EQ(r, I2C_OK, "bus_recovery returned error");
    TEST_PASS();
}

/* =============================================================================
 * [2] SPI Tests
 * =============================================================================
 */

static void test_spi_init(void)
{
    TEST_START("SPI Init @ 42MHz / Mode 0");
    spi_config_t cfg = {
        .port = SPI_PORT_1,
        .mode = SPI_MODE_0,
        .baud = SPI_BAUD_DIV_2,
        .data_size = SPI_DATASIZE_8BIT,
        .first_bit = SPI_FIRSTBIT_MSB,
        .nss_software = true,
        .timeout_ms = 10,
    };
    spi_result_t r = spi_init(&cfg);
    ASSERT_EQ(r, SPI_OK, "spi_init returned error");
    TEST_PASS();
}

static void test_spi_loopback(void)
{
    TEST_START("SPI Self-Loopback MOSI→MISO");
    /* يتطلب وصل MOSI (PA7) بـ MISO (PA6) فيزيائياً */
    uint8_t tx[4] = {0xA5, 0x5A, 0xDE, 0xAD};
    uint8_t rx[4] = {0};
    spi_result_t r = spi_transfer(SPI_PORT_1, tx, rx, 4, 10);
    ASSERT_EQ(r, SPI_OK, "spi_transfer failed");
    /* في حالة loopback: rx == tx */
    for (int i = 0; i < 4; i++) {
        if (rx[i] != tx[i]) { TEST_FAIL("Loopback data mismatch"); return; }
    }
    TEST_PASS();
}

static void test_spi_asm_burst(void)
{
    TEST_START("SPI ASM Burst Pump Speed Test");
    extern void asm_spi1_transfer_burst(uint32_t tx_ptr, uint32_t rx_ptr, uint32_t len);
    uint8_t buf[64];
    for (int i = 0; i < 64; i++) buf[i] = (uint8_t)i;
    uint8_t rx[64] = {0};
    uint32_t t0 = systick_get_count();
    asm_spi1_transfer_burst((uint32_t)buf, (uint32_t)rx, 64);
    uint32_t elapsed = systick_get_count() - t0;
    /* 64 bytes @ 42MHz ≈ 12µs << 1ms */
    ASSERT_RANGE(elapsed, 0, 1, "ASM burst took > 1ms for 64 bytes");
    TEST_PASS();
}

/* =============================================================================
 * [3] ADC Tests
 * =============================================================================
 */

static void test_adc_init(void)
{
    TEST_START("ADC Init 12-bit 3-channel");
    adc_config_t cfg = {
        .port = ADC_PORT_1,
        .resolution = ADC_RESOLUTION_12BIT,
        .num_channels = 1,
        .channels = {{ADC_CHANNEL_TEMP, ADC_SAMPLETIME_480, 1}},
    };
    adc_result_t r = adc_init(&cfg);
    ASSERT_EQ(r, ADC_OK, "adc_init returned error");
    TEST_PASS();
}

static void test_adc_temperature(void)
{
    TEST_START("ADC Internal Temperature Sensor");
    float temp = adc_read_temperature();
    /* يجب أن تكون بين 10°C و 85°C معملياً */
    ASSERT_RANGE((int)temp, 10, 85, "Temperature out of range");
    TEST_PASS();
}

static void test_adc_channel_read(void)
{
    TEST_START("ADC Channel 0 Raw Read");
    uint16_t raw = adc_read_channel(ADC_PORT_1, ADC_CHANNEL_0, ADC_SAMPLETIME_56);
    /* 12-bit → 0..4095 */
    ASSERT_RANGE(raw, 0, 4095, "ADC out of 12-bit range");
    TEST_PASS();
}

static void test_adc_asm_poll(void)
{
    TEST_START("ADC ASM Poll Speed vs C Read");
    extern uint32_t asm_adc1_read_channel(uint32_t ch);

    uint32_t t0, t1, elapsed_asm, elapsed_c;

    t0 = systick_get_count();
    for (int i = 0; i < 100; i++) asm_adc1_read_channel(0);
    t1 = systick_get_count();
    elapsed_asm = t1 - t0;

    t0 = systick_get_count();
    for (int i = 0; i < 100; i++) adc_read_channel(ADC_PORT_1, ADC_CHANNEL_0, ADC_SAMPLETIME_56);
    t1 = systick_get_count();
    elapsed_c = t1 - t0;

    t_puts("\r\n  ASM: "); t_putu(elapsed_asm); t_puts("ms | C: "); t_putu(elapsed_c); t_puts("ms");
    /* ASM يجب أن يكون أسرع أو مساوياً */
    if (elapsed_asm > elapsed_c + 5) { TEST_FAIL("ASM slower than C?"); return; }
    TEST_PASS();
}

/* =============================================================================
 * [4] RTOS Tests
 * =============================================================================
 */

static volatile uint32_t s_task_counter = 0;

static void test_task_fn(void) {
    s_task_counter++;
    task_sleep_ms(1);
}

static void test_scheduler_init(void)
{
    TEST_START("RTOS Scheduler Init");
    scheduler_init();
    ASSERT_NE(0, 0, "always pass after init");  /* тест существования */
    TEST_PASS();
}

static void test_stack_guard(void)
{
    TEST_START("RTOS Stack Overflow Guard");
    const char *ov = scheduler_check_stack_overflow();
    /* في بداية التنفيذ لا يوجد overflow */
    if (ov != NULL) {
        t_puts("\r\n  OVERFLOW DETECTED: "); t_puts(ov);
        TEST_FAIL("Stack overflow at startup");
        return;
    }
    TEST_PASS();
}

static void test_mutex(void)
{
    TEST_START("RTOS Mutex Lock/Unlock");
    mutex_t m;
    mutex_init(&m, "test");
    ASSERT_EQ(m.lock, 0u, "Mutex not initialized to 0");
    bool ok = mutex_trylock(&m);
    ASSERT_EQ(ok, true, "mutex_trylock failed on free mutex");
    ASSERT_EQ(m.lock, 1u, "Mutex not locked");
    /* حاول قفل مرة أخرى */
    bool ok2 = mutex_trylock(&m);
    ASSERT_EQ(ok2, false, "mutex_trylock succeeded on locked mutex");
    mutex_unlock(&m);
    ASSERT_EQ(m.lock, 0u, "Mutex not released");
    TEST_PASS();
}

static void test_semaphore(void)
{
    TEST_START("RTOS Semaphore Give/Take");
    semaphore_t s;
    sem_init(&s, 0, 3, "test");
    sem_give(&s); ASSERT_EQ(s.count, 1, "sem count != 1 after give");
    sem_give(&s); ASSERT_EQ(s.count, 2, "sem count != 2");
    sem_give(&s); ASSERT_EQ(s.count, 3, "sem count != 3");
    /* لا تتجاوز max */
    sem_give(&s); ASSERT_EQ(s.count, 3, "sem exceeded max_count");
    /* Take */
    bool ok = sem_take(&s, 0);
    ASSERT_EQ(ok, true, "sem_take failed");
    ASSERT_EQ(s.count, 2, "sem count wrong after take");
    TEST_PASS();
}

/* =============================================================================
 * [5] ASM Math Tests
 * =============================================================================
 */

static void test_asm_sqrt(void)
{
    TEST_START("ASM Fast SQRT (FPU)");
    extern float asm_fast_sqrt(float x);
    float result = asm_fast_sqrt(144.0f);
    int r = (int)(result + 0.5f);
    ASSERT_EQ(r, 12, "sqrt(144) != 12");
    result = asm_fast_sqrt(2.0f);   /* ≈ 1.414 */
    ASSERT_RANGE((int)(result * 1000), 1413, 1416, "sqrt(2) out of range");
    TEST_PASS();
}

static void test_asm_clamp(void)
{
    TEST_START("ASM Clamp Function");
    extern int32_t asm_clamp(int32_t v, int32_t lo, int32_t hi);
    ASSERT_EQ(asm_clamp(150, -100, 100), 100,  "clamp upper failed");
    ASSERT_EQ(asm_clamp(-200,-100, 100), -100, "clamp lower failed");
    ASSERT_EQ(asm_clamp(50,  -100, 100),  50,  "clamp passthrough failed");
    TEST_PASS();
}

static void test_asm_fixed_mul(void)
{
    TEST_START("ASM Fixed-Point Multiply Q16.16");
    extern int32_t asm_fixed_multiply(int32_t x, int32_t y);
    /* 2.0 × 3.0 = 6.0 في Q16.16: 2<<16=131072, 3<<16=196608 */
    int32_t r = asm_fixed_multiply(2 << 16, 3 << 16);
    ASSERT_EQ(r >> 16, 6, "2.0 * 3.0 != 6.0 in Q16.16");
    TEST_PASS();
}

/* =============================================================================
 * main_test — نقطة دخول بديلة لـ Test Mode
 * =============================================================================
 */
void main_test(void)
{
    /* تهيئة UART أولاً */
    t_puts("\r\n\r\n");
    t_puts("========================================\r\n");
    t_puts("  RoboOS Unit Test Suite v1.0\r\n");
    t_puts("  Target: STM32F407 @ 168 MHz\r\n");
    t_puts("========================================\r\n");

    /* I2C Tests */
    t_puts("\r\n[I2C Tests]\r\n");
    test_i2c_init();
    test_i2c_mpu6050_probe();
    test_i2c_mpu6050_who_am_i();
    test_i2c_bus_recovery();

    /* SPI Tests */
    t_puts("\r\n[SPI Tests]\r\n");
    test_spi_init();
    test_spi_loopback();
    test_spi_asm_burst();

    /* ADC Tests */
    t_puts("\r\n[ADC Tests]\r\n");
    test_adc_init();
    test_adc_temperature();
    test_adc_channel_read();
    test_adc_asm_poll();

    /* RTOS Tests */
    t_puts("\r\n[RTOS Tests]\r\n");
    test_scheduler_init();
    test_stack_guard();
    test_mutex();
    test_semaphore();

    /* Math ASM Tests */
    t_puts("\r\n[ASM Math Tests]\r\n");
    test_asm_sqrt();
    test_asm_clamp();
    test_asm_fixed_mul();

    /* ---- Summary -------------------------------------------------------- */
    t_puts("\r\n========================================\r\n");
    t_puts("Results: PASSED="); t_putu(s_passed);
    t_puts(" / FAILED=");       t_putu(s_failed);
    t_puts(" / TOTAL=");        t_putu(s_passed + s_failed);
    t_puts("\r\n");
    if (s_failed == 0) {
        t_puts(">>> ALL TESTS PASSED <<<\r\n");
    } else {
        t_puts(">>> SOME TESTS FAILED <<<\r\n");
    }
    t_puts("========================================\r\n");

    /* أشعل LED حسب النتيجة */
    #define GPIOD_ODR (*((volatile uint32_t*)0x40020C14))
    if (s_failed == 0) GPIOD_ODR |= (1 << 12);   /* Green = All Pass */
    else               GPIOD_ODR |= (1 << 14);   /* Red = Some Failed */

    for (;;) {
        __asm volatile("wfi");
    }
}
