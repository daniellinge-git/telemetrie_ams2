import time
import os
import msvcrt
import sys
from ams2_reader import AMS2Reader
from ams2_race_engineer import RaceEngineer
from ams2_lap_manager import LapTimeManager

import ctypes

# Console Width for padding - reduced to 80 to prevent wrapping issues
CONSOLE_WIDTH = 80

def enable_ansi():
    # Enable ANSI escape sequences on Windows 10/11
    if os.name == 'nt':
        try:
            kernel32 = ctypes.windll.kernel32
            STD_OUTPUT_HANDLE = -11
            hOut = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            out_mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(hOut, ctypes.byref(out_mode))
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            kernel32.SetConsoleMode(hOut, out_mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
        except:
            pass

def clear_screen():
    # Try ANSI first (fastest, no flicker)
    print("\033[H", end="")
    
    # Check if we are actually at the top (heuristic? No, hard to check)
    # If ANSI is not supported, this prints garbage or does nothing.
    # But we enabled it.
    
    # Fallback/Double-check with ctypes for Windows
    if os.name == 'nt':
        try:
            class COORD(ctypes.Structure):
                _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]
            
            STD_OUTPUT_HANDLE = -11
            h = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            # Check return value!
            res = ctypes.windll.kernel32.SetConsoleCursorPosition(h, COORD(0, 0))
            if res == 0:
                # If ctypes fails, use cls
                os.system('cls')
        except Exception:
            os.system('cls')
    else:
        # Linux/Mac
        # print("\033[H", end="") is usually enough, but let's be safe
        pass

def print_line(text=""):
    # Truncate if too long, then pad
    text = str(text)[:CONSOLE_WIDTH]
    print(f"{text:<{CONSOLE_WIDTH}}")

