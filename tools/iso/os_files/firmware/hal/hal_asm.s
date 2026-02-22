; =============================================================================
; RoboOS — HAL Assembly Primitives (ARM Cortex-M4)
; =============================================================================
; دوال HAL التي لا يمكن تنفيذها بكفاءة أو صحة بالـ C وحده:
;   - تعليمات ضبط المقاطعات (CPSID/CPSIE)
;   - حواجز الذاكرة (DSB، ISB، DMB)
;   - الدخول لوضع الطاقة المنخفضة (WFI، WFE)
;   - عمليات bit-banding الذرية
;   - قراءة System Registers (CONTROL، PRIMASK...)
; =============================================================================

    .syntax unified
    .cpu    cortex-m4
    .fpu    fpv4-sp-d16
    .thumb

    .section .text

; =============================================================================
; [1] INTERRUPT CONTROL
; =============================================================================

    ; تعطيل جميع المقاطعات القابلة للتعطيل
    .global hal_disable_irq
    .type   hal_disable_irq, %function
hal_disable_irq:
    cpsid   i
    bx      lr
    .size   hal_disable_irq, . - hal_disable_irq

    ; تفعيل المقاطعات
    .global hal_enable_irq
    .type   hal_enable_irq, %function
hal_enable_irq:
    cpsie   i
    bx      lr
    .size   hal_enable_irq, . - hal_enable_irq

    ; تعطيل المقاطعات وإرجاع PRIMASK السابق (للأقسام الحرجة)
    ; Output: r0 = قيمة PRIMASK السابقة
    .global hal_enter_critical
    .type   hal_enter_critical, %function
hal_enter_critical:
    mrs     r0, primask         ; احفظ الحالة الحالية
    cpsid   i                   ; أوقف المقاطعات
    bx      lr
    .size   hal_enter_critical, . - hal_enter_critical

    ; استعادة PRIMASK (الخروج من القسم الحرج)
    ; Input: r0 = قيمة PRIMASK المحفوظة سابقاً
    .global hal_exit_critical
    .type   hal_exit_critical, %function
hal_exit_critical:
    msr     primask, r0         ; استعِد الحالة
    bx      lr
    .size   hal_exit_critical, . - hal_exit_critical


; =============================================================================
; [2] MEMORY BARRIERS — ضرورية بعد تعديل Hardware Registers
; =============================================================================

    ; Data Synchronization Barrier — انتظر تنفيذ كل عمليات الذاكرة
    .global hal_dsb
    .type   hal_dsb, %function
hal_dsb:
    dsb     sy
    bx      lr
    .size   hal_dsb, . - hal_dsb

    ; Instruction Synchronization Barrier — مسح Pipeline بعد تغيير التهيئة
    .global hal_isb
    .type   hal_isb, %function
hal_isb:
    isb     sy
    bx      lr
    .size   hal_isb, . - hal_isb

    ; Data Memory Barrier — ضمان ترتيب الوصول للذاكرة المشتركة
    .global hal_dmb
    .type   hal_dmb, %function
hal_dmb:
    dmb     sy
    bx      lr
    .size   hal_dmb, . - hal_dmb


; =============================================================================
; [3] POWER MANAGEMENT
; =============================================================================

    ; Wait For Interrupt — دخول وضع Sleep حتى أول مقاطعة
    .global hal_wfi
    .type   hal_wfi, %function
hal_wfi:
    wfi
    bx      lr
    .size   hal_wfi, . - hal_wfi

    ; Wait For Event — دخول وضع Sleep حتى أول حدث
    .global hal_wfe
    .type   hal_wfe, %function
hal_wfe:
    wfe
    bx      lr
    .size   hal_wfe, . - hal_wfe

    ; SEND EVENT — إيقاظ المعالج من WFE
    .global hal_sev
    .type   hal_sev, %function
hal_sev:
    sev
    bx      lr
    .size   hal_sev, . - hal_sev


; =============================================================================
; [4] SYSTEM REGISTER ACCESS
; =============================================================================

    ; قراءة سجل CONTROL (Thread/Handler mode, PSP/MSP, FPU active)
    .global hal_get_control
    .type   hal_get_control, %function
hal_get_control:
    mrs     r0, control
    bx      lr
    .size   hal_get_control, . - hal_get_control

    ; تعيين سجل CONTROL
    .global hal_set_control
    .type   hal_set_control, %function
hal_set_control:
    msr     control, r0
    isb                         ; متطلب بعد تعديل CONTROL
    bx      lr
    .size   hal_set_control, . - hal_set_control

    ; قراءة PSP (Process Stack Pointer)
    .global hal_get_psp
    .type   hal_get_psp, %function
hal_get_psp:
    mrs     r0, psp
    bx      lr
    .size   hal_get_psp, . - hal_get_psp

    ; تعيين PSP
    .global hal_set_psp
    .type   hal_set_psp, %function
hal_set_psp:
    msr     psp, r0
    bx      lr
    .size   hal_set_psp, . - hal_set_psp

    ; قراءة MSP (Main Stack Pointer)
    .global hal_get_msp
    .type   hal_get_msp, %function
hal_get_msp:
    mrs     r0, msp
    bx      lr
    .size   hal_get_msp, . - hal_get_msp


; =============================================================================
; [5] ATOMIC BIT OPERATIONS — قراءة/تعديل/كتابة أتومية
; يستخدم LDREX/STREX (Load/Store Exclusive) لـ Cortex-M4
; =============================================================================

    ; ذري: تحميل كلمة 32-bit (Load Exclusive)
    ; Input : r0 = عنوان
    ; Output: r0 = القيمة
    .global hal_atomic_load
    .type   hal_atomic_load, %function
hal_atomic_load:
    ldrex   r0, [r0]
    bx      lr
    .size   hal_atomic_load, . - hal_atomic_load

    ; ذري: تخزين كلمة 32-bit (Store Exclusive)
    ; Input : r0 = عنوان, r1 = قيمة جديدة
    ; Output: r0 = 0 (نجاح) أو 1 (فشل — يُعاد المحاولة)
    .global hal_atomic_store
    .type   hal_atomic_store, %function
hal_atomic_store:
    strex   r0, r1, [r0]
    bx      lr
    .size   hal_atomic_store, . - hal_atomic_store

    ; Compare-And-Swap ذري
    ; Input : r0 = عنوان, r1 = قيمة متوقعة, r2 = قيمة جديدة
    ; Output: r0 = 0 (تم التبديل) أو 1 (القيمة مختلفة)
    .global hal_cas
    .type   hal_cas, %function
hal_cas:
    ldrex   r3, [r0]            ; r3 = القيمة الحالية
    cmp     r3, r1              ; هل تساوي المتوقعة؟
    bne     .cas_fail
    strex   r3, r2, [r0]        ; حاول الكتابة
    cmp     r3, #0
    bne     hal_cas             ; إذا فشل strex (contention) → أعِد المحاولة
    movs    r0, #0              ; نجاح
    bx      lr
.cas_fail:
    clrex                       ; امسح حالة exclusive monitor
    movs    r0, #1              ; فشل
    bx      lr
    .size   hal_cas, . - hal_cas


; =============================================================================
; [6] NOP DELAY — تأخير بسيط للـ Startup Delays
; Input: r0 = عدد التكرارات (loops)
; =============================================================================
    .global hal_delay_loops
    .type   hal_delay_loops, %function
hal_delay_loops:
    cbz     r0, .delay_done
.delay_loop:
    subs    r0, r0, #1
    bne     .delay_loop
.delay_done:
    bx      lr
    .size   hal_delay_loops, . - hal_delay_loops

; إنهاء الملف
