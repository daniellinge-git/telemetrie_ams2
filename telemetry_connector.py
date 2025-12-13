import mmap
import ctypes
import time
from ams2_structs import SharedMemory

class AMS2Connector:
    """
    Data Layer for AMS2 Race Engineer.
    Handles low-level connection to Shared Memory '$pcars2$'.
    """
    def __init__(self):
        self.map_name = "$pcars2$"
        self.shared_memory = None
        self.map_file = None
        self.connected = False
        self.last_error = None
        
        self.connect()

    def connect(self):
        """Attempts to connect to the memory map."""
        try:
            # AMS2 uses paging file backed shared memory
            self.map_file = mmap.mmap(0, ctypes.sizeof(SharedMemory), self.map_name)
            self.shared_memory = SharedMemory.from_buffer(self.map_file)
            self.connected = True
            print(f"Connected to Shared Memory: {self.map_name}")
        except FileNotFoundError:
            self.connected = False
            self.last_error = "AMS2/PCars2 not running (Shared Memory not found)."
        except Exception as e:
            self.connected = False
            self.last_error = f"Connection Error: {e}"
            print(self.last_error)

    def read_data(self):
        """
        Reads the current state from shared memory.
        Returns the SharedMemory struct object or None if not connected.
        Attempts to reconnect if disconnected.
        """
        if not self.connected:
            self.connect()
            if not self.connected:
                return None

        try:
            # In a real scenario with mmap, the struct is directly mapped to memory,
            # so accessing self.shared_memory fields reads live data.
            # However, for safety and snapshotting logic, we might want to return 
            # the reference or a copy if we needed thread safety (not needed here based on MainLoop requirement).
            return self.shared_memory
        except Exception as e:
            print(f"Error reading data: {e}")
            self.connected = False
            self.close()
            return None

    def close(self):
        try:
            if self.map_file:
                self.map_file.close()
        except:
            pass
        self.map_file = None
        self.shared_memory = None
        self.connected = False
