# RoboOS — مخطط المعمارية الكامل

> الهدف: ARM Cortex-M4 MCU (STM32F407) | 168 MHz | 512KB Flash | 128KB SRAM
> الإصدار: v2.0 — يشمل I2C + SPI + ADC + Peripheral ASM Helpers

---

## 1. خريطة الذاكرة (Memory Map)

```
0xFFFFFFFF ┌─────────────────────────────────────┐
           │         System ROM / Vendor          │
0xE0100000 ├─────────────────────────────────────┤
           │     Core Debug (ITM, DWT, FPB)       │
0xE0000000 ├─────────────────────────────────────┤
           │   PPB: NVIC + SCB + SysTick + FPU   │
0xE0000000 ├─────────────────────────────────────┤
           │                                     │
           │         Peripheral Buses            │
           │    (APB1/APB2: UART, SPI, I2C...)   │
0x40000000 ├─────────────────────────────────────┤
           │                                     │
           │         SRAM: 128 KB               │
           │  ┌──────────────────────────────┐   │
           │  │ 0x20020000 ← _estack (top)  │   │
           │  │ ███████████ Stack (8 KB) ██  │   │
           │  │ ·  ·  ·  grows downward ·  · │   │
           │  │                              │   │
           │  │ ·  ·  ·  grows upward ·  ·  │   │
           │  │ ░░░░░░░░░ Heap (16 KB) ░░░  │   │
           │  │ 0x20008000 ← _heap_end      │   │
           │  ├──────────────────────────────┤   │
           │  │ .bss   — uninit. globals    │   │
           │  │ .data  — init. globals      │   │
           │  │ 0x20000000 ← SRAM base      │   │
           │  └──────────────────────────────┘   │
0x20000000 ├─────────────────────────────────────┤
           │                                     │
           │         Flash ROM: 512 KB           │
           │  ┌──────────────────────────────┐   │
           │  │ .rodata — const data         │   │
           │  │ .text   — code (C + ASM)     │   │
           │  │ > isr_vectors.s              │   │
           │  │ > boot.s                     │   │
           │  │ > context_switch.s           │   │
           │  │ > syscall.s                  │   │
           │  │ > math_utils.s               │   │
           │  │ > hal_asm.s                  │   │
           │  │ > C drivers & kernel         │   │
           │  ├──────────────────────────────┤   │
           │  │ .isr_vector — Vector Table   │   │
           │  │ 0x08000000 ← Flash base      │   │
           │  └──────────────────────────────┘   │
0x08000000 └─────────────────────────────────────┘
```

---

## 2. طبقات النظام (System Layers)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         [APPLICATION LAYER]                              │
│                    firmware/app/ + firmware/robot_api/                   │
│   motor_control.py  │  led_control.py  │  robot_simulation.py            │
│   sensor_tasks.py   │  language_demo.py │  ai_robot_demo.py ★ NEW        │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │  API Calls / Custom Language Programs
┌────────────────────────────▼─────────────────────────────────────────────┐
│                     [LANGUAGE ENGINE LAYER]                              │
│                        firmware/lang/engine.py                           │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────────────┐  │
│  │    Lexer     │──▶│    Parser    │──▶│         Executor             │  │
│  │  (Tokenizer) │   │  (AST Build) │   │  (Runtime Variable/Func Mgr) │  │
│  └──────────────┘   └──────────────┘   └──────────────────────────────┘  │
│   Keywords: var, if, while, for, func, return, motor, sensor, led        │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────────┐
│                        [AI ENGINE LAYER]  ← ★ NEW                        │
│                        firmware/ai/engine.py                             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────────────┐  │
│  │  PID Control │   │ Fuzzy Logic  │   │   Q-Learning (RL Agent)      │  │
│  ├──────────────┤   ├──────────────┤   ├──────────────────────────────┤  │
│  │ Anomaly Det. │   │ A* Planning  │   │   Neural Network (Classifier)│  │
│  └──────────────┘   └──────────────┘   └──────────────────────────────┘  │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │  Task Requests
┌────────────────────────────▼─────────────────────────────────────────────┐
│                       [SCHEDULER LAYER]                                  │
│                  firmware/core/scheduler.py  (Python Sim)                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐     │
│  │  Task 0  │  │  Task 1  │  │  Task 2  │  │  Idle Task           │     │
│  │  READY   │  │ RUNNING  │  │ BLOCKED  │  │  hal_wfi() ← ASM     │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────────┘     │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │  SVC #n / PendSV
┌───────────────────────────▼──────────────────────────────────────────┐
│                      [KERNEL LAYER]  ← NEW                           │
│                     firmware/kernel/                                 │
│  ┌─────────────────────┐    ┌──────────────────────────────────────┐ │
│  │      irq.c          │    │         Assembly Handlers            │ │
│  │  systick_init()     │    │  PendSV_Handler  ← context_switch.s │ │
│  │  irq_enable()       │    │  SVC_Handler     ← syscall.s        │ │
│  │  irq_enter_critical │    │  SysTick_Handler → tick update       │ │
│  │  HardFault_Handler  │    │  HardFault_Handler (naked+C)         │ │
│  └─────────────────────┘    └──────────────────────────────────────┘ │
└───────────────────────────┬──────────────────────────────────────────┘
                            │ register reads/writes
