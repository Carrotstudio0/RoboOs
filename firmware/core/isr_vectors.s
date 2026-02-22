; =============================================================================
; RoboOS — Interrupt Vector Table (ARM Cortex-M4)
; =============================================================================
; يُعرِّف هذا الملف جدول المقاطعات الكامل لـ Cortex-M4.
; يُوضع في قسم .isr_vector الذي يربطه linker.ld عند عنوان 0x00000000.
;
; ترتيب الجدول (حسب ARM Architecture Reference Manual):
;   [0]  = قيمة مبدئية لـ Stack Pointer (MSP)
;   [1]  = Reset Handler
;   [2]  = NMI Handler
;   ... إلخ
; =============================================================================

    .syntax unified
    .cpu    cortex-m4
    .thumb

; ---- رموز خارجية -----------------------------------------------------------
    .extern Reset_Handler
    .extern _estack             ; نهاية Stack (تعريفها في linker.ld)

; ---- رموز ضعيفة (weak) — تُعرَّف في ملفات أخرى أو تبقى Default ----------
    .weak  NMI_Handler
    .weak  HardFault_Handler
    .weak  MemManage_Handler
    .weak  BusFault_Handler
    .weak  UsageFault_Handler
    .weak  SVC_Handler
    .weak  DebugMon_Handler
    .weak  PendSV_Handler
    .weak  SysTick_Handler

; ---- IRQs خاصة بالمحيطات (STM32F4 نموذجاً) --------------------------------
    .weak  WWDG_IRQHandler
    .weak  PVD_IRQHandler
    .weak  TAMP_STAMP_IRQHandler
    .weak  RTC_WKUP_IRQHandler
    .weak  FLASH_IRQHandler
    .weak  RCC_IRQHandler
    .weak  EXTI0_IRQHandler
    .weak  EXTI1_IRQHandler
    .weak  EXTI2_IRQHandler
    .weak  EXTI3_IRQHandler
    .weak  EXTI4_IRQHandler
    .weak  DMA1_Stream0_IRQHandler
    .weak  DMA1_Stream1_IRQHandler
    .weak  DMA1_Stream2_IRQHandler
    .weak  DMA1_Stream3_IRQHandler
    .weak  DMA1_Stream4_IRQHandler
    .weak  DMA1_Stream5_IRQHandler
    .weak  DMA1_Stream6_IRQHandler
    .weak  ADC_IRQHandler
    .weak  TIM1_UP_TIM10_IRQHandler
    .weak  TIM2_IRQHandler
    .weak  TIM3_IRQHandler
    .weak  TIM4_IRQHandler
    .weak  USART1_IRQHandler
    .weak  USART2_IRQHandler
    .weak  USART3_IRQHandler
    .weak  I2C1_EV_IRQHandler
    .weak  SPI1_IRQHandler
    .weak  SPI2_IRQHandler

; =============================================================================
; Vector Table — موضوعة في Flash (ROM) عند 0x00000000
; =============================================================================
    .section .isr_vector, "a", %progbits
    .type   g_pfnVectors, %object

g_pfnVectors:
    ; --- Core Cortex-M4 Exceptions ---
    .word   _estack                    ; 0x000: Initial Stack Pointer
    .word   Reset_Handler              ; 0x004: Reset
    .word   NMI_Handler                ; 0x008: Non-Maskable Interrupt
    .word   HardFault_Handler          ; 0x00C: Hard Fault
    .word   MemManage_Handler          ; 0x010: Memory Management Fault
    .word   BusFault_Handler           ; 0x014: Bus Fault
    .word   UsageFault_Handler         ; 0x018: Usage Fault
    .word   0                          ; 0x01C: Reserved
    .word   0                          ; 0x020: Reserved
    .word   0                          ; 0x024: Reserved
    .word   0                          ; 0x028: Reserved
    .word   SVC_Handler                ; 0x02C: Supervisor Call (Syscall)
    .word   DebugMon_Handler           ; 0x030: Debug Monitor
    .word   0                          ; 0x034: Reserved
    .word   PendSV_Handler             ; 0x038: Pendable Service (Context Switch)
    .word   SysTick_Handler            ; 0x03C: System Tick Timer (RTOS Tick)

    ; --- External Peripheral IRQs (IRQ0 → IRQ...) ---
    .word   WWDG_IRQHandler            ; IRQ0:  Window WatchDog
    .word   PVD_IRQHandler             ; IRQ1:  PVD via EXTI Line
    .word   TAMP_STAMP_IRQHandler      ; IRQ2:  Tamper Timestamp
    .word   RTC_WKUP_IRQHandler        ; IRQ3:  RTC Wakeup
    .word   FLASH_IRQHandler           ; IRQ4:  Flash global
    .word   RCC_IRQHandler             ; IRQ5:  RCC global
    .word   EXTI0_IRQHandler           ; IRQ6:  EXTI Line 0
    .word   EXTI1_IRQHandler           ; IRQ7:  EXTI Line 1
    .word   EXTI2_IRQHandler           ; IRQ8:  EXTI Line 2
    .word   EXTI3_IRQHandler           ; IRQ9:  EXTI Line 3
    .word   EXTI4_IRQHandler           ; IRQ10: EXTI Line 4
    .word   DMA1_Stream0_IRQHandler    ; IRQ11: DMA1 Stream 0
    .word   DMA1_Stream1_IRQHandler    ; IRQ12: DMA1 Stream 1
    .word   DMA1_Stream2_IRQHandler    ; IRQ13: DMA1 Stream 2
    .word   DMA1_Stream3_IRQHandler    ; IRQ14: DMA1 Stream 3
    .word   DMA1_Stream4_IRQHandler    ; IRQ15: DMA1 Stream 4
    .word   DMA1_Stream5_IRQHandler    ; IRQ16: DMA1 Stream 5
    .word   DMA1_Stream6_IRQHandler    ; IRQ17: DMA1 Stream 6
    .word   ADC_IRQHandler             ; IRQ18: ADC global
    .word   0                          ; IRQ19: Reserved
    .word   0                          ; IRQ20: Reserved
    .word   0                          ; IRQ21: Reserved
    .word   0                          ; IRQ22: Reserved
    .word   TIM1_UP_TIM10_IRQHandler   ; IRQ25: TIM1 Update / TIM10
    .word   0                          ; IRQ26: Reserved
    .word   0                          ; IRQ27: Reserved
    .word   TIM2_IRQHandler            ; IRQ28: TIM2
    .word   TIM3_IRQHandler            ; IRQ29: TIM3
    .word   TIM4_IRQHandler            ; IRQ30: TIM4
    .word   I2C1_EV_IRQHandler         ; IRQ31: I2C1 Event
    .word   0                          ; IRQ32: Reserved
    .word   SPI1_IRQHandler            ; IRQ35: SPI1
    .word   SPI2_IRQHandler            ; IRQ36: SPI2
    .word   USART1_IRQHandler          ; IRQ37: USART1
    .word   USART2_IRQHandler          ; IRQ38: USART2
    .word   USART3_IRQHandler          ; IRQ39: USART3

    .size   g_pfnVectors, . - g_pfnVectors

; إنهاء الملف
