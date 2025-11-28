import csv
import time
import os
from datetime import datetime

class DataRecorder:
    def __init__(self, output_dir="data"):
        self.output_dir = output_dir
        self.recording = False
        self.file_handle = None
        self.writer = None
        self.start_time = 0
        self.filename = ""

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def start(self):
        if self.recording:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = os.path.join(self.output_dir, f"telemetry_{timestamp}.csv")
        
        try:
            self.file_handle = open(self.filename, 'w', newline='')
            self.writer = csv.writer(self.file_handle)
            
            # Write Header
            header = [
                "Timestamp", "SessionTime", "FrameIdentifier",
                "SessionState", "GameState",
                "Speed_Kmh", "RPM", "Gear",
                "Throttle", "Brake", "Clutch", "Steering",
                "LapInvalidated", "CurrentLapTime", "LastLapTime", "BestLapTime",
                "TrackTemp", "AmbientTemp", "RainDensity",
                "TyreTemp_FL", "TyreTemp_FR", "TyreTemp_RL", "TyreTemp_RR",
                "TyreWear_FL", "TyreWear_FR", "TyreWear_RL", "TyreWear_RR",
                "BrakeTemp_FL", "BrakeTemp_FR", "BrakeTemp_RL", "BrakeTemp_RR",
                "RideHeight_FL", "RideHeight_FR", "RideHeight_RL", "RideHeight_RR",
                "SuspensionTravel_FL", "SuspensionTravel_FR", "SuspensionTravel_RL", "SuspensionTravel_RR",
                "PosX", "PosY", "PosZ"
            ]
            self.writer.writerow(header)
            
            self.recording = True
            self.start_time = time.time()
            print(f"Recording started: {self.filename}")
        except Exception as e:
            print(f"Failed to start recording: {e}")

    def stop(self):
        if not self.recording:
            return

        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
            self.writer = None
        
        self.recording = False
        print(f"Recording stopped: {self.filename}")

    def record_frame(self, data):
        if not self.recording or not data:
            return

        current_time = time.time()
        
        # Extract Tyre Temps (convert to list if needed, ctypes array is iterable)
        tyre_temps = [t for t in data.mTyreTemp]
        tyre_wear = [w for w in data.mTyreWear]
        brake_temps = [b for b in data.mBrakeTempCelsius]
        ride_height = [h for h in data.mRideHeight]
        susp_travel = [s for s in data.mSuspensionTravel]
        # pos = [p for p in data.mPosition] # mPosition not in SharedMemory struct

        row = [
            f"{current_time:.3f}", f"{data.mCurrentTime:.3f}", "0", # FrameNum placeholder
            data.mSessionState, data.mGameState,
            f"{data.mSpeed * 3.6:.2f}", f"{data.mRpm:.0f}", data.mGear,
            f"{data.mThrottle:.3f}", f"{data.mBrake:.3f}", f"{data.mClutch:.3f}", f"{data.mSteering:.3f}",
            data.mLapInvalidated, f"{data.mCurrentTime:.3f}", f"{data.mLastLapTime:.3f}", f"{data.mBestLapTime:.3f}",
            f"{data.mTrackTemperature:.1f}", f"{data.mAmbientTemperature:.1f}", f"{data.mRainDensity:.2f}",
            f"{tyre_temps[0]:.0f}", f"{tyre_temps[1]:.0f}", f"{tyre_temps[2]:.0f}", f"{tyre_temps[3]:.0f}",
            f"{tyre_wear[0]:.3f}", f"{tyre_wear[1]:.3f}", f"{tyre_wear[2]:.3f}", f"{tyre_wear[3]:.3f}",
            f"{brake_temps[0]:.0f}", f"{brake_temps[1]:.0f}", f"{brake_temps[2]:.0f}", f"{brake_temps[3]:.0f}",
            f"{ride_height[0]:.3f}", f"{ride_height[1]:.3f}", f"{ride_height[2]:.3f}", f"{ride_height[3]:.3f}",
            f"{susp_travel[0]:.3f}", f"{susp_travel[1]:.3f}", f"{susp_travel[2]:.3f}", f"{susp_travel[3]:.3f}",
            "0.00", "0.00", "0.00" # PosX, PosY, PosZ placeholders
        ]
        
        try:
            self.writer.writerow(row)
        except Exception as e:
            print(f"Error writing frame: {e}")
