; =============================================================================
; RoboOS — Peripheral Assembly Helpers (ARM Cortex-M4)
; =============================================================================
; دوال أسمبلي عالية الأداء لتعزيز درايفرات المحيطات:
;   - قراءة/كتابة سجلات بضمان ترتيب الذاكرة
;   - DMA burst helpers
;   - Bit-banding للتحكم الذري بالـ GPIO
;   - Fast SPI byte pump
;   - I2C timeout microsecond delay
;   - ADC start & poll (بدون انتظار busy في C)
; =============================================================================

    .syntax unified
    .cpu    cortex-m4
    .fpu    fpv4-sp-d16
    .thumb

    .section .text

; ---- ثوابت عناوين السجلات (STM32F4) ----------------------------------------
    .equ    SPI1_DR,    0x4001300C  /* SPI1 Data Register */
    .equ    SPI1_SR,    0x40013008  /* SPI1 Status Register */
    .equ    SPI2_DR,    0x4000380C
    .equ    SPI2_SR,    0x40003808
    .equ    ADC1_SR,    0x40012000  /* ADC1 Status Register */
    .equ    ADC1_CR2,   0x40012008
    .equ    ADC1_DR,    0x4001204C
    .equ    SPI_SR_TXE, (1 << 1)   /* Tx Empty */
    .equ    SPI_SR_RXNE,(1 << 0)   /* Rx Not Empty */
    .equ    SPI_SR_BSY, (1 << 7)   /* Busy */
    .equ    ADC_SR_EOC, (1 << 1)   /* End of Conversion */
    .equ    ADC_CR2_SWSTART, (1 << 30)

; =============================================================================
; [1] PERIPHERAL REGISTER READ with DSB
; Input : r0 = عنوان السجل
; Output: r0 = القيمة
; الضمان: أي عمليات ذاكرة سابقة تكتمل قبل القراءة
; =============================================================================
    .global periph_read32
    .type   periph_read32, %function
periph_read32:
    dsb     sy              ; أكمل كل الكتابات السابقة
    ldr     r0, [r0]        ; قراءة مضمونة
    bx      lr
    .size   periph_read32, . - periph_read32


; =============================================================================
; [2] PERIPHERAL REGISTER WRITE with DSB
; Input : r0 = عنوان السجل, r1 = القيمة
; =============================================================================
    .global periph_write32
    .type   periph_write32, %function
periph_write32:
    str     r1, [r0]        ; كتابة السجل
    dsb     sy              ; انتظر اكتمال الكتابة
    bx      lr
    .size   periph_write32, . - periph_write32


; =============================================================================
; [3] FAST SPI BYTE PUMP — SPI1
; نقل مجموعة بايتات بأسرع وقت ممكن (بدون C loop overhead)
; Input : r0 = pointer to Tx data, r1 = pointer to Rx buf, r2 = len
; =============================================================================
    .global asm_spi1_transfer_burst
    .type   asm_spi1_transfer_burst, %function
asm_spi1_transfer_burst:
    push    {r4-r6, lr}
    ldr     r4, =SPI1_SR
    ldr     r5, =SPI1_DR
    cbz     r2, .spi_burst_done

.spi_burst_loop:
    ; انتظر TXE
.spi_wait_txe:
    ldr     r6, [r4]
    tst     r6, #SPI_SR_TXE
    beq     .spi_wait_txe
    ; أرسل بايتاً
    cmp     r0, #0
    itee    ne
    ldrbne  r6, [r0], #1   ; إذا tx_data موجود: load and advance
    moveq   r6, #0xFF       ; وإلا أرسل 0xFF
    strb    r6, [r5]
    ; انتظر RXNE
.spi_wait_rxne:
    ldr     r6, [r4]
    tst     r6, #SPI_SR_RXNE
    beq     .spi_wait_rxne
    ; استقبل بايتاً
    ldrb    r6, [r5]
    cmp     r1, #0
    it      ne
    strbne  r6, [r1], #1   ; إذا rx_buf موجود: save and advance
    ; تكرار
    subs    r2, r2, #1
    bne     .spi_burst_loop

    ; انتظر انتهاء آخر بايت (BSY clear)
.spi_wait_bsy:
    ldr     r6, [r4]
    tst     r6, #SPI_SR_BSY
    bne     .spi_wait_bsy

.spi_burst_done:
    pop     {r4-r6, pc}
    .size   asm_spi1_transfer_burst, . - asm_spi1_transfer_burst


