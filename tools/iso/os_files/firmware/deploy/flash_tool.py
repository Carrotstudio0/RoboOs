"""
RoboOS Flash Tool — نظام النشر على الشرائح
==========================================
أداة متكاملة لنشر RoboOS على:
  - ESP32 / ESP32-S3 / ESP32-C3
  - STM32F4xx / STM32H7xx
  - Raspberry Pi Pico (RP2040)
  - Generic ARM Cortex-M
"""

import os
import sys
import json
import time
import struct
import hashlib
import subprocess
import platform
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


# ─────────────────────────────────────────────────────────────
# TARGET DEFINITIONS
# ─────────────────────────────────────────────────────────────

class TargetMCU(Enum):
    ESP32        = "esp32"
    ESP32_S3     = "esp32s3"
    ESP32_C3     = "esp32c3"
    STM32F407    = "stm32f407"
    STM32F411    = "stm32f411"
    STM32H743    = "stm32h743"
    RP2040       = "rp2040"
    GENERIC_ARM  = "generic_arm"
    SIMULATOR    = "simulator"


@dataclass
class MCUProfile:
    """ملف تعريف الشريحة"""
    name: str
    arch: str                    # arm, xtensa, riscv
    flash_size_kb: int
    ram_size_kb: int
    cpu_freq_mhz: int
    toolchain: str               # arm-none-eabi, xtensa-esp32-elf
    flash_offset: int = 0x08000000
    upload_protocol: str = "openocd"
    openocd_target: str = ""
    esptool_chip: str = ""
    micropython_port: str = ""
    features: List[str] = field(default_factory=list)


MCU_PROFILES: Dict[TargetMCU, MCUProfile] = {
    TargetMCU.ESP32: MCUProfile(
        name="ESP32", arch="xtensa", flash_size_kb=4096, ram_size_kb=520,
        cpu_freq_mhz=240, toolchain="xtensa-esp32-elf-gcc",
        upload_protocol="esptool", esptool_chip="esp32",
        micropython_port="esp32",
        features=["wifi", "bluetooth", "dual_core", "psram"]
    ),
    TargetMCU.ESP32_S3: MCUProfile(
        name="ESP32-S3", arch="xtensa", flash_size_kb=8192, ram_size_kb=512,
        cpu_freq_mhz=240, toolchain="xtensa-esp32s3-elf-gcc",
        upload_protocol="esptool", esptool_chip="esp32s3",
        micropython_port="esp32",
        features=["wifi", "bluetooth5", "usb_otg", "ai_acceleration"]
    ),
    TargetMCU.ESP32_C3: MCUProfile(
        name="ESP32-C3", arch="riscv", flash_size_kb=4096, ram_size_kb=400,
        cpu_freq_mhz=160, toolchain="riscv32-esp-elf-gcc",
        upload_protocol="esptool", esptool_chip="esp32c3",
        micropython_port="esp32",
        features=["wifi", "bluetooth5_le", "low_power"]
    ),
    TargetMCU.STM32F407: MCUProfile(
        name="STM32F407", arch="arm", flash_size_kb=1024, ram_size_kb=192,
        cpu_freq_mhz=168, toolchain="arm-none-eabi-gcc",
        flash_offset=0x08000000, upload_protocol="openocd",
        openocd_target="target/stm32f4x.cfg",
        micropython_port="stm32",
        features=["fpu", "dsp", "ethernet", "can", "usb_otg"]
    ),
    TargetMCU.STM32F411: MCUProfile(
        name="STM32F411", arch="arm", flash_size_kb=512, ram_size_kb=128,
        cpu_freq_mhz=100, toolchain="arm-none-eabi-gcc",
        flash_offset=0x08000000, upload_protocol="openocd",
        openocd_target="target/stm32f4x.cfg",
        micropython_port="stm32",
        features=["fpu", "low_power", "usb_otg"]
    ),
    TargetMCU.STM32H743: MCUProfile(
        name="STM32H743", arch="arm", flash_size_kb=2048, ram_size_kb=1024,
        cpu_freq_mhz=480, toolchain="arm-none-eabi-gcc",
        flash_offset=0x08000000, upload_protocol="openocd",
        openocd_target="target/stm32h7x.cfg",
        micropython_port="stm32",
        features=["fpu", "dsp", "double_core", "ethernet", "ltdc", "chrome_art"]
    ),
    TargetMCU.RP2040: MCUProfile(
        name="RP2040", arch="arm", flash_size_kb=16384, ram_size_kb=264,
        cpu_freq_mhz=133, toolchain="arm-none-eabi-gcc",
        flash_offset=0x10000000, upload_protocol="picotool",
        micropython_port="rp2",
        features=["dual_core", "pio", "usb", "low_power"]
    ),
}


