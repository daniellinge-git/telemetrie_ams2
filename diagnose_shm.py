import mmap
import struct
import time

SHARED_MEMORY_NAME = "$pcars2$"
BUFFER_SIZE = 9000 # Enough to cover most headers

def hex_dump(data, length=64):
    print(f"First {length} bytes:")
    print(" ".join(f"{b:02X}" for b in data[:length]))

def diagnose():
    print(f"Attempting to open Shared Memory: {SHARED_MEMORY_NAME}")
    try:
        # Try opening without size first (existing map)
        shm = mmap.mmap(0, BUFFER_SIZE, tagname=SHARED_MEMORY_NAME, access=mmap.ACCESS_READ)
        print("SUCCESS: Connected to Shared Memory!")
        
        while True:
            shm.seek(0)
            data = shm.read(BUFFER_SIZE)
            
            # Check for ANY non-zero byte
            non_zero = any(b != 0 for b in data)
            
            # Decode Version (first 4 bytes, uint)
            version = struct.unpack("I", data[:4])[0]
            game_state = struct.unpack("I", data[8:12])[0]
            
            print("-" * 40)
            print(f"Data Detected: {non_zero}")
            print(f"Version: {version}")
            print(f"GameState: {game_state}")
            hex_dump(data)
            
            if not non_zero:
                print("\nWARNING: MEMORY IS ALL ZEROS.")
                print("Possible causes:")
                print("1. Game is not running.")
                print("2. 'Shared Memory' is disabled in Game Options.")
                print("3. Game is running as Admin, Script is not.")
            else:
                print("\nOK: Data found!")
            
            print("\nPress Ctrl+C to stop...")
            time.sleep(2.0)
            
    except FileNotFoundError:
        print("ERROR: Shared Memory file not found.")
        print("Game is likely not running or has not created the memory map yet.")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    diagnose()
