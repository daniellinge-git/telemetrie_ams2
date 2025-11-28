import time
import os
import msvcrt
import sys
from ams2_reader import AMS2Reader

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("==================================================")
    print("       AMS2 TELEMETRY MONITOR (Standalone)        ")
    print("==================================================")
    print("Press 'Ctrl+C' to exit.")
    print("--------------------------------------------------")

def main():
    reader = AMS2Reader()
    
    print_header()
    print("Connecting to AMS2 Shared Memory ($pcars2$)...")
    
    # Retry loop for connection
    while True:
        if reader.connect():
            break
        print("Waiting for AMS2 to start... (Retrying in 2s)", end="\r")
        time.sleep(2)
    
    print("\nConnected! Reading data...")
    time.sleep(1)

    try:
        while True:
            data = reader.read()
            
            if data and (data.mGameState == 2 or data.mGameState == 4): # 2 = Playing, 4 = In Menu/Pit
                clear_screen()
                print_header()
                
                # Debug Info
                print(f"DEBUG: Version={data.mVersion} | Build={data.mBuildVersionNumber}")
                print(f"DEBUG: ViewedPartIdx={data.mViewedParticipantIndex} | NumPart={data.mNumParticipants}")
                
                # Basic Info
                state_desc = "Playing" if data.mGameState == 2 else "In Menu/Pit (Time Ticking)"
                print(f"SESSION STATE: {data.mSessionState} | GAME STATE: {data.mGameState} ({state_desc})")
                
                # Strings (Check if these are readable)
                car_name = data.mCarName.decode('utf-8', errors='ignore').strip()
                track_name = data.mTrackLocation.decode('utf-8', errors='ignore').strip()
                print(f"CAR: '{car_name}'")
                print(f"TRACK: '{track_name}'")
                
                print("\n--- DRIVING DATA ---")
                print(f"SPEED:    {data.mSpeed * 3.6:6.1f} km/h")
                print(f"RPM:      {data.mRpm:6.0f}")
                print(f"GEAR:     {data.mGear}")
                
                # Pedals
                print(f"THROTTLE: {data.mThrottle*100:5.1f}%")
                print(f"BRAKE:    {data.mBrake*100:5.1f}%")
                
                # Tyres
                temps = [t for t in data.mTyreTemp]
                print("\n--- TYRE TEMPS (C) ---")
                print(f"FL: {temps[0]:3.0f} | FR: {temps[1]:3.0f}")
                print(f"RL: {temps[2]:3.0f} | RR: {temps[3]:3.0f}")
                
                if data.mSpeed == 0 and data.mRpm == 0:
                    print("\n[WARNING] All values are ZERO? Checking raw bytes...")
                    # If we could inspect raw memory here it would be good, but for now let's rely on the strings.
                    if not car_name:
                        print("-> Car Name is empty. Struct might be completely misaligned or empty.")

            elif data:
                # Game is running but not in a race/driving state
                clear_screen()
                print_header()
                print("Game is running but not in driving mode.")
                print(f"GameState: {data.mGameState} (1=Menu, 2=Playing, 3=Paused)")
                print("Waiting for race to start...")
            
            else:
                print("Lost connection to shared memory?", end="\r")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        reader.close()
        print("Disconnected.")

if __name__ == "__main__":
    main()