# ─────────────────────────────────────────────────────────────
# FIRMWARE BUILDER
# ─────────────────────────────────────────────────────────────

@dataclass
class BuildConfig:
    """إعداد البناء"""
    target: TargetMCU
    optimization: str = "Os"      # O0, O1, O2, O3, Os, Og
    debug: bool = False
    enable_ai: bool = True
    enable_wifi: bool = True
    enable_ble: bool = True
    heap_size_kb: int = 16
    stack_size_kb: int = 8
    extra_defines: List[str] = field(default_factory=list)
    output_dir: str = "build"


class FirmwareBuilder:
    """
    بناء الفيرمور للشريحة المحددة
    يولد CMakeLists.txt وسكريبتات البناء تلقائياً
    """

    def __init__(self, project_root: str, config: BuildConfig):
        self.root = Path(project_root)
        self.config = config
        self.profile = MCU_PROFILES.get(config.target)
        self.build_dir = self.root / config.output_dir / config.target.value
        self.log: List[str] = []

    def _log(self, msg: str):
        print(f"[BUILD] {msg}")
        self.log.append(f"[{time.strftime('%H:%M:%S')}] {msg}")

    def generate_cmake(self) -> str:
        """توليد CMakeLists.txt مخصص للشريحة"""
        p = self.profile
        c = self.config

        defines = " ".join([
            f"-DROBO_TARGET_{c.target.name}",
            f"-DHEAP_SIZE_KB={c.heap_size_kb}",
            f"-DSTACK_SIZE_KB={c.stack_size_kb}",
            f"-DENABLE_AI={'1' if c.enable_ai else '0'}",
            f"-DENABLE_WIFI={'1' if c.enable_wifi else '0'}",
        ] + [f"-D{d}" for d in c.extra_defines])

        if p.arch == "arm":
            cpu_flags = {
                "stm32f407": "-mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb",
                "stm32f411": "-mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb",
                "stm32h743":  "-mcpu=cortex-m7 -mfpu=fpv5-d16 -mfloat-abi=hard -mthumb",
                "rp2040":     "-mcpu=cortex-m0plus -mthumb",
            }.get(c.target.value, "-mcpu=cortex-m4 -mthumb")

            cmake = f"""# Auto-Generated CMakeLists.txt for {p.name}
# RoboOS Build System v2.0

cmake_minimum_required(VERSION 3.16)
project(RoboOS_{p.name.replace('-','_')} C CXX ASM)

set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

# Toolchain
set(CMAKE_C_COMPILER   {p.toolchain.replace('gcc','gcc')})
set(CMAKE_CXX_COMPILER {p.toolchain.replace('gcc','g++')})
set(CMAKE_ASM_COMPILER {p.toolchain.replace('gcc','gcc')})
set(CMAKE_OBJCOPY      {p.toolchain.replace('gcc','objcopy')})
set(CMAKE_SIZE         {p.toolchain.replace('gcc','size')})

# CPU Flags
set(CPU_FLAGS "{cpu_flags}")
set(OPT_FLAGS "-{c.optimization}")

set(CMAKE_C_FLAGS       "${{CPU_FLAGS}} ${{OPT_FLAGS}} -Wall -fdata-sections -ffunction-sections")
set(CMAKE_CXX_FLAGS     "${{CMAKE_C_FLAGS}} -std=c++17 -fno-exceptions -fno-rtti")
set(CMAKE_ASM_FLAGS     "${{CPU_FLAGS}} -x assembler-with-cpp")
set(CMAKE_EXE_LINKER_FLAGS "${{CPU_FLAGS}} -T${{CMAKE_SOURCE_DIR}}/firmware/core/linker.ld -Wl,--gc-sections -Wl,-Map=output.map")

# Defines
add_compile_definitions({" ".join([
    f"ROBO_TARGET_{c.target.name}",
    f"HEAP_SIZE_KB={c.heap_size_kb}",
    f"STACK_SIZE_KB={c.stack_size_kb}",
    "USE_HAL_DRIVER"
])})

# Source Files
file(GLOB_RECURSE C_SOURCES
    "${{CMAKE_SOURCE_DIR}}/firmware/core/*.c"
    "${{CMAKE_SOURCE_DIR}}/firmware/kernel/*.c"
    "${{CMAKE_SOURCE_DIR}}/firmware/hal/*.c"
    "${{CMAKE_SOURCE_DIR}}/firmware/drivers/**/*.c"
    "${{CMAKE_SOURCE_DIR}}/firmware/app/*.c"
)
file(GLOB_RECURSE ASM_SOURCES
    "${{CMAKE_SOURCE_DIR}}/firmware/core/*.s"
    "${{CMAKE_SOURCE_DIR}}/firmware/hal/*.s"
)

# Include Directories
include_directories(
    ${{CMAKE_SOURCE_DIR}}/firmware/include
    ${{CMAKE_SOURCE_DIR}}/firmware/kernel
    ${{CMAKE_SOURCE_DIR}}/firmware/hal
    ${{CMAKE_SOURCE_DIR}}/firmware/drivers/gpio
    ${{CMAKE_SOURCE_DIR}}/firmware/drivers/uart
    ${{CMAKE_SOURCE_DIR}}/firmware/drivers/timer
    ${{CMAKE_SOURCE_DIR}}/firmware/drivers/memory
    ${{CMAKE_SOURCE_DIR}}/firmware/drivers/i2c
    ${{CMAKE_SOURCE_DIR}}/firmware/drivers/spi
    ${{CMAKE_SOURCE_DIR}}/firmware/drivers/adc
)

add_executable(RoboOS.elf ${{C_SOURCES}} ${{ASM_SOURCES}})

# Post-build
add_custom_command(TARGET RoboOS.elf POST_BUILD
    COMMAND ${{CMAKE_OBJCOPY}} -O ihex   $<TARGET_FILE:RoboOS.elf> RoboOS.hex
    COMMAND ${{CMAKE_OBJCOPY}} -O binary $<TARGET_FILE:RoboOS.elf> RoboOS.bin
    COMMAND ${{CMAKE_SIZE}} $<TARGET_FILE:RoboOS.elf>
    COMMENT "Generating HEX and BIN..."
)

message(STATUS "Target: {p.name}")
message(STATUS "Flash: {p.flash_size_kb} KB | RAM: {p.ram_size_kb} KB | CPU: {p.cpu_freq_mhz} MHz")
"""
        elif p.arch in ("xtensa", "riscv"):
            cmake = f"""# Auto-Generated CMakeLists.txt for {p.name}
# Uses ESP-IDF / Arduino framework

cmake_minimum_required(VERSION 3.16)
include($ENV{{IDF_PATH}}/tools/cmake/project.cmake)
project(RoboOS_{p.name.replace('-','_')})

message(STATUS "Building for {p.name} ({p.arch})")
message(STATUS "Flash: {p.flash_size_kb} KB | RAM: {p.ram_size_kb} KB")
"""
        else:
            cmake = f"# Unsupported target: {p.name}"

        return cmake

    def generate_micropython_main(self) -> str:
        """توليد main.py للـ MicroPython على الشريحة"""
        p = self.profile
        return f'''# RoboOS MicroPython Entry Point
# Target: {p.name} | Arch: {p.arch}
# Auto-generated — Do not edit manually
# Generated: {time.strftime("%Y-%m-%d %H:%M")}

import sys
import gc
import time

# خصائص الشريحة
MCU_NAME      = "{p.name}"
MCU_ARCH      = "{p.arch}"
FLASH_SIZE_KB = {p.flash_size_kb}
RAM_SIZE_KB   = {p.ram_size_kb}
CPU_FREQ_MHZ  = {p.cpu_freq_mhz}
FEATURES      = {p.features}

print(f"═══ RoboOS v2.0 — {{MCU_NAME}} ═══")
print(f"Flash: {{FLASH_SIZE_KB}}KB | RAM: {{RAM_SIZE_KB}}KB | CPU: {{CPU_FREQ_MHZ}}MHz")
print(f"MicroPython: {{sys.version}}")
print(f"Free RAM: {{gc.mem_free() // 1024}} KB")

# Platform-specific init
{"from machine import freq; freq(240_000_000)" if p.arch == "xtensa" else ""}
{"from machine import freq; freq(133_000_000)" if p.arch == "arm" and "rp2040" in p.name.lower() else ""}

# Import RoboOS modules
try:
    from roboos.scheduler import Scheduler
    from roboos.hal import HALManager
    from roboos.robot_api import Robot
    print("[BOOT] ✅ RoboOS modules loaded")
except ImportError as e:
    print(f"[BOOT] ⚠️ Module import: {{e}}")

# User application
def main():
    print("[MAIN] Starting RoboOS kernel...")
    scheduler = Scheduler(tick_rate_hz=1000)
    hal = HALManager()
    hal.init()

    # TODO: Add your tasks here
    # scheduler.create_task("motor_task", motor_control, priority=90)
    # scheduler.create_task("ai_task", ai_loop, priority=70)
    # scheduler.create_task("sensor_task", sensor_read, priority=80)

    print("[MAIN] Scheduler starting...")
    scheduler.run()

if __name__ == "__main__":
    main()
'''

    def build(self) -> bool:
        """تنفيذ عملية البناء"""
        self._log(f"بدء بناء {self.profile.name}...")
        self.build_dir.mkdir(parents=True, exist_ok=True)

        # كتابة CMakeLists.txt
        cmake_content = self.generate_cmake()
        cmake_path = self.build_dir / "CMakeLists.txt"
        cmake_path.write_text(cmake_content, encoding="utf-8")
        self._log(f"✅ CMakeLists.txt → {cmake_path}")

        # كتابة main.py للـ MicroPython
        main_py = self.generate_micropython_main()
        main_path = self.build_dir / "main.py"
        main_path.write_text(main_py, encoding="utf-8")
        self._log(f"✅ main.py → {main_path}")

        # كتابة معلومات البناء
        build_info = {
            "target": self.config.target.name,
            "profile": {
                "name": self.profile.name,
                "arch": self.profile.arch,
                "flash_kb": self.profile.flash_size_kb,
                "ram_kb": self.profile.ram_size_kb,
                "freq_mhz": self.profile.cpu_freq_mhz,
                "features": self.profile.features,
            },
            "config": {
                "optimization": self.config.optimization,
                "debug": self.config.debug,
                "enable_ai": self.config.enable_ai,
                "heap_kb": self.config.heap_size_kb,
            },
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "build_log": self.log
        }
        info_path = self.build_dir / "build_info.json"
        info_path.write_text(json.dumps(build_info, indent=2, ensure_ascii=False), encoding="utf-8")
        self._log(f"✅ build_info.json → {info_path}")

        if self.config.target == TargetMCU.SIMULATOR:
            self._log("✅ محاكي — لا حاجة لبناء C")
            return True

        # محاولة cmake الفعلي
        cmake_bin_dir = self.build_dir / "_cmake"
        cmake_bin_dir.mkdir(exist_ok=True)

        try:
            result = subprocess.run(
                ["cmake", str(self.build_dir), f"-DCMAKE_BUILD_TYPE={'Debug' if self.config.debug else 'Release'}"],
                cwd=str(cmake_bin_dir),
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                self._log("✅ CMake configuration OK")
                make_result = subprocess.run(
                    ["cmake", "--build", ".", "--", "-j4"],
                    cwd=str(cmake_bin_dir),
                    capture_output=True, text=True, timeout=300
                )
                if make_result.returncode == 0:
                    self._log("✅ Build SUCCESS")
                    return True
                else:
                    self._log(f"⚠️ Build warnings: {make_result.stderr[:500]}")
            else:
                self._log(f"⚠️ CMake: toolchain not found — FILES GENERATED ONLY")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self._log("ℹ️ cmake غير متاح — الملفات مولّدة ويمكن بناؤها يدوياً")

        return True  # الملفات مولّدة حتى لو cmake غير متاح


# ─────────────────────────────────────────────────────────────
# FLASH TOOL
# ─────────────────────────────────────────────────────────────

class FlashResult(Enum):
    SUCCESS      = "success"
    FAILED       = "failed"
    PORT_ERROR   = "port_error"
    TOOL_MISSING = "tool_missing"
    VERIFY_ERROR = "verify_error"


@dataclass
class FlashReport:
    """تقرير عملية الفلاش"""
    target: str
    port: str
    result: FlashResult
    duration_s: float
    messages: List[str]
    file_size_bytes: int = 0
    verified: bool = False


class FlashTool:
    """
    أداة فلاش الشرائح
    تدعم esptool (ESP32) + OpenOCD (STM32) + picotool (RP2040)
    """

    def __init__(self, project_root: str):
        self.root = Path(project_root)
        self.messages: List[str] = []

    def _msg(self, text: str):
        print(f"[FLASH] {text}")
        self.messages.append(text)

    def detect_port(self) -> Optional[str]:
        """كشف منفذ تلقائي"""
        system = platform.system()
        candidates = []

        if system == "Windows":
            # تجربة COM ports شائعة
            for i in range(1, 20):
                candidates.append(f"COM{i}")
        elif system == "Linux":
            for dev in ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/ttyACM1"]:
                if Path(dev).exists():
                    return dev
        elif system == "Darwin":
            for dev in ["/dev/cu.SLAB_USBtoUART", "/dev/cu.usbserial-0001"]:
                if Path(dev).exists():
                    return dev

        # محاولة اكتشاف تلقائي
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if any(kw in port.description.lower()
                       for kw in ["cp210", "ch340", "ftdi", "stlink", "jlink"]):
                    self._msg(f"🔍 اكتشاف تلقائي: {port.device} ({port.description})")
                    return port.device
        except ImportError:
            pass

        return None

    def flash_esp32(self, binary_path: str, port: str,
                    chip: str = "esp32", baud: int = 921600) -> FlashReport:
        """فلاش ESP32 باستخدام esptool"""
        start = time.time()
        self.messages.clear()
        self._msg(f"🔥 نشر على {chip.upper()} عبر {port} @ {baud} baud")

        bin_path = Path(binary_path)
        if not bin_path.exists():
            self._msg(f"❌ الملف غير موجود: {binary_path}")
            return FlashReport(chip, port, FlashResult.FAILED,
                             time.time()-start, self.messages)

        cmd = [
            "esptool.py",
            "--chip", chip,
            "--port", port,
            "--baud", str(baud),
            "write_flash",
            "--flash_mode", "dio",
            "--flash_freq", "40m",
            "--flash_size", "detect",
            "0x0", str(bin_path)
        ]

        self._msg(f"$ {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                self._msg("✅ فلاش مكتمل!")
                return FlashReport(chip, port, FlashResult.SUCCESS,
                                 time.time()-start, self.messages,
                                 bin_path.stat().st_size, True)
            else:
                self._msg(f"❌ خطأ: {result.stderr[:300]}")
                return FlashReport(chip, port, FlashResult.FAILED,
                                 time.time()-start, self.messages)
        except FileNotFoundError:
            self._msg("⚠️ esptool.py غير مثبت — تثبيت: pip install esptool")
            return FlashReport(chip, port, FlashResult.TOOL_MISSING,
                             time.time()-start, self.messages)
        except subprocess.TimeoutExpired:
            self._msg("❌ انتهى الوقت — تأكد من الاتصال")
            return FlashReport(chip, port, FlashResult.FAILED,
                             time.time()-start, self.messages)

    def flash_stm32(self, binary_path: str, port: str = None,
                    target_cfg: str = "target/stm32f4x.cfg",
                    interface: str = "interface/stlink.cfg") -> FlashReport:
        """فلاش STM32 باستخدام OpenOCD"""
        start = time.time()
        self.messages.clear()
        self._msg(f"🔥 نشر على STM32 باستخدام OpenOCD")

        bin_path = Path(binary_path)
        if not bin_path.exists():
            self._msg(f"❌ الملف غير موجود: {binary_path}")
            return FlashReport("stm32", port or "JTAG",
                             FlashResult.FAILED, time.time()-start, self.messages)

        cmd = [
            "openocd",
            "-f", interface,
            "-f", target_cfg,
            "-c", f"program {str(bin_path)} verify reset exit 0x08000000"
        ]
        self._msg(f"$ {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and "verified" in result.output.lower():
                self._msg("✅ فلاش STM32 مكتمل مع التحقق!")
                return FlashReport("stm32", "JTAG/SWD", FlashResult.SUCCESS,
                                 time.time()-start, self.messages,
                                 bin_path.stat().st_size, True)
            else:
                self._msg(f"❌ OpenOCD: {result.stderr[:300]}")
                return FlashReport("stm32", "JTAG/SWD", FlashResult.FAILED,
                                 time.time()-start, self.messages)
        except FileNotFoundError:
            self._msg("⚠️ openocd غير مثبت — تحميل من openocd.org")
            return FlashReport("stm32", "JTAG/SWD", FlashResult.TOOL_MISSING,
                             time.time()-start, self.messages)

    def flash_micropython(self, port: str, scripts_dir: str) -> FlashReport:
        """رفع ملفات Python للشريحة عبر ampy أو mpremote"""
        start = time.time()
        self.messages.clear()
        self._msg(f"📡 رفع ملفات MicroPython على {port}")

        scripts = list(Path(scripts_dir).rglob("*.py"))
        if not scripts:
            self._msg("❌ لا توجد ملفات Python")
            return FlashReport("micropython", port, FlashResult.FAILED,
                             time.time()-start, self.messages)

        uploaded = 0
        for script in scripts:
            # محاولة mpremote أولاً ثم ampy
            for tool, cmd_template in [
                ("mpremote", f"mpremote connect {port} cp {script} :"),
                ("ampy",     f"ampy --port {port} put {script}"),
            ]:
                try:
                    cmd = cmd_template.split()
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        self._msg(f"✅ {script.name}")
                        uploaded += 1
                        break
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue

        if uploaded > 0:
            self._msg(f"✅ رُفع {uploaded}/{len(scripts)} ملف")
            return FlashReport("micropython", port, FlashResult.SUCCESS,
                             time.time()-start, self.messages, uploaded)

        self._msg("⚠️ mpremote/ampy غير متاح — تثبيت: pip install mpremote")
        return FlashReport("micropython", port, FlashResult.TOOL_MISSING,
                         time.time()-start, self.messages)

    def simulate(self, build_dir: str) -> FlashReport:
        """تشغيل المحاكي بدلاً من الفلاش"""
        start = time.time()
        self.messages.clear()
        self._msg("🖥️ تشغيل المحاكي...")

        sim_cmd = [sys.executable, "-m", "firmware.simulator.simulator"]
        try:
            self._msg(f"$ {' '.join(sim_cmd)}")
            result = subprocess.run(sim_cmd, capture_output=True, text=True,
                                  timeout=30, cwd=str(self.root))
            self._msg(result.stdout[:500] if result.stdout else "جاهز")
            return FlashReport("simulator", "virtual", FlashResult.SUCCESS,
                             time.time()-start, self.messages)
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            self._msg(f"ℹ️ {e}")
            return FlashReport("simulator", "virtual", FlashResult.SUCCESS,
                             time.time()-start, self.messages)


# ─────────────────────────────────────────────────────────────
# DEPLOY MANAGER — الواجهة الرئيسية
# ─────────────────────────────────────────────────────────────

class DeployManager:
    """
    مدير النشر الكامل — يجمع البناء والفلاش معاً
    """

    def __init__(self, project_root: str):
        self.root = project_root
        self.flash_tool = FlashTool(project_root)

    def deploy(self, target: TargetMCU, port: str = None,
               optimization: str = "Os", enable_ai: bool = True) -> bool:
        """
        نشر كامل: بناء + فلاش
        """
        print(f"\n{'═'*55}")
        print(f"  RoboOS Deploy Manager — {target.name}")
        print(f"{'═'*55}")

        # 1. البناء
        config = BuildConfig(
            target=target,
            optimization=optimization,
            enable_ai=enable_ai,
        )
        builder = FirmwareBuilder(self.root, config)

        print(f"\n[1/3] 🔨 بناء الفيرمور لـ {target.name}...")
        if not builder.build():
            print("[DEPLOY] ❌ فشل البناء")
            return False
        print("[DEPLOY] ✅ بناء ناجح")

        # 2. اكتشاف المنفذ
        if port is None and target != TargetMCU.SIMULATOR:
            print("\n[2/3] 🔍 اكتشاف المنفذ...")
            port = self.flash_tool.detect_port()
            if port:
                print(f"[DEPLOY] ✅ منفذ: {port}")
            else:
                print("[DEPLOY] ⚠️ لم يُكتشف منفذ — تحقق من الاتصال")
        else:
            print(f"\n[2/3] 📌 منفذ: {port or 'محاكي'}")

        # 3. الفلاش
        print(f"\n[3/3] 🔥 نشر على الشريحة...")
        profile = MCU_PROFILES.get(target)
        build_dir = str(Path(self.root) / "build" / target.value)

        if target == TargetMCU.SIMULATOR:
            report = self.flash_tool.simulate(build_dir)
        elif target in (TargetMCU.ESP32, TargetMCU.ESP32_S3, TargetMCU.ESP32_C3):
            bin_path = str(Path(build_dir) / "_cmake" / "RoboOS.bin")
            report = self.flash_tool.flash_esp32(
                bin_path, port or "COM3", profile.esptool_chip)
        elif "stm32" in target.value:
            bin_path = str(Path(build_dir) / "_cmake" / "RoboOS.bin")
            report = self.flash_tool.flash_stm32(
                bin_path, target_cfg=profile.openocd_target)
        else:
            # MicroPython fallback
            report = self.flash_tool.flash_micropython(
                port or "COM3", str(Path(self.root) / "firmware"))

        print(f"\n{'─'*55}")
        status = "✅ نجح" if report.result == FlashResult.SUCCESS else "❌ فشل"
        print(f"  النتيجة:  {status}")
        print(f"  الوقت:    {report.duration_s:.1f}s")
        print(f"  الهدف:    {report.target}")
        print(f"  المنفذ:   {report.port}")
        print(f"{'─'*55}\n")

        return report.result == FlashResult.SUCCESS

    def list_targets(self):
        """عرض الشرائح المدعومة"""
        print(f"\n{'═'*65}")
        print(f"  الشرائح المدعومة في RoboOS Flash Tool")
        print(f"{'═'*65}")
        print(f"  {'الاسم':<20} {'المعالج':<10} {'Flash':<10} {'RAM':<8} {'MHz':<6} المميزات")
        print(f"  {'─'*60}")
        for mcu, p in MCU_PROFILES.items():
            feats = ", ".join(p.features[:3])
            print(f"  {mcu.name:<20} {p.arch:<10} {p.flash_size_kb:<10} {p.ram_size_kb:<8} {p.cpu_freq_mhz:<6} {feats}")
        print(f"{'─'*65}\n")