def format_time(seconds):
    if seconds <= 0: return "--:--.---"
    m = int(seconds // 60)
    s = int(seconds % 60)
    ms = int((seconds * 1000) % 1000)
    return f"{m:02d}:{s:02d}.{ms:03d}"

def print_header():
    print_line("==================================================")
    print_line("       AMS2 TELEMETRY MONITOR (Standalone)        ")
    print_line("==================================================")
    print_line("Press 'Ctrl+C' to exit.")
    print_line("--------------------------------------------------")

def main():
    enable_ansi()
    
    reader = AMS2Reader()
    engineer = RaceEngineer()
    lap_manager = LapTimeManager()
    
    # Initial clear
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print_header()
    print_line("Connecting to AMS2 Shared Memory ($pcars2$)...")
    
    # Retry loop for connection
    while True:
        if reader.connect():
            break
        print_line("Waiting for AMS2 to start... (Retrying in 2s)")
        time.sleep(2)
    
    print_line("\nConnected! Reading data...")
    time.sleep(1)

    try:
        while True:
            data = reader.read()
            
            if data and (data.mGameState == 2 or data.mGameState == 4): # 2 = Playing, 4 = In Menu/Pit
                clear_screen()
                print_header()
                
                # Update Engineer
                engineer.update(data)
                
                # Debug Info
                print_line(f"DEBUG: Version={data.mVersion} | Build={data.mBuildVersionNumber}")
                print_line(f"DEBUG: ViewedPartIdx={data.mViewedParticipantIndex} | NumPart={data.mNumParticipants}")
                
                # Basic Info
                state_desc = "Playing" if data.mGameState == 2 else "In Menu/Pit (Time Ticking)"
                print_line(f"SESSION STATE: {data.mSessionState} | GAME STATE: {data.mGameState} ({state_desc})")
                
                # Strings
                car_name = data.mCarName.decode('utf-8', errors='ignore').strip()
                track_name = data.mTrackLocation.decode('utf-8', errors='ignore').strip()
                print_line(f"CAR:   '{car_name}'")
                print_line(f"TRACK: '{track_name}'")
                
                # Weather & Track Info
                print_line(f"COND:  Air: {data.mAmbientTemperature:.1f}C | Track: {data.mTrackTemperature:.1f}C | Rain: {data.mRainDensity:.2f}")
                
                # Lap Times
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
                
                print_line("\n--- RUNDENZEITEN ---")
                print_line(f"Aktuelle Runde: {current_lap}")
                print_line(f"Letzte Runde:   {format_time(last_lap_time)}")
                print_line(f"Beste Runde:    {best_lap_str}")
                
                print_line("\n--- DRIVING DATA ---")
                print_line(f"SPEED:    {data.mSpeed * 3.6:6.1f} km/h")
                print_line(f"RPM:      {data.mRpm:6.0f}")
                print_line(f"GEAR:     {data.mGear}")
                
                # Pedals
                print_line(f"THROTTLE: {data.mThrottle*100:5.1f}%")
                print_line(f"BRAKE:    {data.mBrake*100:5.1f}%")
                
                # Tyres
                temps = [t for t in data.mTyreTemp]
                print_line("\n--- TYRE TEMPS (C) ---")
                print_line(f"FL: {temps[0]:3.0f} | FR: {temps[1]:3.0f}")
                print_line(f"RL: {temps[2]:3.0f} | RR: {temps[3]:3.0f}")

                # Engineer Message
                print_line("\n--- RACE ENGINEER ---")
                msg = engineer.get_message()
                if "Box" in msg:
                    print_line(f"!!! {msg} !!!")
                else:
                    print_line(f"> {msg}")
                
                if data.mSpeed == 0 and data.mRpm == 0:
                    print_line("\n[WARNING] All values are ZERO? Checking raw bytes...")
                    if not car_name:
                        print_line("-> Car Name is empty. Struct might be completely misaligned or empty.")
                
                # Clear remaining lines
                for _ in range(5):
                    print_line("")

            elif data and data.mGameState == 3:
                # PAUSE MODE
                clear_screen()
                print_line("==================================================")
                print_line("       PAUSE - SETUP EMPFEHLUNGEN                 ")
                print_line("==================================================")
                
                analysis = engineer.get_analysis()
                
                if analysis['ready']:
                    print_line("\n--- REIFEN & STURZ ANALYSE ---")
                    print_line(f"{'Reifen':<6} | {'Temp':<6} | {'Druck-Status':<12} | {'Druck-Action':<22} | {'Sturz-Action':<25}")
                    print_line("-" * 85)
                    
                    tyre_info = analysis['tyres']
                    for tyre in ["FL", "FR", "RL", "RR"]:
                        if tyre in tyre_info:
                            info = tyre_info[tyre]
                            print_line(f"{tyre:<6} | {info['temp']:5.1f}C | {info['status']:<12} | {info['action']:<22} | {info['camber_action']:<25}")
                            
                            if info['details']:
                                print_line(f"       -> {info['details']}")
                            
                            if "VERRINGERN" in info['camber_action']:
                                diff = info['temp_inner'] - info['temp_outer']
                                print_line(f"       -> GRUND: Innen zu kalt (Delta: {diff:.1f}C). Kontaktfläche muss nach innen.")
                            elif "ERHÖHEN" in info['camber_action']:
                                diff = info['temp_inner'] - info['temp_outer']
                                print_line(f"       -> GRUND: Innen zu heiß (Delta: {diff:.1f}C). Kontaktfläche muss nach außen.")
                    
                    print_line("\n--- LENKUNG ---")
                    if analysis['steering']:
                        print_line(f"Empfehlung: {analysis['steering']}")
                    else:
                        print_line("Keine Empfehlung zur Lenkung.")
                        
                    print_line("\n[HINWEIS] Ändere diese Einstellungen im Setup-Menü.")
                else:
                    print_line("\nNoch nicht genügend Daten für eine Analyse gesammelt.")
                    print_line(f"Status: {engineer.get_message()}")
                
                for _ in range(5):
                    print_line("")

            elif data:
                clear_screen()
                print_header()
                print_line("Game is running but not in driving mode.")
                print_line(f"GameState: {data.mGameState} (1=Menu, 2=Playing, 3=Paused)")
                print_line("Waiting for race to start...")
                for _ in range(15):
                    print_line("")
            
            else:
                print_line("Lost connection to shared memory?")

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
