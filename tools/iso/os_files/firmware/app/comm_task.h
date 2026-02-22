/**
 * @file comm_task.h / comm_task.c
 * @brief UART Communication & Debug Logging Task
 * يطبع إحصائيات النظام والبيانات الحية كل ثانية عبر UART1 (115200 baud).
 */

#ifndef COMM_TASK_H
#define COMM_TASK_H
void comm_task_entry(void);
#endif
