/**
 * @file sensor_task.c
 * @brief MPU-6050 IMU Reading via I2C — RTOS Task
 *
 * يقرأ كل 10ms (100Hz) بيانات التسارع والدوران من MPU-6050
 * ويضعها في g_imu_data للاستخدام من مهام أخرى.
 */

#include "sensor_task.h"
#include "../kernel/scheduler.h"
#include "../kernel/irq.h"
#include "../drivers/i2c/i2c.h"

/* البيانات المشتركة بين المهام */
volatile imu_data_t g_imu_data = {0};

/* Mutex لحماية g_imu_data */
static mutex_t s_imu_mutex;

/* =============================================================================
 * تهيئة MPU-6050
 * =============================================================================
 */
static int mpu6050_init(void)
{
    /* تحقق من WHO_AM_I */
    uint8_t who;
    if (i2c_read_reg8(I2C_PORT_1, MPU6050_ADDR, MPU6050_REG_WHO_AM_I, &who) != I2C_OK) {
        return -1;
    }
    if (who != 0x68) return -2;

    /* أيقظ الحساس (PWR_MGMT_1 = 0) */
    i2c_write_reg8(I2C_PORT_1, MPU6050_ADDR, MPU6050_REG_PWR_MGMT_1, 0x00);

    /* Sample Rate = 1kHz / (1 + SMPLRT_DIV) → 9 = 100 Hz */
    i2c_write_reg8(I2C_PORT_1, MPU6050_ADDR, MPU6050_REG_SMPLRT_DIV, 9);

    /* DLPF = 42 Hz (CONFIG = 3) */
    i2c_write_reg8(I2C_PORT_1, MPU6050_ADDR, MPU6050_REG_CONFIG, 0x03);

    /* ±2g Accel, ±250°/s Gyro */
    i2c_write_reg8(I2C_PORT_1, MPU6050_ADDR, MPU6050_REG_GYRO_CFG, 0x00);
    i2c_write_reg8(I2C_PORT_1, MPU6050_ADDR, MPU6050_REG_ACCEL_CFG, 0x00);

    return 0;
}

/* =============================================================================
 * قراءة 14 بايت من MPU-6050 وتحويلها لوحدات حقيقية
 * =============================================================================
 */
static int mpu6050_read(imu_data_t *out, uint32_t ts)
{
    uint8_t raw[14];
    uint8_t reg = MPU6050_REG_ACCEL_XOUT;

    if (i2c_write_read(I2C_PORT_1, MPU6050_ADDR, &reg, 1, raw, 14) != I2C_OK) {
        return -1;
    }

    /* دمج الـ bytes (Big-Endian) */
    int16_t ax = (int16_t)((raw[0]  << 8) | raw[1]);
    int16_t ay = (int16_t)((raw[2]  << 8) | raw[3]);
    int16_t az = (int16_t)((raw[4]  << 8) | raw[5]);
    int16_t tp = (int16_t)((raw[6]  << 8) | raw[7]);
    int16_t gx = (int16_t)((raw[8]  << 8) | raw[9]);
    int16_t gy = (int16_t)((raw[10] << 8) | raw[11]);
    int16_t gz = (int16_t)((raw[12] << 8) | raw[13]);

    /* تحويل لوحدات حقيقية:
     * Accel: sensitivity = 16384 LSB/g (±2g scale)
     * Gyro:  sensitivity = 131 LSB/(°/s) (±250 °/s scale)
     * Temp:  T = (raw / 340.0) + 36.53
     */
    out->accel_x = (float)ax / 16384.0f;
    out->accel_y = (float)ay / 16384.0f;
    out->accel_z = (float)az / 16384.0f;
    out->gyro_x  = (float)gx / 131.0f;
    out->gyro_y  = (float)gy / 131.0f;
    out->gyro_z  = (float)gz / 131.0f;
    out->temp_c  = ((float)tp / 340.0f) + 36.53f;
    out->timestamp_ms = ts;

    return 0;
}

/* =============================================================================
 * sensor_task_entry — يعمل كل 10ms (100 Hz)
 * =============================================================================
 */
void sensor_task_entry(void)
{
    mutex_init(&s_imu_mutex, "imu");

    /* انتظر تهيئة I2C */
    task_sleep_ms(100);

    /* هيئ MPU-6050 */
    int ret = mpu6050_init();
    if (ret != 0) {
        /* خطأ في التهيئة — تأخير لا نهائي */
        for (;;) task_sleep_ms(1000);
    }

    for (;;) {
        imu_data_t local;
        uint32_t ts = scheduler_get_tick_count();

        if (mpu6050_read(&local, ts) == 0) {
            /* حدِّث البيانات المشتركة بشكل آمن */
            if (mutex_lock(&s_imu_mutex, 5)) {
                g_imu_data = local;
                mutex_unlock(&s_imu_mutex);
            }
        } else {
            /* محاولة استعادة I2C Bus */
            i2c_bus_recovery(I2C_PORT_1);
            task_sleep_ms(100);
            mpu6050_init();
        }

        task_sleep_ms(10);  /* 100 Hz */
    }
}
