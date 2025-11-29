import time
import os
import msvcrt
import sys
from ams2_reader import AMS2Reader
from ams2_tyre_analyzer import TyreAnalyzer
from ams2_lap_manager import LapTimeManager

import ctypes

def clear_screen():
    # Use ctypes to move cursor to (0,0) on Windows to avoid flickering and scrolling
    try:
        class COORD(ctypes.Structure):
            _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]
        
        STD_OUTPUT_HANDLE = -11
        h = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        ctypes.windll.kernel32.SetConsoleCursorPosition(h, COORD(0, 0))
    except Exception:
        # Fallback if something goes wrong
        os.system('cls' if os.name == 'nt' else 'clear')

def format_time(seconds):
    if seconds <= 0: return "--:--.---"
    m = int(seconds // 60)
    s = int(seconds % 60)
    ms = int((seconds * 1000) % 1000)
    return f"{m:02d}:{s:02d}.{ms:03d}"

def print_header():
    # We print a big block of newlines first time to clear, then overwrite
    # But for now, let's just print the header.
    print("==================================================")
    print("       AMS2 TELEMETRY MONITOR (Standalone)        ")
    print("==================================================")
    print("Press 'Ctrl+C' to exit.")
    print("--------------------------------------------------")

def main():
    reader = AMS2Reader()
    analyzer = TyreAnalyzer()
    lap_manager = LapTimeManager()
    
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
                print(f"CAR:   '{car_name}'")
                print(f"TRACK: '{track_name}'")
                
                # Weather & Track Info
                print(f"COND:  Air: {data.mAmbientTemperature:.1f}C | Track: {data.mTrackTemperature:.1f}C | Rain: {data.mRainDensity:.2f}")
                
                # Lap Times
                # mCurrentLap is in ParticipantInfo, not top-level
                viewed_idx = data.mViewedParticipantIndex
                current_lap = 0
                if 0 <= viewed_idx < data.mNumParticipants:
                     current_lap = data.mParticipantInfo[viewed_idx].mCurrentLap

                last_lap_time = data.mLastLapTime
                
                # Save best lap if valid
                if last_lap_time > 0:
                    lap_manager.save_best_lap(car_name, track_name, last_lap_time)
                
                best_lap_record = lap_manager.get_best_lap(car_name, track_name)
                best_lap_str = f"{format_time(best_lap_record[0])} ({best_lap_record[1]})" if best_lap_record else "Noch keine"
                
                print("\n--- RUNDENZEITEN ---")
                print(f"Aktuelle Runde: {current_lap}")
                print(f"Letzte Runde:   {format_time(last_lap_time)}")
                print(f"Beste Runde:    {best_lap_str}")
                
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

                # Update Analyzer with Lap Count
                # Note: mCurrentLap is 1-based. Completed laps = mCurrentLap - 1 (roughly)
                # But AMS2 mCurrentLap starts at 1. So if we are in lap 1, we completed 0.
                laps_completed = current_lap - 1 if current_lap > 0 else 0
                analyzer.update(data, laps_completed)
                
                # Print Analyzer Output
                print("\n--- REIFEN INGENIEUR ---")
                print(f"Status: {analyzer.get_status()}")
                
                analysis = analyzer.get_analysis()
                if analysis:
                    print(f"{'Reifen':<6} | {'Temp':<6} | {'Druck-Status':<12} | {'Druck-Action':<22} | {'Sturz-Action':<25}")
                    print("-" * 85)
                    for tyre in ["FL", "FR", "RL", "RR"]:
                        info = analysis[tyre]
                        print(f"{tyre:<6} | {info['temp']:5.1f}C | {info['status']:<12} | {info['action']:<22} | {info['camber_action']:<25}")
                        if info['details']:
                            print(f"       -> {info['details']}")
                
                if data.mSpeed == 0 and data.mRpm == 0:
                    print("\n[WARNING] All values are ZERO? Checking raw bytes...")
                    # If we could inspect raw memory here it would be good, but for now let's rely on the strings.
                    if not car_name:
                        print("-> Car Name is empty. Struct might be completely misaligned or empty.")

            elif data and data.mGameState == 3:
                # PAUSE MODE
                clear_screen()
                print("==================================================")
                print("       PAUSE - SETUP EMPFEHLUNGEN                 ")
                print("==================================================")
                
                analysis = analyzer.get_analysis()
                if analysis:
                    print("\n--- REIFEN & STURZ ANALYSE ---")
                    print(f"{'Reifen':<6} | {'Temp':<6} | {'Druck-Status':<12} | {'Druck-Action':<22} | {'Sturz-Action':<25}")
                    print("-" * 85)
                    for tyre in ["FL", "FR", "RL", "RR"]:
                        info = analysis[tyre]
                        print(f"{tyre:<6} | {info['temp']:5.1f}C | {info['status']:<12} | {info['action']:<22} | {info['camber_action']:<25}")
                        
                        # Detailed reasoning for Pause Mode
                        if info['details']:
                            print(f"       -> {info['details']}")
                        
                        # Camber reasoning
                        if "VERRINGERN" in info['camber_action']:
                            diff = info['temp_inner'] - info['temp_outer']
                            print(f"       -> GRUND: Innen zu kalt (Delta: {diff:.1f}C). Kontaktfläche muss nach innen.")
                        elif "ERHÖHEN" in info['camber_action']:
                            diff = info['temp_inner'] - info['temp_outer']
                            print(f"       -> GRUND: Innen zu heiß (Delta: {diff:.1f}C). Kontaktfläche muss nach außen.")
                            
                    print("\n[HINWEIS] Ändere diese Einstellungen im Setup-Menü.")
                else:
                    print("\nNoch nicht genügend Daten für eine Analyse gesammelt.")
                    print(f"Status: {analyzer.get_status()}")

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
    except Exception as e:
        import traceback
        print("\n\nCRITICAL ERROR OCCURRED:")
        traceback.print_exc()
        print(f"\nError: {e}")
        input("\nPress Enter to exit...")
    finally:
        reader.close()
        print("Disconnected.")

if __name__ == "__main__":
    main()
