import time
import os
import msvcrt
from ams2_reader import AMS2Reader
from ams2_recorder import DataRecorder

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    reader = AMS2Reader()
    recorder = DataRecorder()
    print("Connecting to AMS2 Shared Memory...")
    
    if reader.connect():
        print("Connected! Press 'r' to toggle recording, Ctrl+C to stop.", flush=True)
        try:
            while True:
                # Check for key press
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key.lower() == b'r':
                        if recorder.recording:
                            recorder.stop()
                        else:
                            recorder.start()

                data = reader.read()
                if data:
                    recorder.record_frame(data)
                    
                    # clear_screen()
                    print("=== AMS2 Telemetry Debug ===")
                    print(f"Version: {data.mVersion} | Build: {data.mBuildVersionNumber}")
                    print(f"Session State: {data.mSessionState} | Game State: {data.mGameState}")
                    print(f"Recording: {'[ON]' if recorder.recording else '[OFF]'}")
                    
                    print("\n--- Session Info ---")
                    print(f"Car: {data.mCarName.decode('utf-8', errors='ignore')}")
                    print(f"Class: {data.mCarClassName.decode('utf-8', errors='ignore')}")
                    print(f"Track: {data.mTrackLocation.decode('utf-8', errors='ignore')} ({data.mTrackVariation.decode('utf-8', errors='ignore')})")
                    
                    print("\n--- Weather ---")
                    print(f"Ambient Temp: {data.mAmbientTemperature:.1f}°C")
                    print(f"Track Temp:   {data.mTrackTemperature:.1f}°C")
                    print(f"Rain Density: {data.mRainDensity:.2f}")
                    print(f"Wind Speed:   {data.mWindSpeed:.1f} m/s")
                    
                    print("\n--- Physics ---")
                    print(f"Speed:    {data.mSpeed*3.6:.1f} km/h")
                    print(f"RPM:      {data.mRpm:.0f}")
                    print(f"Gear:     {data.mGear}")
                    print(f"Throttle: {data.mThrottle:.2f}")
                    print(f"Brake:    {data.mBrake:.2f}")
                    print(f"Steering: {data.mSteering:.2f}")
                    
                    print("\n--- Tyres (FL, FR, RL, RR) ---")
                    temps = [t for t in data.mTyreTemp]
                    print(f"Temps: {temps[0]:.0f}°C, {temps[1]:.0f}°C, {temps[2]:.0f}°C, {temps[3]:.0f}°C", flush=True)
                else:
                    print("Waiting for data...", end="\r", flush=True)
                    
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopped.")
        finally:
            recorder.stop()
            reader.close()
    else:
        print("Could not connect. Make sure AMS2 is running and Shared Memory is enabled (Project Cars 2 mode).")

if __name__ == "__main__":
    main()
