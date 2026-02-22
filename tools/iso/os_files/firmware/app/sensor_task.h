/**
 * @file sensor_task.h
 * @brief MPU-6050 IMU Sensor Task via I2C
 */

#ifndef SENSOR_TASK_H
#define SENSOR_TASK_H

#include <stdint.h>

/* MPU-6050 I2C Address */
#define MPU6050_ADDR        0x68  /* AD0=LOW */
#define MPU6050_ADDR_ALT    0x69  /* AD0=HIGH */

/* MPU-6050 Registers */
#define MPU6050_REG_PWR_MGMT_1  0x6B
#define MPU6050_REG_SMPLRT_DIV  0x19
#define MPU6050_REG_CONFIG      0x1A
#define MPU6050_REG_GYRO_CFG    0x1B
#define MPU6050_REG_ACCEL_CFG   0x1C
#define MPU6050_REG_ACCEL_XOUT  0x3B  /* 14 bytes: Ax,Ay,Az,Temp,Gx,Gy,Gz */
#define MPU6050_REG_WHO_AM_I    0x75  /* يجب أن يُرجع 0x68 */

/* بيانات الـ IMU */
typedef struct {
    float accel_x, accel_y, accel_z;   /* (g) */
    float gyro_x, gyro_y, gyro_z;      /* (deg/s) */
    float temp_c;                       /* (°C) */
    uint32_t timestamp_ms;
} imu_data_t;

/* Buffer مشترك مع باقي المهام */
extern volatile imu_data_t g_imu_data;

void sensor_task_entry(void);

#endif