; =============================================================================
; [4] ADC SOFTWARE START + POLL (ADC1)
; يبدأ التحويل ويعود بالنتيجة فوراً (بدون loop في C)
; Input : r0 = channel number (0-18)
; Output: r0 = raw ADC value (12-bit)
; =============================================================================
    .global asm_adc1_read_channel
    .type   asm_adc1_read_channel, %function
asm_adc1_read_channel:
    push    {r4-r5, lr}

    ldr     r4, =ADC1_SR
    ldr     r5, =ADC1_CR2

    ; مسح EOC
    ldr     r1, [r4]
    bic     r1, r1, #ADC_SR_EOC
    str     r1, [r4]

    ; بدء التحويل (SWSTART)
    ldr     r1, [r5]
    orr     r1, r1, #ADC_CR2_SWSTART
    str     r1, [r5]
    dsb

    ; الانتظار حتى EOC
.adc_poll_loop:
    ldr     r1, [r4]
    tst     r1, #ADC_SR_EOC
    beq     .adc_poll_loop

    ; قراءة النتيجة
    ldr     r1, =ADC1_DR
    ldr     r0, [r1]
    and     r0, r0, #0xFFF  ; 12-bit mask

    pop     {r4-r5, pc}
    .size   asm_adc1_read_channel, . - asm_adc1_read_channel


; =============================================================================
; [5] GPIO BIT-BAND SET — تغيير بت GPIO بشكل ذري
; ARM Cortex-M4 يدعم Bit-Banding في منطقة 0x40000000-0x400FFFFF
; Bit-band alias = 0x42000000 + (byte_offset × 32) + (bit × 4)
;
; Input : r0 = عنوان GPIO_ODR, r1 = pin number (0-15), r2 = value (0 أو 1)
; =============================================================================
    .global asm_gpio_bit_write
    .type   asm_gpio_bit_write, %function
asm_gpio_bit_write:
    ; احسب عنوان Bit-Band alias
    ; peripheral_byte_offset = r0 - 0x40000000
    ldr     r3, =0x40000000
    sub     r0, r0, r3          ; r0 = byte offset من بداية القسم

    ldr     r3, =0x42000000
    lsl     r0, r0, #5          ; × 32
    add     r0, r3, r0          ; base + byte_offset × 32
    lsl     r1, r1, #2          ; bit × 4
    add     r0, r0, r1          ; + bit × 4

    ; الكتابة الذرية
    str     r2, [r0]
    bx      lr
    .size   asm_gpio_bit_write, . - asm_gpio_bit_write


; =============================================================================
; [6] MICROSECOND DELAY — تأخير دقيق بالميكروثانية
; Input : r0 = عدد الميكروثواني
; يفترض: CPU = 168MHz → 168 دورة لكل µs
; 8 تعليمات في الحلقة ≈ 8/168 µs → نحسب loops = us × 168 / 8 = us × 21
; =============================================================================
    .global asm_delay_us
    .type   asm_delay_us, %function
asm_delay_us:
    ; loops = r0 × 21
    movs    r1, #21
    mul     r0, r0, r1
    cbz     r0, .delay_us_done
.delay_us_loop:
    nop
    nop
    nop
    nop
    subs    r0, r0, #1
    bne     .delay_us_loop
.delay_us_done:
    bx      lr
    .size   asm_delay_us, . - asm_delay_us


; =============================================================================
; [7] MEMCPY32 — نسخ سريع بالكلمات (4 بايت في كل دورة)
; Input : r0 = dest, r1 = src, r2 = count (عدد الكلمات الـ 32-bit)
; =============================================================================
    .global asm_memcpy32
    .type   asm_memcpy32, %function
asm_memcpy32:
    cbz     r2, .memcpy32_done
.memcpy32_loop:
    ldr     r3, [r1], #4
    str     r3, [r0], #4
    subs    r2, r2, #1
    bne     .memcpy32_loop
.memcpy32_done:
    bx      lr
    .size   asm_memcpy32, . - asm_memcpy32


; =============================================================================
; [8] MEMSET32 — تصفير سريع بالكلمات
; Input : r0 = dest, r1 = value (uint32), r2 = count (كلمات)
; =============================================================================
    .global asm_memset32
    .type   asm_memset32, %function
asm_memset32:
    cbz     r2, .memset32_done
.memset32_loop:
    str     r1, [r0], #4
    subs    r2, r2, #1
    bne     .memset32_loop
.memset32_done:
    bx      lr
    .size   asm_memset32, . - asm_memset32

; إنهاء الملف
