; =============================================================================
; RoboOS — Context Switch (ARM Cortex-M4 RTOS Core)
; =============================================================================
; هذا الملف يُنفِّذ قلب نظام التشغيل الفوري (RTOS):
;   تبديل السياق (Context Switch) بين المهام عبر PendSV_Handler
;
; آلية العمل:
;   - عند استدعاء الجدولة، يُفعَّل PendSV الذي له أدنى أولوية
;   - Cortex-M4 يحفظ تلقائياً {r0-r3, r12, lr, pc, xpsr} على Stack
;   - نحن نحفظ يدوياً {r4-r11} والـ PSP (Process Stack Pointer)
;   - نستدعي scheduler_get_next_task() للحصول على TCB المهمة الجديدة
;   - نستعيد {r4-r11} من stack المهمة الجديدة
;   - نُعيد تعيين PSP وEXC_RETURN للعودة للمهمة الجديدة
;
; تخطيط TCB (Task Control Block) المُتوقع من C:
;   struct TCB {
;       uint32_t *stack_ptr;  // offset 0x00 — حقل أول دائماً
;       ...
;   };
; =============================================================================

    .syntax unified
    .cpu    cortex-m4
    .fpu    fpv4-sp-d16
    .thumb

; ---- رموز خارجية -----------------------------------------------------------
    .extern scheduler_get_next_tcb     ; رجع: r0 = pointer to new TCB
    .extern g_current_tcb              ; مؤشر المهمة الحالية (TCB**)

; =============================================================================
; PendSV_Handler — تبديل السياق الأساسي
; =============================================================================
    .global PendSV_Handler
    .section .text.PendSV_Handler, "ax", %progbits
    .type   PendSV_Handler, %function

