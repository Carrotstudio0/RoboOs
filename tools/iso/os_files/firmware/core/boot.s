; =============================================================================
; RoboOS — Real Bootloader (ARM Cortex-M4)
; =============================================================================
; يبدأ هذا الملف من نقطة الإعادة الحقيقية Reset_Handler.
; يؤدي:
;   1. نقل قسم .data من Flash إلى RAM
;   2. تصفير قسم .bss
;   3. استدعاء SystemInit() لتهيئة الساعات والذاكرة
;   4. استدعاء main() — دخول نواة RoboOS
; =============================================================================

    .syntax unified
    .cpu    cortex-m4
    .fpu    fpv4-sp-d16
    .thumb

; ---- رموز مُصدَّرة ----------------------------------------------------------
    .global Reset_Handler
    .global Default_Handler

; ---- رموز مستوردة من Linker Script (linker.ld) -----------------------------
    .extern _sidata        ; عنوان بيانات .data في Flash (LMA)
    .extern _sdata         ; بداية .data في RAM (VMA)
    .extern _edata         ; نهاية .data في RAM
    .extern _sbss          ; بداية .bss
    .extern _ebss          ; نهاية .bss
    .extern SystemInit     ; تهيئة الساعة (CMSIS)
    .extern main           ; نواة RoboOS

; =============================================================================
; Reset_Handler — أول كود ينفذ بعد إعادة التشغيل
; =============================================================================
    .section .text.Reset_Handler, "ax", %progbits
    .type   Reset_Handler, %function

Reset_Handler:
    ; --------------------------------------------------------
    ; 1. أوقف جميع المقاطعات لنضمن بدء آمن
    ; --------------------------------------------------------
    cpsid   i

    ; --------------------------------------------------------
    ; 2. نقل .data من Flash (LMA) إلى RAM (VMA)
    ;    r0 = مصدر (Flash) | r1 = وجهة (RAM) | r2 = نهاية
    ; --------------------------------------------------------
    ldr     r0, =_sidata
    ldr     r1, =_sdata
    ldr     r2, =_edata
    b       .copy_data_check
.copy_data_loop:
    ldr     r3, [r0], #4
    str     r3, [r1], #4
.copy_data_check:
    cmp     r1, r2
    bcc     .copy_data_loop

    ; --------------------------------------------------------
    ; 3. تصفير .bss (المتغيرات غير المهيأة)
    ;    r0 = بداية .bss | r1 = نهاية .bss | r2 = صفر
    ; --------------------------------------------------------
    ldr     r0, =_sbss
    ldr     r1, =_ebss
    movs    r2, #0
    b       .zero_bss_check
.zero_bss_loop:
    str     r2, [r0], #4
.zero_bss_check:
    cmp     r0, r1
    bcc     .zero_bss_loop

    ; --------------------------------------------------------
    ; 4. تفعيل FPU — Cortex-M4 يتطلب تفعيله يدوياً
    ;    CPACR (0xE000ED88) bits [23:20] = 0xF للوصول الكامل
    ; --------------------------------------------------------
    ldr     r0, =0xE000ED88
    ldr     r1, [r0]
    orr     r1, r1, #(0xF << 20)
    str     r1, [r0]
    dsb                         ; Data Sync Barrier
    isb                         ; Instruction Sync Barrier

    ; --------------------------------------------------------
    ; 5. استدعاء SystemInit (تهيئة PLL، ساعة النظام)
    ; --------------------------------------------------------
    bl      SystemInit

    ; --------------------------------------------------------
    ; 6. تفعيل المقاطعات ثم القفز لـ main() — نواة RoboOS
    ; --------------------------------------------------------
    cpsie   i
    bl      main

    ; --------------------------------------------------------
    ; 7. إذا عاد main (لا يجب) — حلقة لا نهائية آمنة
    ; --------------------------------------------------------
.hang:
    wfi
    b       .hang

    .size   Reset_Handler, . - Reset_Handler


; =============================================================================
; Default_Handler — معالج افتراضي لأي مقاطعة غير مُعرَّفة
; =============================================================================
    .section .text.Default_Handler, "ax", %progbits
    .type   Default_Handler, %function
    .weak   Default_Handler

Default_Handler:
    ; أدخل حالة Debug إذا كان Debugger متصلاً، وإلا حلقة لا نهائية
    bkpt    #0
.loop_default:
    wfi
    b       .loop_default

    .size   Default_Handler, . - Default_Handler


; =============================================================================
; Weak aliases — كل المقاطعات تشير لـ Default_Handler إذا لم تُعرَّف
; =============================================================================
    .weak  NMI_Handler
    .thumb_set NMI_Handler, Default_Handler

    .weak  HardFault_Handler
    .thumb_set HardFault_Handler, Default_Handler

    .weak  MemManage_Handler
    .thumb_set MemManage_Handler, Default_Handler

    .weak  BusFault_Handler
    .thumb_set BusFault_Handler, Default_Handler

    .weak  UsageFault_Handler
    .thumb_set UsageFault_Handler, Default_Handler

    .weak  SVC_Handler
    .thumb_set SVC_Handler, Default_Handler

    .weak  DebugMon_Handler
    .thumb_set DebugMon_Handler, Default_Handler

    .weak  PendSV_Handler
    .thumb_set PendSV_Handler, Default_Handler

    .weak  SysTick_Handler
    .thumb_set SysTick_Handler, Default_Handler

; إنهاء الملف
