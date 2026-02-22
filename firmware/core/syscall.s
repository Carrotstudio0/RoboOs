; =============================================================================
; RoboOS — SVC (System Call) Handler (ARM Cortex-M4)
; =============================================================================
; توفر هذه الطبقة بوابة منظمة بين كود المستخدم ونواة النظام.
;
; كيفية استخدام Syscall من C:
;   void task_yield(void) { asm volatile("svc #0"); }
;   void task_sleep(uint32_t ms) { asm volatile("svc #1"); }
;   int  task_create(...) { asm volatile("svc #2"); }
;
; تُرسَل المعاملات عبر {r0, r1, r2, r3} وفق ARM AAPCS.
; رقم الـ syscall مضمَّن في تعليمة SVC نفسها (imm8).
;
; جدول Syscalls:
;   SVC #0  = YIELD    : تنازُل عن المعالج طوعاً
;   SVC #1  = SLEEP    : تأخير بالميلي-ثانية (r0 = ms)
;   SVC #2  = CREATE   : إنشاء مهمة جديدة
;   SVC #3  = TERMINATE: إنهاء المهمة الحالية
;   SVC #4  = MUTEX_LOCK  : قفل Mutex
;   SVC #5  = MUTEX_UNLOCK: فتح Mutex
; =============================================================================

    .syntax unified
    .cpu    cortex-m4
    .thumb

; ---- رموز خارجية -----------------------------------------------------------
    .extern svc_yield           ; kernel: تنازل عن المعالج
    .extern svc_sleep           ; kernel: تأخير مهمة
    .extern svc_task_create     ; kernel: إنشاء مهمة
    .extern svc_task_terminate  ; kernel: إنهاء مهمة
    .extern svc_mutex_lock      ; kernel: قفل Mutex
    .extern svc_mutex_unlock    ; kernel: فتح Mutex

; =============================================================================
; SVC_Handler — معالج استدعاءات النظام
; =============================================================================
    .global SVC_Handler
    .section .text.SVC_Handler, "ax", %progbits
    .type   SVC_Handler, %function

SVC_Handler:
    ; --------------------------------------------------------
    ; 1. حدِّد من أين جاء الاستدعاء: Thread Mode أو Handler Mode
    ;    إذا LR bit 2 = 1 → استُخدم PSP | وإلا MSP
    ; --------------------------------------------------------
    tst     lr, #4
    ite     eq
    mrseq   r0, msp             ; Handler Mode → MSP
    mrsne   r0, psp             ; Thread Mode  → PSP

    ; --------------------------------------------------------
    ; 2. استخرج رقم الـ SVC من التعليمة نفسها
    ;    Stack Frame: [r0+24] = PC وقت الاستدعاء
    ;    التعليمة عند PC-2 هي "SVC #n" → byte الأخير = رقم n
    ; --------------------------------------------------------
    ldr     r1, [r0, #24]       ; r1 = PC وقت SVC
    ldrb    r2, [r1, #-2]       ; r2 = رقم الـ syscall (imm8 من SVC)

    ; --------------------------------------------------------
    ; 3. أعِد تحميل المعاملات من Stack للوظيفة المستدعاة
    ;    Stack Frame (منخفض → مرتفع):
    ;    r0, r1, r2, r3, r12, lr, pc, xpsr
    ; --------------------------------------------------------
    ldm     r0, {r0-r3}         ; استعِد r0-r3 كمعاملات

    ; --------------------------------------------------------
    ; 4. Dispatch: وجِّه لـ Handler المناسب
    ; --------------------------------------------------------
    cmp     r2, #0
    beq     .svc_yield
    cmp     r2, #1
    beq     .svc_sleep
    cmp     r2, #2
    beq     .svc_create
    cmp     r2, #3
    beq     .svc_terminate
    cmp     r2, #4
    beq     .svc_mutex_lock
    cmp     r2, #5
    beq     .svc_mutex_unlock
    ; syscall غير معروف — تجاهل
    bx      lr

.svc_yield:
    b       svc_yield

.svc_sleep:
    b       svc_sleep

.svc_create:
    b       svc_task_create

.svc_terminate:
    b       svc_task_terminate

.svc_mutex_lock:
    b       svc_mutex_lock

.svc_mutex_unlock:
    b       svc_mutex_unlock

    .size   SVC_Handler, . - SVC_Handler


; =============================================================================
; Syscall Wrappers — للاستخدام من C بدون inline asm
; =============================================================================

    ; yield() — تنازُل طوعي عن المعالج
    .global sys_yield
    .section .text.sys_yield, "ax", %progbits
    .type   sys_yield, %function
sys_yield:
    svc     #0
    bx      lr
    .size   sys_yield, . - sys_yield

    ; sys_sleep(uint32_t ms) — تأخير
    .global sys_sleep
    .section .text.sys_sleep, "ax", %progbits
    .type   sys_sleep, %function
sys_sleep:
    svc     #1
    bx      lr
    .size   sys_sleep, . - sys_sleep

    ; sys_task_terminate() — إنهاء المهمة الحالية
    .global sys_task_terminate
    .section .text.sys_task_terminate, "ax", %progbits
    .type   sys_task_terminate, %function
sys_task_terminate:
    svc     #3
    bx      lr
    .size   sys_task_terminate, . - sys_task_terminate

; إنهاء الملف
