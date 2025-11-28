import mmap
import ctypes
import time
from ams2_structs import SharedMemory

SHARED_MEMORY_NAME = "$pcars2$"

class AMS2Reader:
    def __init__(self):
        self.shm = None
        self.mm = None
        self.shared_data = None

    def connect(self):
        try:
            struct_size = ctypes.sizeof(SharedMemory)
            self.mm = mmap.mmap(0, struct_size, tagname=SHARED_MEMORY_NAME, access=mmap.ACCESS_READ)
            print(f"Connected to AMS2 Shared Memory ({struct_size} bytes).")
            return True
        except FileNotFoundError:
            print("AMS2 Shared Memory not found. Is the game running?")
            return False
        except Exception as e:
            print(f"Error connecting to Shared Memory: {e}")
            return False

    def read(self):
        if not self.mm:
            return None
        # Create a copy of the data from the shared memory buffer
        return SharedMemory.from_buffer_copy(self.mm)

    def close(self):
        if self.mm:
            self.mm.close()
            self.mm = None

if __name__ == "__main__":
    reader = AMS2Reader()
    if reader.connect():
        try:
            while True:
                data = reader.read()
                if data:
                    # Print some key metrics
                    print(f"RPM: {data.mRpm:.0f} | Speed: {data.mSpeed*3.6:.1f} km/h | Gear: {data.mGear} | Throttle: {data.mThrottle:.2f}", end="\r")
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            reader.close()