PendSV_Handler:
    ; --------------------------------------------------------
    ; 1. أوقف المقاطعات خلال التبديل لضمان الأمان
    ; --------------------------------------------------------
    cpsid   i

    ; --------------------------------------------------------
    ; 2. اقرأ PSP (Process Stack Pointer) للمهمة الحالية
    ;    r0 = PSP الحالي
    ; --------------------------------------------------------
    mrs     r0, psp
    isb

    ; --------------------------------------------------------
    ; 3. احفظ السياق الموسَّع: {r4-r11} + FPU registers
    ;    Cortex-M4 لا يحفظ r4-r11 تلقائياً
    ; --------------------------------------------------------
    ; احفظ r4-r11 على stack المهمة الحالية
    stmdb   r0!, {r4-r11}

    ; --------------------------------------------------------
    ; 4. احفظ PSP الجديد في TCB المهمة الحالية
    ;    g_current_tcb يشير لـ TCB** — أي *(g_current_tcb) = current TCB
    ;    أول حقل في TCB هو stack_ptr
    ; --------------------------------------------------------
    ldr     r2, =g_current_tcb
    ldr     r2, [r2]            ; r2 = pointer to current TCB
    str     r0, [r2, #0]        ; TCB->stack_ptr = PSP المحدَّث

    ; --------------------------------------------------------
    ; 5. استدعاء الجدولة للحصول على المهمة التالية
    ;    scheduler_get_next_tcb() → r0 = new TCB*
    ; --------------------------------------------------------
    push    {lr}                ; احفظ EXC_RETURN
    bl      scheduler_get_next_tcb
    pop     {lr}

    ; --------------------------------------------------------
    ; 6. حدِّث g_current_tcb بالمهمة الجديدة
    ; --------------------------------------------------------
    ldr     r2, =g_current_tcb
    str     r0, [r2]            ; g_current_tcb = new TCB*

    ; --------------------------------------------------------
    ; 7. استعِد PSP من TCB الجديد
    ;    أول حقل في TCB هو stack_ptr
    ; --------------------------------------------------------
    ldr     r0, [r0, #0]        ; r0 = new TCB->stack_ptr

    ; --------------------------------------------------------
    ; 8. استعِد {r4-r11} من stack المهمة الجديدة
    ; --------------------------------------------------------
    ldmia   r0!, {r4-r11}

    ; --------------------------------------------------------
    ; 9. اضبط PSP على Stack المهمة الجديدة
    ; --------------------------------------------------------
    msr     psp, r0
    isb

    ; --------------------------------------------------------
    ; 10. أعِد تفعيل المقاطعات
    ; --------------------------------------------------------
    cpsie   i

    ; --------------------------------------------------------
    ; 11. عُد عبر EXC_RETURN لتنفيذ المهمة الجديدة
    ;     LR = 0xFFFFFFFD (العودة لـ Thread Mode باستخدام PSP)
    ; --------------------------------------------------------
    bx      lr

    .size   PendSV_Handler, . - PendSV_Handler


; =============================================================================
; portYIELD — طلب تبديل السياق من C code
; يُفعِّل PendSV الذي يُنفَّذ بعد اكتمال المهمة الحالية
; =============================================================================
    .global portYIELD
    .section .text.portYIELD, "ax", %progbits
    .type   portYIELD, %function

portYIELD:
    ; اضبط PENDSVSET bit في ICSR (Interrupt Control and State Register)
    ldr     r0, =0xE000ED04
    ldr     r1, =0x10000000     ; bit 28 = PENDSVSET
    str     r1, [r0]
    dsb                         ; ضمان كتابة الأمر
    isb
    bx      lr
    .size   portYIELD, . - portYIELD


; =============================================================================
; task_create_stack — تهيئة Stack مهمة جديدة (initial context)
; Input : r0 = stack top (uint32_t*), r1 = task function ptr
; Output: r0 = PSP الابتدائي للمهمة (يُحفظ في TCB->stack_ptr)
; =============================================================================
    .global task_create_stack
    .section .text.task_create_stack, "ax", %progbits
    .type   task_create_stack, %function

task_create_stack:
    ; Cortex-M4 يتوقع Stack Frame الأولي على هذا الشكل:
    ;  [top-1]  xPSR  = 0x01000000 (T-bit مضبوط)
    ;  [top-2]  PC    = عنوان المهمة
    ;  [top-3]  LR    = 0xFFFFFFFD (EXC_RETURN للخروج من المقاطعة)
    ;  [top-4]  R12   = 0
    ;  [top-5]  R3    = 0
    ;  [top-6]  R2    = 0
    ;  [top-7]  R1    = 0
    ;  [top-8]  R0    = 0
    ;  --- هذا ما بحفظه نحن يدوياً ---
    ;  [top-9]  R11   = 0
    ;  ...
    ;  [top-16] R4    = 0

    ; ابدأ من أعلى الـ Stack (متوافق مع Cortex-M4 full-descending stack)
    ; أولاً: الجزء الذي يحفظه HW تلقائياً
    mov     r2, #0x01000000     ; xPSR: T-bit
    str     r2, [r0, #-4]!     ; Push xPSR
    str     r1, [r0, #-4]!     ; Push PC = task function
    ldr     r2, =0xFFFFFFFD
    str     r2, [r0, #-4]!     ; Push LR = EXC_RETURN
    movs    r2, #0
    str     r2, [r0, #-4]!     ; Push R12=0
    str     r2, [r0, #-4]!     ; Push R3=0
    str     r2, [r0, #-4]!     ; Push R2=0
    str     r2, [r0, #-4]!     ; Push R1=0
    str     r2, [r0, #-4]!     ; Push R0=0

    ; ثانياً: الجزء الذي نحفظه نحن (r4-r11)
    str     r2, [r0, #-4]!     ; Push R11=0
    str     r2, [r0, #-4]!     ; Push R10=0
    str     r2, [r0, #-4]!     ; Push R9=0
    str     r2, [r0, #-4]!     ; Push R8=0
    str     r2, [r0, #-4]!     ; Push R7=0
    str     r2, [r0, #-4]!     ; Push R6=0
    str     r2, [r0, #-4]!     ; Push R5=0
    str     r2, [r0, #-4]!     ; Push R4=0

    ; r0 = PSP الابتدائي للمهمة الجديدة
    bx      lr
    .size   task_create_stack, . - task_create_stack

; إنهاء الملف
