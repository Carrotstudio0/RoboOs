; =============================================================================
; RoboOS — High-Performance Math & DSP Suite (ARM Cortex-M4 + FPU)
; =============================================================================
; مجموعة دوال رياضية محسّنة يدوياً تستغل:
;   - وحدة FPU العائمة المدمجة (VFP4)
;   - تعليمات SIMD للـ Cortex-M4 (SMLAL, SMULL, USAD8...)
;   - تعليمات DSP (SSAT, USAT, REV...)
; =============================================================================

    .syntax unified
    .cpu    cortex-m4
    .fpu    fpv4-sp-d16
    .thumb

    .section .text

; =============================================================================
; [1] FLOAT FAST SQUARE ROOT
; Input : s0 = x (float)
; Output: s0 = sqrt(x)
; Cycles: ~14 (hardware VSQRT vs ~100+ software)
; =============================================================================
    .global asm_fast_sqrt
    .type   asm_fast_sqrt, %function
asm_fast_sqrt:
    vsqrt.f32   s0, s0
    bx          lr
    .size   asm_fast_sqrt, . - asm_fast_sqrt


; =============================================================================
; [2] FIXED-POINT 16.16 MULTIPLY
; Input : r0 = x (Q16.16), r1 = y (Q16.16)
; Output: r0 = (x * y) >> 16
; =============================================================================
    .global asm_fixed_multiply
    .type   asm_fixed_multiply, %function
asm_fixed_multiply:
    smull   r2, r3, r0, r1      ; 64-bit signed multiply: [r3:r2] = r0*r1
    lsr     r0, r2, #16         ; الجزء السفلي
    orr     r0, r0, r3, lsl #16 ; دمج مع الجزء العلوي
    bx      lr
    .size   asm_fixed_multiply, . - asm_fixed_multiply


; =============================================================================
; [3] FLOAT DOT PRODUCT — Vector3 (3×float)
; Input : r0 = pointer to vec3 A, r1 = pointer to vec3 B
; Output: s0 = A.x*B.x + A.y*B.y + A.z*B.z
; =============================================================================
    .global asm_vec3_dot
    .type   asm_vec3_dot, %function
asm_vec3_dot:
    vldm    r0, {s0-s2}         ; تحميل A.x, A.y, A.z
    vldm    r1, {s4-s6}         ; تحميل B.x, B.y, B.z
    vmul.f32 s0, s0, s4         ; s0 = Ax*Bx
    vmla.f32 s0, s1, s5         ; s0 += Ay*By
    vmla.f32 s0, s2, s6         ; s0 += Az*Bz
    bx      lr
    .size   asm_vec3_dot, . - asm_vec3_dot


; =============================================================================
; [4] FLOAT CROSS PRODUCT — Vector3
; Input : r0 = pointer to result (vec3), r1 = A, r2 = B
; Output: [r0] = A × B
; =============================================================================
    .global asm_vec3_cross
    .type   asm_vec3_cross, %function
asm_vec3_cross:
    vldm    r1, {s0-s2}         ; A.x, A.y, A.z
    vldm    r2, {s4-s6}         ; B.x, B.y, B.z
    ; Result.x = Ay*Bz - Az*By
    vmul.f32 s8, s1, s6
    vmls.f32 s8, s2, s5
    ; Result.y = Az*Bx - Ax*Bz
    vmul.f32 s9, s2, s4
    vmls.f32 s9, s0, s6
    ; Result.z = Ax*By - Ay*Bx
    vmul.f32 s10, s0, s5
    vmls.f32 s10, s1, s4
    vstm    r0, {s8-s10}        ; حفظ النتيجة
    bx      lr
    .size   asm_vec3_cross, . - asm_vec3_cross


; =============================================================================
; [5] PID CONTROLLER UPDATE (fixed-point Q16.16)
; Input : r0 = error (Q16.16)
;         r1 = pointer to PID state: {Kp, Ki, Kd, integral, prev_error}
; Output: r0 = output (Q16.16)
; =============================================================================
; PID State layout (5 × int32):
;   [0] = Kp, [1] = Ki, [2] = Kd, [3] = integral, [4] = prev_error
    .global asm_pid_update
    .type   asm_pid_update, %function
asm_pid_update:
    push    {r4-r7, lr}

    ldm     r1, {r2-r6}         ; r2=Kp, r3=Ki, r4=Kd, r5=integral, r6=prev_error

    ; proportional = Kp * error
    smull   r7, r12, r2, r0
    lsr     r7, r7, #16
    orr     r7, r7, r12, lsl #16    ; r7 = proportional

    ; integral += error
    add     r5, r5, r0
    str     r5, [r1, #12]

    ; integral_term = Ki * integral
    smull   r12, r14, r3, r5
    lsr     r12, r12, #16
    orr     r12, r12, r14, lsl #16  ; r12 = integral_term

    ; derivative = Kd * (error - prev_error)
    sub     r14, r0, r6
    smull   r6, r8, r4, r14
    lsr     r6, r6, #16
    orr     r6, r6, r8, lsl #16     ; r6 = derivative_term

    ; save prev_error
    str     r0, [r1, #16]

    ; output = proportional + integral_term + derivative_term
    add     r0, r7, r12
    add     r0, r0, r6

    pop     {r4-r7, pc}
    .size   asm_pid_update, . - asm_pid_update


; =============================================================================
; [6] INTEGER CLAMP
; Input : r0 = value, r1 = min, r2 = max
; Output: r0 = clamp(value, min, max)
; =============================================================================
    .global asm_clamp
    .type   asm_clamp, %function
asm_clamp:
    cmp     r0, r1
    it      lt
    movlt   r0, r1              ; إذا أصغر من min => min
    cmp     r0, r2
    it      gt
    movgt   r0, r2              ; إذا أكبر من max => max
    bx      lr
    .size   asm_clamp, . - asm_clamp


; =============================================================================
; [7] FAST ABSOLUTE VALUE (integer)
; Input : r0 = value
; Output: r0 = |value|
; =============================================================================
    .global asm_abs
    .type   asm_abs, %function
asm_abs:
    cmp     r0, #0
    it      mi
    rsbmi   r0, r0, #0          ; r0 = 0 - r0 إذا سالب
    bx      lr
    .size   asm_abs, . - asm_abs


; =============================================================================
; [8] COUNT LEADING ZEROS (CLZ) — مفيد لتطبيع الأعداد
; Input : r0 = value
; Output: r0 = عدد الأصفار البادئة (0-32)
; =============================================================================
    .global asm_clz
    .type   asm_clz, %function
asm_clz:
    clz     r0, r0
    bx      lr
    .size   asm_clz, . - asm_clz


; =============================================================================
; [9] BYTE REVERSE — تحويل Endianness
; Input : r0 = 32-bit value
; Output: r0 = byte-reversed value
; =============================================================================
    .global asm_bswap32
    .type   asm_bswap32, %function
asm_bswap32:
    rev     r0, r0
    bx      lr
    .size   asm_bswap32, . - asm_bswap32


; إنهاء الملف