┌───────────────────────────▼──────────────────────────────────────────┐
│                      [HAL LAYER]                                     │
│          firmware/hal/                                               │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │              hal_asm.s  ← NEW (Assembly Primitives)          │    │
│  │  hal_disable_irq()   hal_enable_irq()   hal_enter_critical() │    │
│  │  hal_dsb()           hal_isb()          hal_dmb()            │    │
│  │  hal_wfi()           hal_wfe()          hal_sev()            │    │
│  │  hal_get_psp()       hal_set_psp()      hal_get_control()    │    │
│  │  hal_atomic_load()   hal_atomic_store() hal_cas()            │    │
│  └──────────────────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │              __init__.py (Python HAL Simulation)             │    │
│  │  GPIO │ Timer │ UART │ PWM │ ADC                             │    │
│  └──────────────────────────────────────────────────────────────┘    │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────────┐
│                     [DRIVER LAYER]  (C)                              │
│                    firmware/drivers/                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────────────┐  │
│  │  gpio.c  │  │  uart.c  │  │  timer.c │  │  memory_manager.c   │  │
│  └──────────┘  └──────────┘  └──────────┘  └─────────────────────┘  │
└───────────────────────────┬──────────────────────────────────────────┘
                            │ registers
┌───────────────────────────▼──────────────────────────────────────────┐
│                     [ASSEMBLY CORE]  ← NEW                           │
│                    firmware/core/*.s                                 │
│  ┌──────────────────┐  ┌───────────────────┐  ┌──────────────────┐  │
│  │  isr_vectors.s   │  │     boot.s        │  │  math_utils.s    │  │
│  │  Vector Table    │  │  Reset_Handler    │  │  asm_fast_sqrt   │  │
│  │  [0] _estack     │  │  Copy .data       │  │  asm_vec3_dot    │  │
│  │  [1] Reset       │  │  Zero  .bss       │  │  asm_vec3_cross  │  │
│  │  [2] NMI         │  │  Enable FPU       │  │  asm_pid_update  │  │
│  │  [14] PendSV ─┐  │  │  SystemInit()     │  │  asm_clamp       │  │
│  │  [15] SysTick  │  │  │  → main()        │  │  asm_clz / bswap │  │
│  └────────────────│──┘  └───────────────────┘  └──────────────────┘  │
│  ┌────────────────▼──┐  ┌───────────────────────────────────────┐    │
│  │ context_switch.s  │  │         syscall.s                     │    │
│  │ PendSV_Handler    │  │  SVC_Handler                          │    │
│  │  cpsid i          │  │  SVC #0 → sys_yield()                 │    │
│  │  mrs r0, psp      │  │  SVC #1 → sys_sleep(ms)               │    │
│  │  stmdb {r4-r11}   │  │  SVC #2 → sys_task_create()           │    │
│  │  → scheduler()    │  │  SVC #3 → sys_task_terminate()        │    │
│  │  ldmia {r4-r11}   │  │  SVC #4 → sys_mutex_lock()            │    │
│  │  msr psp, r0      │  │  SVC #5 → sys_mutex_unlock()          │    │
│  │  cpsie i          │  │                                       │    │
│  │  bx lr            │  │                                       │    │
│  └───────────────────┘  └───────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────────┐
│                      [HARDWARE]                                      │
│              ARM Cortex-M4 (STM32F407 / STM32F411)                  │
│  CPU: 168MHz  │  FPU: fpv4-sp-d16  │  Flash: 512KB  │  SRAM: 128KB  │
│  Peripherals: GPIO, UART, SPI, I2C, TIM, ADC, DMA                   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. تدفق الـ Boot (Boot Sequence)

```
Power ON / Reset
      │
      ▼
[isr_vectors.s]
  g_pfnVectors[0] → _estack loaded into MSP (by CPU hardware)
  g_pfnVectors[1] → Reset_Handler address → CPU jumps there
      │
      ▼
[boot.s] Reset_Handler:
  1. cpsid i          ── تعطيل المقاطعات
  2. Copy .data:      ── نقل بيانات مهيأة من Flash → SRAM
     LDR r0 = _sidata (Flash LMA)
     LDR r1 = _sdata  (SRAM VMA)
     loop: STR [r0++] → [r1++] till r1==_edata
  3. Zero .bss:       ── تصفير متغيرات غير مهيأة
     loop: STR 0 → [r0++] till r0==_ebss
  4. Enable FPU:      ── كتابة CPACR bits [23:20] = 0xF
  5. bl SystemInit()  ── تهيئة PLL/Clock (168 MHz)
  6. cpsie i          ── تفعيل المقاطعات
  7. bl main()        ── دخول نواة RoboOS
  8. wfi loop         ── (لا يصل هنا أبداً)
      │
      ▼
[kernel] main() / RoboOS Kernel:
  1. systick_init(168_000_000, 1000) ── SysTick @1ms
  2. irq_set_priority(PendSV, LOWEST) ── تبديل السياق آخر شيء
  3. scheduler_init()
  4. task_create(motor_task, ...)
  5. task_create(sensor_task, ...)
  6. scheduler_start()    ── حلقة لا تنتهي
```

---

## 4. تدفق تبديل السياق (Context Switch)

```
SysTick IRQ (كل 1ms)
      │
      ▼
[irq.c] SysTick_Handler:
  g_systick_count++
  SCB_ICSR |= PENDSVSET ── طلب تشغيل PendSV
      │
      ▼ (بعد اكتمال جميع ISRs الأعلى أولوية)
[context_switch.s] PendSV_Handler:
  cpsid i                  ── Critical Section
  mrs r0, psp              ── قرأ PSP المهمة الحالية
  stmdb r0!, {r4-r11}      ── احفظ r4-r11 على Stack المهمة
  LDR current_tcb → str r0 ── احفظ PSP في TCB
  BL scheduler_get_next_tcb── الجدولة تختار المهمة التالية
  STR new_tcb              ── حدّث g_current_tcb
  LDR r0 = new TCB→sp      ── PSP الجديد
  ldmia r0!, {r4-r11}      ── استعِد r4-r11 من Stack الجديدة
  msr psp, r0              ── حدّث PSP
  cpsie i
  bx lr (EXC_RETURN=0xFFFFFFFD) ── عُد لـ Thread Mode بـ PSP
      │
      ▼
[خروج من PendSV — CPU يستعيد r0-r3, r12, lr, pc, xpsr تلقائياً]
  تنفيذ المهمة الجديدة من PC المحفوظ
```

---

## 5. بنية الملفات (File Structure)

```
os/
├── CMakeLists.txt                  ← نظام البناء (ARM + ASM + جميع المحيطات)
├── firmware/
│   ├── core/
│   │   ├── isr_vectors.s          ← [ASM] Vector Table الكامل
│   │   ├── boot.s                 ← [ASM] Real Bootloader
│   │   ├── context_switch.s       ← [ASM] RTOS Context Switch
│   │   ├── syscall.s              ← [ASM] SVC System Calls
│   │   ├── math_utils.s           ← [ASM] FPU/DSP Math Suite
│   │   ├── linker.ld              ← [LD]  Linker Script
│   │   └── scheduler.py           ← [PY]  Scheduler (Simulation)
│   ├── hal/
│   │   ├── hal_asm.s              ← [ASM] HAL Primitives
│   │   ├── peripheral_asm.s       ← [ASM] Peripheral Helpers ★ NEW
│   │   └── __init__.py            ← [PY]  GPIO/UART/Timer/PWM/ADC
│   ├── kernel/
│   │   ├── irq.h                  ← [C]   IRQ Interface
│   │   └── irq.c                  ← [C]   SysTick + NVIC + HardFault
│   ├── drivers/
│   │   ├── gpio/gpio.c            ← [C]  GPIO Driver
│   │   ├── uart/uart.c            ← [C]  UART Driver
│   │   ├── timer/timer.c          ← [C]  Timer Driver
│   │   ├── memory/memory_manager.c← [C]  Memory Manager
│   │   ├── i2c/i2c.h + i2c.c     ← [C]  I2C Driver  ★ NEW
│   │   ├── spi/spi.h + spi.c     ← [C]  SPI Driver  ★ NEW
│   │   └── adc/adc.h + adc.c     ← [C]  ADC Driver  ★ NEW
│   ├── include/
│   │   ├── gpio.h
│   │   ├── uart.h
│   │   ├── timer.h
│   │   └── memory_manager.h
│   ├── lang/engine.py             ← [PY] Language Engine
│   ├── robot_api/robot.py         ← [PY] Robot API
│   └── simulator/                 ← [PY] PC Simulation
├── docs/
│   ├── ARCHITECTURE_FULL.md       ← هذا الملف ★ NEW
│   └── ...
├── tests/test_suite.py
└── examples/
```

---

## 6. طبقات الأسمبلي (Assembly Modules Summary)

| الملف | الوظيفة | التعليمات الرئيسية |
|---|---|---|
| `isr_vectors.s` | Vector Table — جدول المقاطعات | `.word` entries |
| `boot.s` | Real Bootloader | `ldm/stm`, `dsb`, `isb`, `cpsid/ie`, `bl` |
| `context_switch.s` | RTOS Context Switch | `mrs/msr psp`, `stmdb/ldmia {r4-r11}`, `bx lr` |
| `syscall.s` | System Call Gateway | `svc #n`, `ldrb [pc-2]`, `ldm`, `b` dispatch |
| `math_utils.s` | Math / DSP / FPU | `vsqrt.f32`, `vmul/vmla/vmls`, `smull`, `clz`, `rev` |
| `hal_asm.s` | HAL Primitives | `cpsid/ie`, `dsb/isb/dmb`, `wfi/wfe`, `ldrex/strex` |
| `peripheral_asm.s` | Peripheral Helpers | `ldrex/str periph`, SPI burst pump, ADC poll, GPIO bit-band, µs delay |

---

## 7. دورة حياة المهمة (Task Lifecycle)

```
                  task_create()
                       │
                       ▼
                   [IDLE / READY]
                       │
              scheduler picks task
                       │
                       ▼
                   [RUNNING] ←── SysTick tick
                  /    │    \
                 /     │     \
          sys_yield  blocks  terminates
            │          │         │
            ▼          ▼         ▼
         [READY]   [BLOCKED]  [TERMINATED]
            │          │
            └──wakeup──┘
```

---

## 8. نقاط القوة الحقيقية للنظام

---

## 9. محيطات التحكم الكامل بالروبوت

```
                  ┌─────────────────────────────────────────────┐
                  │            RoboOS MCU (STM32F407)           │
                  │                                             │
  ┌───────────┐   │   ┌──────────────────────────────────────┐  │
  │ IMU / Mag │◄──┼───┤ I2C1 (PB6/PB7) — 400kHz Fast Mode   │  │
  │ MPU-6050  │   │   │  i2c_write_read() → 6-axis data      │  │
  │ HMC5883   │   │   │  asm_delay_us() for bus recovery      │  │
  └───────────┘   │   └──────────────────────────────────────┘  │
                  │                                             │
  ┌───────────┐   │   ┌──────────────────────────────────────┐  │
  │ Flash SPI │◄──┼───┤ SPI1 (PA5/PA6/PA7) — 42MHz Max       │  │
  │ W25Q64    │   │   │  asm_spi1_transfer_burst() — ASM pump │  │
  │ OLED/LCD  │   │   │  spi_transfer_dma() for large frames  │  │
  └───────────┘   │   └──────────────────────────────────────┘  │
                  │                                             │
  ┌───────────┐   │   ┌──────────────────────────────────────┐  │
  │ IR Sensor │◄──┼───┤ ADC1 (PA0..PA5) — 12-bit, Scan mode  │  │
  │ Battery   │   │   │  asm_adc1_read_channel() — ASM poll   │  │
  │ Joystick  │   │   │  adc_read_temperature() — internal    │  │
  └───────────┘   │   └──────────────────────────────────────┘  │
                  │                                             │
  ┌───────────┐   │   ┌──────────────────────────────────────┐  │
  │  Motors   │◄──┼───┤ GPIO + PWM — asm_gpio_bit_write()    │  │
  │  LEDs     │   │   │  Bit-Band atomic GPIO toggle          │  │
  │  Relays   │   │   │  gpio.c + timer.c for PWM             │  │
  └───────────┘   │   └──────────────────────────────────────┘  │
                  │                                             │
  ┌───────────┐   │   ┌──────────────────────────────────────┐  │
  │ PC/Debug  │◄──┼───┤ UART1 (PA9/PA10) — 115200 baud       │  │
  │ Bluetooth │   │   │  uart.c + DMA for logging             │  │
  └───────────┘   │   └──────────────────────────────────────┘  │
                  │                                             │
                  └─────────────────────────────────────────────┘
```

### Peripheral ASM Speedups

| الدالة | بدلاً عن | الكسب |
|---|---|---|  
| `asm_spi1_transfer_burst()` | C loop مع function calls | لا overhead — نبض مباشر |
| `asm_adc1_read_channel()` | C while loop + function call | أقل تعليمات في الانتظار |
| `asm_gpio_bit_write()` | Read-Modify-Write | ذري بالكامل (Bit-Band) |
| `asm_delay_us()` | HAL_Delay (SysTick) | دقيق لأقل من 1ms |
| `asm_memcpy32()` | memcpy() | 4 بايت في كل دورة |

---

| المجال | التقنية | الكسب |
|---|---|---|
| **Math** | FPU Hardware `vsqrt`, `vmul`, `vmla` | ~10× أسرع من Software |
| **RTOS Core** | PendSV Context Switch بالأسمبلي | أقل جدول للتبديل ممكن |
| **Syscalls** | SVC Handler مع Dispatch Table | API آمنة بين المهام والنواة |
| **Atomics** | `ldrex`/`strex`/CAS | مزامنة بدون تعطيل مقاطعات |
| **Power** | `wfi`/`wfe` في Idle Task | توفير حقيقي للطاقة |
| **Barriers** | `dsb`/`isb`/`dmb` في HAL | صحة الترتيب مع الهاردوير |
| **Fault** | HardFault naked handler | تشخيص دقيق مع Stack Frame |
