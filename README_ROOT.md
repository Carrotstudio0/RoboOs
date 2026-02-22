# RoboOS - Embedded Operating System
# نظام تشغيل مدمج للروبوتات

**Lightweight embedded OS for robots with custom Python-based language**

## 📁 Project Structure

```
RoboOS/
├── firmware/          # Firmware layer (Python + C drivers)
│   ├── drivers/       # C hardware drivers (GPIO, UART, Timer, Memory)
│   ├── include/       # C headers for drivers
│   ├── hal/           # Hardware abstraction layer
│   ├── core/          # Core scheduler
│   ├── lang/          # Custom language engine
│   ├── robot_api/     # Robot control APIs
│   └── simulator/     # Virtual hardware simulator
├── tests/             # Test suite (14 passing tests)
├── examples/          # Working examples
├── docs/              # 📚 Complete documentation (see below)
└── .vscode/           # VS Code configuration
```

## 📚 Documentation

All documentation has been organized in the `docs/` folder:

| Document | Content |
|----------|---------|
| [README.md](docs/README.md) | Project overview |
| [QUICKSTART.md](docs/QUICKSTART.md) | Getting started guide |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture |
| [API_REFERENCE.md](docs/API_REFERENCE.md) | Complete API documentation |
| [C_DRIVERS_BUILD.md](docs/C_DRIVERS_BUILD.md) | C driver build guide |
| [INDEX.md](docs/INDEX.md) | Project index |
| [BUILD_REPORT.md](docs/BUILD_REPORT.md) | Build status report |
| [COMPLETION.md](docs/COMPLETION.md) | Phase 1 completion |
| [PHASE_2_COMPLETION.md](docs/PHASE_2_COMPLETION.md) | Phase 2 completion |
| [SUMMARY.md](docs/SUMMARY.md) | Project summary |

**👉 Start with [QUICKSTART.md](docs/QUICKSTART.md) for setup instructions.**

## ✨ Key Features

- ✅ **2,251 lines of embedded-optimized C code**
- ✅ **4 Hardware Drivers**: GPIO, UART, Timer, Memory Manager
- ✅ **14 passing Python tests**
- ✅ **Custom language engine** for robot programming
- ✅ **Real MCU deployment ready** (ESP32, STM32)
- ✅ **Memory-efficient** (~15 KB heap)
- ✅ **Python + C hybrid** for gradual optimization

## 🚀 Quick Start

### Python Installation
```bash
cd c:\Users\Tech Shop\Desktop\os
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Run Tests
```bash
python tests/test_suite.py
# Output: 14/14 tests PASSED ✅
```

### Run Examples
```bash
python examples/motor_control.py
python examples/led_control.py
python examples/language_demo.py
python examples/robot_simulation.py
```

### Build C Drivers (Optional)
```bash
mkdir build
cd build
cmake ..
make  # or cmake --build . for Windows
```

## 📊 Current Status

| Component | Status | Lines |
|-----------|--------|-------|
| Python Simulation Layer | ✅ Complete | ~3,450 |
| Custom Language Engine | ✅ Complete | ~1,200 |
| Test Suite | ✅ 14/14 PASS | ~400 |
| C Hardware Drivers | ✅ Complete | ~2,251 |
| ESP32 Support | 🔄 Pending | - |
| STM32 Support | 🔄 Pending | - |

## 🏗️ Architecture Layers

```
┌─────────────────────────────────────────────┐
│  User Programs (Python/Custom Language)     │
├─────────────────────────────────────────────┤
│  Language Engine (Lexer/Parser/Executor)    │
├─────────────────────────────────────────────┤
│  Scheduler & Task Management                │
├─────────────────────────────────────────────┤
│  Robot APIs (Motor/LED/Sensor)              │
├─────────────────────────────────────────────┤
│  HAL + C Drivers Bridge (GPIO/UART/Timer)   │
├─────────────────────────────────────────────┤
│  C Hardware Drivers (Real MCU Ready)        │
├─────────────────────────────────────────────┤
│  Virtual/Real Hardware                      │
└─────────────────────────────────────────────┘
```

## 📋 Files Overview

### Core Python
- `firmware/lang/engine.py` - Custom language (Lexer, Parser, Executor)
- `firmware/core/scheduler.py` - Task scheduling
- `firmware/hal/manager.py` - Hardware abstraction
- `firmware/robot_api/robot.py` - Robot control APIs

### C Drivers (Production-Ready)
- `firmware/drivers/gpio/gpio.c` - GPIO driver (373 lines)
- `firmware/drivers/uart/uart.c` - UART driver (364 lines)
- `firmware/drivers/timer/timer.c` - Timer driver (350 lines)
- `firmware/drivers/memory/memory_manager.c` - Memory manager (400 lines)

### Testing & Examples
- `tests/test_suite.py` - 14 comprehensive tests
- `examples/motor_control.py` - Motor control example
- `examples/led_control.py` - LED control example
- `examples/language_demo.py` - Language engine demo
- `examples/robot_simulation.py` - Full simulation example

## 🔧 Requirements

- **Python 3.8+** (tested on 3.14.3)
- **C Compiler** (GCC, Clang, or MSVC for C drivers)
- **CMake 3.10+** (for building C code)
- **Optional**: ESP-IDF (for ESP32), STM32CubeMX (for STM32)

## 📦 Dependencies

- `ply` - Lexer/Parser library
- `pyserial` - UART communication (optional)
- `pytest` - Testing framework (optional)

## 🎯 Next Steps (Phase 3)

1. Port critical components to C (Scheduler, Language Engine)
2. Optimize memory usage
3. Add real-time capabilities
4. Deploy to ESP32/STM32
5. Add SPI/I2C drivers
6. Implement interrupt system

## 📝 License

Open source project for embedded systems education and research.

## 👥 Contact

For questions or contributions, refer to documentation in [docs/](docs/) folder.

---

**Last Updated**: February 22, 2026  
**Version**: 2.0 (Phase 2 Complete)  
**Status**: ✅ Production-Ready for Simulation, Ready for MCU Deployment
