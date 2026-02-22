cmake_minimum_required(VERSION 3.16)
project(RoboOS C ASM)

# ==============================================================================
# ARM Cortex-M4 Toolchain
# ==============================================================================

set(CMAKE_C_STANDARD 11)
set(CMAKE_SYSTEM_NAME    Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)
enable_language(C ASM)

set(CPU_FLAGS  "-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard")
set(WARN_FLAGS "-Wall -Wextra -Wshadow -Wdouble-promotion -Wundef")
set(OPT_FLAGS  "-O2 -ffunction-sections -fdata-sections -fno-common")
set(DBG_FLAGS  "-g3 -gdwarf-4")

set(CMAKE_C_FLAGS   "${CPU_FLAGS} ${WARN_FLAGS} ${OPT_FLAGS} ${DBG_FLAGS}")
set(CMAKE_ASM_FLAGS "${CPU_FLAGS} -g3")

set(LINKER_SCRIPT "${CMAKE_SOURCE_DIR}/firmware/core/linker.ld")
set(LINK_FLAGS
    "${CPU_FLAGS} \
    -T${LINKER_SCRIPT} \
    -Wl,--gc-sections \
    -Wl,-Map=${CMAKE_BINARY_DIR}/roboos.map \
    -Wl,--print-memory-usage \
    -nostdlib --specs=nano.specs --specs=nosys.specs"
)
set(CMAKE_EXE_LINKER_FLAGS "${LINK_FLAGS}")

# Global Include Paths
include_directories(
    firmware/include
    firmware/kernel
    firmware/core
    firmware/hal
    firmware/app
    firmware/drivers/gpio
    firmware/drivers/uart
    firmware/drivers/timer
    firmware/drivers/memory
    firmware/drivers/i2c
    firmware/drivers/spi
    firmware/drivers/adc
)

# ==============================================================================
# [1] Assembly Core — قلب النظام بالأسمبلي
# ==============================================================================
add_library(asm_core STATIC
    firmware/core/isr_vectors.s          # Vector Table الكامل
    firmware/core/boot.s                 # Real Bootloader
    firmware/core/context_switch.s       # RTOS Context Switch (PendSV)
    firmware/core/syscall.s              # SVC Syscall Gateway
    firmware/core/math_utils.s           # FPU/DSP Math Suite
    firmware/hal/hal_asm.s               # HAL Primitives (IRQ, WFI, Atomic)
    firmware/hal/peripheral_asm.s        # Peripheral Helpers (SPI pump, ADC poll)
)

# ==============================================================================
# [2] RTOS Kernel
# ==============================================================================
add_library(kernel STATIC
    firmware/kernel/irq.c                # NVIC + SysTick + HardFault
    firmware/kernel/scheduler.c          # TCB + Priority Scheduler + Mutex + Sem
)
target_include_directories(kernel PUBLIC firmware/kernel)

# ==============================================================================
# [3] Hardware Drivers
# ==============================================================================
add_library(hw_drivers STATIC
    firmware/drivers/gpio/gpio.c
    firmware/drivers/uart/uart.c
    firmware/drivers/timer/timer.c
    firmware/drivers/memory/memory_manager.c
    firmware/drivers/i2c/i2c.c           # I2C Driver
    firmware/drivers/spi/spi.c           # SPI Driver
    firmware/drivers/adc/adc.c           # ADC Driver
)

# ==============================================================================
# [4] Application Tasks
# ==============================================================================
add_library(app_tasks STATIC
    firmware/app/led_task.c              # LED Heartbeat
    firmware/app/sensor_task.c           # MPU-6050 IMU @ 100Hz
    firmware/app/motor_task.c            # PWM Motor Control + PID
    firmware/app/comm_task.c             # UART Telemetry Logging
)
target_include_directories(app_tasks PUBLIC firmware/app firmware/kernel firmware/drivers/i2c)

# ==============================================================================
# [5] Main Firmware ELF — Proof of Concept
# ==============================================================================
add_executable(roboos.elf
    firmware/app/main.c                  # SystemInit + task_create + scheduler_start
)
target_link_libraries(roboos.elf
    app_tasks       # LED + Sensor + Motor + Comm tasks
    kernel          # RTOS: Scheduler + IRQ + SysTick
    hw_drivers      # GPIO + UART + I2C + SPI + ADC + Timer + Memory
    asm_core        # Assembly: Boot + ISR + CtxSwitch + SVC + Math + HAL
)

# ==============================================================================
# [6] Unit Test ELF — يُبنى منفصلاً
# ==============================================================================
add_executable(roboos_tests.elf
    firmware/tests/unit_test.c
)
# Test entry: linker يستدعي main_test بدلاً من main
target_link_options(roboos_tests.elf PRIVATE "-Wl,--defsym=main=main_test")
target_link_libraries(roboos_tests.elf
    kernel
    hw_drivers
    asm_core
)

