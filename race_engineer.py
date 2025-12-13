from ams2_tyre_analyzer import TyreAnalyzer
import math

class RaceEngineer:
    """
    Logic Layer for AMS2 Race Engineer.
    Implements State Machine: WAITING -> OBSERVING -> ANALYZING -> ADVISING
    """
    # States
    STATE_WAITING = "WAITING"         # Waiting for valid race state/movement
    STATE_OBSERVING = "OBSERVING"     # Collecting reference laps
    STATE_ANALYZING = "ANALYZING"     # Checking consistency
    STATE_ADVISING = "ADVISING"       # Showing Setup Hints (only when stopped)

    def __init__(self):
        self.state = self.STATE_WAITING
        self.tyre_analyzer = TyreAnalyzer()
        
        # Consistency Check
        self.lap_history = [] # List of tuples (lap_time, is_valid)
        self.current_lap = -1
        self.consistency_threshold = 0.5 # seconds
        self.min_consistent_laps = 2
        
        # Track Map / Corner Logic
        self.track_map_points = [] # List of (x, z, speed)
        
        # Output State
        self.message = "Warte auf Start..."
        self.setup_suggestions = [] # List of strings
        self.status_detail = ""
        
        # Internal tracking
        self.last_lap_idx = -1

    def process_data(self, data):
        """
        Main update method called by the loop.
        Input: data (SharedMemory struct)
        Output: Dictionary with advice, status, etc.
        """
        if data is None:
            return self._build_output()

        # Update Tyre Analyzer (always runs to gather history)
        self.tyre_analyzer.update(data)
        
        # State Machine Transition Logic
        self._update_state(data)
        
        # Update Track Map (if moving)
        if data.mSpeed > 5.0 and data.mLapInvalidated is False:
             # Basic sampling for track map
             # Optimisation: Only sample every X frames or distance could be added
             pos = data.mParticipantInfo[data.mViewedParticipantIndex].mWorldPosition
             self.track_map_points.append((pos[0], pos[2], data.mSpeed))

        return self._build_output()

    def _update_state(self, data):
        # 1. Global Checks
        # Get participant info
        idx = data.mViewedParticipantIndex
        participant = data.mParticipantInfo[idx]
        
        is_driving = (data.mGameState == 2) # Playing
        in_pit = (data.mPitMode != 0)
        speed = data.mSpeed
        
        current_lap_idx = participant.mCurrentLap
        
        # Lap Detection
        if current_lap_idx > self.last_lap_idx:
            if self.last_lap_idx != -1:
                # Lap finished
                last_time = data.mLastLapTime
                # Check validity (AMS2 mLapInvalidated is for CURRENT lap, 
                # but mLastLapTime is usually valid unless the previous lap was invalidated. 
                # We should have tracked invalidation during the lap. 
                # For simplicity, we assume if mLastLapTime > 0 it's valid-ish, 
                # but strict check would need per-lap invalidation flag tracking)
                
                # Simple heuristic: If we have a time, we accept it for now.
                # Ideally we check mLapsInvalidated array if available.
                self.lap_history.append(last_time)
                print(f"Lap {self.last_lap_idx} finished: {last_time}s")
            
            self.last_lap_idx = current_lap_idx

        # State Transitions
        if self.state == self.STATE_WAITING:
            if is_driving and not in_pit and speed > 10.0:
                self.state = self.STATE_OBSERVING
                self.message = "Sammle Runden..."
                self.lap_history = [] # Reset history on new run

        elif self.state == self.STATE_OBSERVING:
            self.message = f"Sammle Daten (Runden: {len(self.lap_history)})"
            
            # Check if we have enough laps
            if len(self.lap_history) >= 2:
                self.state = self.STATE_ANALYZING

        elif self.state == self.STATE_ANALYZING:
            is_consistent, delta = self._check_consistency()
            
            if is_consistent:
                self.message = f"Konsistent (Delta: {delta:.3f}s) -> Box für Setup!"
                # Transition to ADVISING only if stopped or in menu (handled by UI visibility mostly, but state can switch)
                if in_pit or speed < 1.0 or data.mGameState == 1: # Menu/Pit
                     self._generate_advice()
                     self.state = self.STATE_ADVISING
            else:
                self.message = f"Inkonsistent (Delta: {delta:.3f}s). Fahre konstanter!"
                # Pop oldest lap to keep sliding window if we want greedy approach, 
                # or just keep OBSERVING. Let's go back to OBSERVING to wait for next lap.
                # Actually, with sliding window we just stay here effectively.
                if len(self.lap_history) > 2:
                    self.lap_history.pop(0) # Remove oldest, keep trying with new pair

        elif self.state == self.STATE_ADVISING:
            # If we start driving again
            if is_driving and not in_pit and speed > 10.0:
                self.state = self.STATE_OBSERVING
                self.message = "Neuer Run gestartet..."
                self.lap_history = []
                self.setup_suggestions = []

    def _check_consistency(self):
        # Check last 2 laps
        if len(self.lap_history) < 2:
            return False, 99.9
            
        t1 = self.lap_history[-1]
        t2 = self.lap_history[-2]
        
        delta = abs(t1 - t2)
        return (delta < self.consistency_threshold), delta

    def _generate_advice(self):
        """Generates setup suggestions based on collected data."""
        self.setup_suggestions = []
        
        # get analysis from TyreAnalyzer
        tyre_data = self.tyre_analyzer.get_analysis()
        
        # 1. Camber Check
        for wheel, info in tyre_data.items():
            if "Sturz" in info.get('camber_action', ''):
                if "OK" not in info['camber_action']:
                     self.setup_suggestions.append(f"{wheel}: {info['camber_action']}")
        
        # 2. Pressure Check
        for wheel, info in tyre_data.items():
             if "Druck" in info.get('action', ''):
                 if "OK" not in info['action']:
                      self.setup_suggestions.append(f"{wheel}: {info['action']}")

        if not self.setup_suggestions:
            self.setup_suggestions.append("Alles OK! Setup scheint gut zu sein.")
            
    def _build_output(self):
        return {
            "state": self.state,
            "message": self.message,
            "suggestions": self.setup_suggestions,
            "track_points": self.track_map_points[-100:] if self.track_map_points else [] # Send recent points? Or all? UI needs to handle logic. 
            # For Canvas, sending all every frame is too heavy. UI should pull or we send only new ones.
            # Let's send only output status here.
        }
