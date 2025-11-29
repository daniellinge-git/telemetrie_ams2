from ams2_tyre_analyzer import TyreAnalyzer
from ams2_steering_analyzer import SteeringAnalyzer

class RaceEngineer:
    def __init__(self):
        self.tyre_analyzer = TyreAnalyzer()
        self.steering_analyzer = SteeringAnalyzer()
        
        # States
        self.STATE_WAITING = "WAITING"         # Waiting for race to start
        self.STATE_GATHERING = "GATHERING"     # Collecting reference laps (2 laps)
        self.STATE_CHECKING = "CHECKING"       # Checking stability
        self.STATE_BOX = "BOX"                 # Ready for box
        
        self.state = self.STATE_WAITING
        self.start_lap = -1
        self.laps_completed = 0
        self.min_laps = 2
        
        self.message = ""
        self.has_visited_pits = False
        
    def update(self, data):
        # Update Sub-Components
        # Calculate laps completed (AMS2 mCurrentLap starts at 1)
        # If mCurrentLap is 1, we have completed 0.
        # But we need to handle the case where we join mid-session?
        # Let's just trust mCurrentLap.
        
        # data.mParticipantInfo[data.mViewedParticipantIndex].mCurrentLap
        current_lap = 0
        if 0 <= data.mViewedParticipantIndex < data.mNumParticipants:
             current_lap = data.mParticipantInfo[data.mViewedParticipantIndex].mCurrentLap
        
        # Laps completed is current_lap - 1
        laps_completed = current_lap - 1 if current_lap > 0 else 0
        self.laps_completed = laps_completed
        
        self.tyre_analyzer.update(data)
        self.steering_analyzer.update(data, current_lap)
        
        # State Machine
        
        # 1. Handle GameState != Playing
        # 1. Handle GameState != Playing
        if data.mGameState != 2:
            # If Paused (3), we just wait. Do NOT reset.
            if data.mGameState == 3:
                return

            # If we are in BOX state (Analysis ready), we KEEP it, so the user can see it in the menu/pause.
            if self.state == self.STATE_BOX:
                return
            
            # Only reset if we are explicitly in MENU (1)
            # BUT: Pit Menu is also State 1. So we CANNOT reset here if we are in BOX state.
            # We rely on the "New Run" detection (Speed > 10) to reset.
            # if data.mGameState == 1:
            #    print(f"DEBUG: RaceEngineer Reset - GameState is MENU (1)")
            #    self.state = self.STATE_WAITING
            #    self.message = "Warte auf Start..."
            
            return

        # 2. Handle State Transitions
        
        # If we are in BOX state, we wait until the user starts a NEW run
        # A new run is defined as: We were in the pits, and now we are driving fast again.
        if self.state == self.STATE_BOX:
            # Track if we are in the pits
            if data.mPitMode != 0:
                self.has_visited_pits = True
            
            # If driving fast AND NOT in pits AND we have visited the pits -> New Run!
            if self.has_visited_pits and data.mSpeed > 10.0 and data.mPitMode == 0:
                print(f"DEBUG: RaceEngineer Reset - New Run Detected (Pit Visit Confirmed)")
                self.state = self.STATE_GATHERING
                self.start_lap = laps_completed
                self.tyre_analyzer.reset()
                self.message = "Neuer Run gestartet. Sammle Daten..."
                self.has_visited_pits = False
            else:
                # If we haven't been to pits yet, we keep showing the message
                if not self.has_visited_pits:
                     pass # Message stays "BOX, Änderung Notwendig!" or similar
                else:
                     self.message = "Bereit für neuen Run..." # In pits
            return

        # If we are WAITING (e.g. just started app or came from Menu)
        if self.state == self.STATE_WAITING:
            self.state = self.STATE_GATHERING
            self.start_lap = laps_completed
            self.tyre_analyzer.reset()
            
        laps_driven = laps_completed - self.start_lap
        
        # Stability First Logic
        # We check stability every update (TyreAnalyzer handles the window)
        # We only need a minimum amount of data (e.g. 30 seconds history in analyzer)
        # The analyzer returns is_stable=False if not enough history.
        
        if self.state == self.STATE_GATHERING or self.state == self.STATE_CHECKING:
            # Check Stability OR Critical Issues
            # If we have enough data (>80%) and temps are way off, we don't need perfect stability
            prog = self.tyre_analyzer.get_progress()
            is_stable = self.tyre_analyzer.are_all_stable()
            
            # Check for critical temps (e.g. > 95 or < 65)
            # We peek at the current analysis
            analysis = self.get_analysis()
            critical_issue = False
            for t in analysis['tyres'].values():
                if "High" in t['action'] or "Low" in t['action']: # If action is strong
                     # Simple check: if we are far from target
                     pass
            
            # Actually, let's just trust the analyzer's "action" if progress is high enough
            if is_stable or prog > 80.0:
                needs_change = False
                for t in analysis['tyres'].values():
                    if "OK" not in t['action'] or "OK" not in t['camber_action']:
                        needs_change = True
                        break
                
                if needs_change:
                    # If not stable yet but > 80%, only trigger if it's really bad?
                    # For now, let's be aggressive. If > 80% and needs change, DO IT.
                    self.state = self.STATE_BOX
                    self.has_visited_pits = False # Reset flag when entering BOX state
                    self.message = "BOX, Änderung Notwendig!"
                elif is_stable:
                    self.message = "Setup OK. Weiterfahren..."
                else:
                    self.message = f"Analysiere... ({prog:.0f}%)"
            else:
                # Not stable yet and < 80%
                self.message = f"Analysiere... ({prog:.0f}%)"

    def get_message(self):
        return self.message
        
    def get_analysis(self):
        # Combine analysis from components
        tyre_analysis = self.tyre_analyzer.get_analysis()
        steering_rec = self.steering_analyzer.get_recommendation()
        
        return {
            'tyres': tyre_analysis,
            'steering': steering_rec,
            'ready': (self.state == self.STATE_BOX)
        }