# ==============================================================================
# [7] Post-Build Artifacts لكلا الـ ELF
# ==============================================================================
foreach(TARGET roboos.elf roboos_tests.elf)
    get_filename_component(TNAME ${TARGET} NAME_WE)

    add_custom_command(TARGET ${TARGET} POST_BUILD
        COMMAND arm-none-eabi-objcopy -O ihex   ${TARGET} ${CMAKE_BINARY_DIR}/${TNAME}.hex
        COMMAND arm-none-eabi-objcopy -O binary ${TARGET} ${CMAKE_BINARY_DIR}/${TNAME}.bin
        COMMAND arm-none-eabi-size --format=SysV ${TARGET}
        COMMAND arm-none-eabi-objdump -d -S ${TARGET} > ${CMAKE_BINARY_DIR}/${TNAME}.lst
        COMMENT "[RoboOS] Built: ${TNAME}.hex / .bin / .lst"
    )
endforeach()

# ==============================================================================
# [8] CTest Integration
# ==============================================================================
enable_testing()

# Python Simulation Test (بدون MCU)
add_test(NAME python_sim
    COMMAND python ${CMAKE_SOURCE_DIR}/main.py
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
)

# ==============================================================================
# Build Summary
# ==============================================================================
message(STATUS "")
message(STATUS "╔══════════════════════════════════════════════════════╗")
message(STATUS "║          RoboOS — Full Build Configuration          ║")
message(STATUS "╠══════════════════════════════════════════════════════╣")
message(STATUS "║  Target : ARM Cortex-M4 + FPU (fpv4-sp-d16)         ║")
message(STATUS "║  CPU    : STM32F407 @ 168 MHz (HSE+PLL)             ║")
message(STATUS "║  Flash  : 512KB @ 0x08000000                         ║")
message(STATUS "║  SRAM   : 128KB @ 0x20000000                         ║")
message(STATUS "╠══════════════════════════════════════════════════════╣")
message(STATUS "║  Assembly (asm_core):                                ║")
message(STATUS "║    ✓ isr_vectors.s    — Full Cortex-M4 Vector Table  ║")
message(STATUS "║    ✓ boot.s           — Real Bootloader (FPU+PLL)    ║")
message(STATUS "║    ✓ context_switch.s — PendSV RTOS Context Switch   ║")
message(STATUS "║    ✓ syscall.s        — SVC Dispatcher (6 Syscalls)  ║")
message(STATUS "║    ✓ math_utils.s     — FPU/DSP/SIMD Math (9 funcs) ║")
message(STATUS "║    ✓ hal_asm.s        — IRQ/Barriers/Atomics/Power   ║")
message(STATUS "║    ✓ peripheral_asm.s — SPI Burst/ADC Poll/BitBand   ║")
message(STATUS "╠══════════════════════════════════════════════════════╣")
message(STATUS "║  Kernel (kernel):                                    ║")
message(STATUS "║    ✓ irq.c            — NVIC + SysTick + HardFault   ║")
message(STATUS "║    ✓ scheduler.c      — TCB + Priorities + Mutex/Sem ║")
message(STATUS "╠══════════════════════════════════════════════════════╣")
message(STATUS "║  Drivers (hw_drivers):                               ║")
message(STATUS "║    ✓ gpio.c / uart.c / timer.c / memory_manager.c   ║")
message(STATUS "║    ✓ i2c.c  — I2C Master (400kHz, Bus Recovery)     ║")
message(STATUS "║    ✓ spi.c  — SPI Full-Duplex + DMA stubs           ║")
message(STATUS "║    ✓ adc.c  — ADC 12-bit + Temp + VBAT + Watchdog   ║")
message(STATUS "╠══════════════════════════════════════════════════════╣")
message(STATUS "║  Application (app_tasks):                            ║")
message(STATUS "║    ✓ led_task.c   — Heartbeat + Stack Overflow Watch ║")
message(STATUS "║    ✓ sensor_task.c— MPU-6050 100Hz + Mutex protect  ║")
message(STATUS "║    ✓ motor_task.c — TIM4 PWM + ASM PID @ 50Hz       ║")
message(STATUS "║    ✓ comm_task.c  — UART Telemetry 1Hz (no printf)  ║")
message(STATUS "╠══════════════════════════════════════════════════════╣")
message(STATUS "║  Outputs:                                            ║")
message(STATUS "║    roboos.elf / .hex / .bin / .lst / .map           ║")
message(STATUS "║    roboos_tests.elf / .hex / .bin / .lst            ║")
message(STATUS "╚══════════════════════════════════════════════════════╝")
message(STATUS "")
message(STATUS "  Build:  cmake -B build && cmake --build build")
message(STATUS "  Flash:  st-flash write build/roboos.bin 0x08000000")
message(STATUS "  Test:   cmake --build build --target roboos_tests.elf")
message(STATUS "          st-flash write build/roboos_tests.bin 0x08000000")
message(STATUS "")
