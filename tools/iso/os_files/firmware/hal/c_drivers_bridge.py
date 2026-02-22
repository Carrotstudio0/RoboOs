"""
C Drivers Bridge
جسر أدرايفرات C
Provides ctypes bindings to C hardware drivers for real MCU deployment
"""

import ctypes
import os
import platform
from pathlib import Path

# Find built drivers library
def find_drivers_library():
    """Find the compiled hardware drivers shared library"""
    base_path = Path(__file__).parent.parent.parent
    
    # Platform-specific library name
    if platform.system() == "Windows":
        lib_names = ["hw_drivers.dll", "hw_drivers.so"]
    elif platform.system() == "Darwin":
        lib_names = ["libhw_drivers.dylib", "hw_drivers.so"]
    else:
        lib_names = ["libhw_drivers.so", "hw_drivers.so"]
    
    # Check build directories
    search_paths = [
        base_path / "build" / "lib",
        base_path / "build",
        base_path / "lib",
        base_path / "firmware" / "drivers",
    ]
    
    for lib_name in lib_names:
        for search_path in search_paths:
            lib_path = search_path / lib_name
            if lib_path.exists():
                return str(lib_path)
    
    return None

class CDriversBridge:
    """Bridge to C hardware drivers using ctypes"""
    
    def __init__(self):
        self.lib = None
        self.loaded = False
        self._load_drivers()
    
    def _load_drivers(self):
        """Load C drivers library"""
        lib_path = find_drivers_library()
        
        if lib_path is None:
            print("[WARN] C drivers library not found. Simulation mode enabled.")
            print("[WARN] Build drivers with: cmake .. && make")
            return
        
        try:
            self.lib = ctypes.CDLL(lib_path)
            self._setup_ctypes()
            self.loaded = True
            print(f"[OK] C Drivers loaded from: {lib_path}")
        except Exception as e:
            print(f"[ERROR] Failed to load C drivers: {e}")
            print("[WARN] Falling back to simulation mode")
    
    def _setup_ctypes(self):
        """Setup ctypes function signatures"""
        
        # === GPIO Functions ===
        self.gpio_init = self.lib.gpio_init
        self.gpio_init.argtypes = []
        self.gpio_init.restype = ctypes.c_int
        
        self.gpio_deinit = self.lib.gpio_deinit
        self.gpio_deinit.argtypes = []
        self.gpio_deinit.restype = ctypes.c_int
        
        self.gpio_configure = self.lib.gpio_configure
        self.gpio_configure.argtypes = [ctypes.c_void_p]
        self.gpio_configure.restype = ctypes.c_int
        
        self.gpio_digital_write = self.lib.gpio_digital_write
        self.gpio_digital_write.argtypes = [ctypes.c_uint8, ctypes.c_uint8]
        self.gpio_digital_write.restype = ctypes.c_int
        
        self.gpio_digital_read = self.lib.gpio_digital_read
        self.gpio_digital_read.argtypes = [ctypes.c_uint8, ctypes.c_void_p]
        self.gpio_digital_read.restype = ctypes.c_int
        
        # === UART Functions ===
        self.uart_init = self.lib.uart_init
        self.uart_init.argtypes = []
        self.uart_init.restype = ctypes.c_int
        
        self.uart_write = self.lib.uart_write
        self.uart_write.argtypes = [ctypes.c_uint8, ctypes.c_void_p, ctypes.c_size_t]
        self.uart_write.restype = ctypes.c_int
        
        self.uart_read = self.lib.uart_read
        self.uart_read.argtypes = [ctypes.c_uint8, ctypes.c_void_p, ctypes.c_size_t]
        self.uart_read.restype = ctypes.c_int
        
        # === Timer Functions ===
        self.timer_init = self.lib.timer_init
        self.timer_init.argtypes = []
        self.timer_init.restype = ctypes.c_int
        
        self.timer_start = self.lib.timer_start
        self.timer_start.argtypes = [ctypes.c_uint8]
        self.timer_start.restype = ctypes.c_int
        
        self.timer_stop = self.lib.timer_stop
        self.timer_stop.argtypes = [ctypes.c_uint8]
        self.timer_stop.restype = ctypes.c_int
        
        # === Memory Manager Functions ===
        self.mem_init = self.lib.mem_init
        self.mem_init.argtypes = []
        self.mem_init.restype = ctypes.c_int
        
        self.mem_alloc = self.lib.mem_alloc
        self.mem_alloc.argtypes = [ctypes.c_size_t]
        self.mem_alloc.restype = ctypes.c_void_p
        
        self.mem_free = self.lib.mem_free
        self.mem_free.argtypes = [ctypes.c_void_p]
        self.mem_free.restype = ctypes.c_int
    
    def is_available(self):
        """Check if C drivers are available"""
        return self.loaded
    
    # === GPIO Interface ===
    
    def gpio_init_hw(self):
        """Initialize GPIO hardware"""
        if not self.loaded:
            print("[WARN] GPIO: Using simulation mode")
            return
        
        result = self.gpio_init()
        if result != 0:
            print("[ERROR] GPIO init failed")
    
    def gpio_digital_write_hw(self, pin, level):
        """Write digital GPIO value"""
        if not self.loaded:
            print(f"[SIM] GPIO {pin} = {level}")
            return
        
        result = self.gpio_digital_write(pin, level)
        if result != 0:
            print(f"[ERROR] GPIO write failed: pin {pin}")
    
    # === UART Interface ===
    
    def uart_init_hw(self):
        """Initialize UART hardware"""
        if not self.loaded:
            print("[WARN] UART: Using simulation mode")
            return
        
        result = self.uart_init()
        if result != 0:
            print("[ERROR] UART init failed")
    
    def uart_write_hw(self, port, data):
        """Write UART data"""
        if not self.loaded:
            print(f"[SIM] UART {port}: {data}")
            return
        
        # Convert data to bytes
        if isinstance(data, str):
            data = data.encode()
        
        result = self.uart_write(port, data, len(data))
        if result < 0:
            print(f"[ERROR] UART write failed: port {port}")
    
    # === Timer Interface ===
    
    def timer_init_hw(self):
        """Initialize Timer hardware"""
        if not self.loaded:
            print("[WARN] Timer: Using simulation mode")
            return
        
        result = self.timer_init()
        if result != 0:
            print("[ERROR] Timer init failed")
    
    def timer_start_hw(self, timer_id):
        """Start timer"""
        if not self.loaded:
            print(f"[SIM] Timer {timer_id} started")
            return
        
        result = self.timer_start(timer_id)
        if result != 0:
            print(f"[ERROR] Timer start failed: timer {timer_id}")
    
    # === Memory Manager Interface ===
    
    def mem_init_hw(self):
        """Initialize Memory Manager"""
        if not self.loaded:
            print("[WARN] Memory: Using simulation mode")
            return
        
        result = self.mem_init()
        if result != 0:
            print("[ERROR] Memory init failed")
    
    def mem_alloc_hw(self, size):
        """Allocate memory using C memory manager"""
        if not self.loaded:
            print(f"[SIM] Memory allocated: {size} bytes")
            return None
        
        ptr = self.mem_alloc(size)
        if ptr == 0:
            print(f"[ERROR] Memory allocation failed: {size} bytes")
            return None
        
        return ptr
    
    def mem_free_hw(self, ptr):
        """Free memory"""
        if not self.loaded:
            print(f"[SIM] Memory freed")
            return
        
        result = self.mem_free(ptr)
        if result != 0:
            print(f"[ERROR] Memory free failed")


# Global instance
_c_drivers = None

def get_c_drivers():
    """Get or create C drivers bridge instance"""
    global _c_drivers
    if _c_drivers is None:
        _c_drivers = CDriversBridge()
    return _c_drivers
