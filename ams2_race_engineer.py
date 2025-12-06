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
        
        # v1.1: Distance Tracking
        self.stint_start_odometer = -1.0
        self.driven_distance_stint = 0.0
        self.analysis_distance_threshold = 10.0 # Analyze after 10 km (was 3.0)
        
        # v1.1: Setup Comparison
        self.previous_run_snapshot = None
        self.setup_feedback = None # "IMPROVED", "WORSENED", "NEUTRAL", or None
        
        # v1.1: Handling Analysis
        self.handling_status = "NEUTRAL" # "UNDERSTEER", "OVERSTEER", "NEUTRAL"
        self.handling_value = 0.0 # Positive = Oversteer, Negative = Understeer
        
        self.message = ""
        self.has_visited_pits = False
        
    def update(self, data):
        # Update Sub-Components
        
        # Odometer Tracking
        if self.stint_start_odometer < 0:
            self.stint_start_odometer = data.mOdometerKM
            
        # Calculate driven distance in this stint
        # Ensure we don't get negative values if odometer resets (e.g. restart)
        current_odometer = data.mOdometerKM
        if current_odometer < self.stint_start_odometer:
             self.stint_start_odometer = current_odometer
             
        self.driven_distance_stint = current_odometer - self.stint_start_odometer
        
        # Calculate laps completed (AMS2 mCurrentLap starts at 1)
        current_lap = 0
        if 0 <= data.mViewedParticipantIndex < data.mNumParticipants:
             current_lap = data.mParticipantInfo[data.mViewedParticipantIndex].mCurrentLap
        
        laps_completed = current_lap - 1 if current_lap > 0 else 0
        self.laps_completed = laps_completed
        
        self.tyre_analyzer.update(data)
        self.steering_analyzer.update(data, current_lap)
        
        # v1.1: Handling Analysis (Realtime)
        self.check_handling_balance(data)
        
        # State Machine
        
        # 1. Handle GameState != Playing
        if data.mGameState != 2:
            # If Paused (3), we just wait. Do NOT reset.
            if data.mGameState == 3:
                return

            # If we are in BOX state (Analysis ready), we KEEP it.
            if self.state == self.STATE_BOX:
                return
            
            return

        # 2. Handle State Transitions
        
        # If we are in BOX state, we wait until the user starts a NEW run
        if self.state == self.STATE_BOX:
            # Track if we are in the pits
            if data.mPitMode != 0:
                self.has_visited_pits = True
            
            # If driving fast AND NOT in pits AND we have visited the pits -> New Run!
            if self.has_visited_pits and data.mSpeed > 10.0 and data.mPitMode == 0:
                print(f"DEBUG: RaceEngineer Reset - New Run Detected (Pit Visit Confirmed)")
                
                # Snapshot current analysis before resetting? 
                # Actually we should have done this when entering BOX state.
                
                self.state = self.STATE_GATHERING
                self.start_lap = laps_completed
                
                # v1.1: Reset Distance
                self.stint_start_odometer = data.mOdometerKM
                self.driven_distance_stint = 0.0
                self.setup_feedback = None # Reset feedback for new run
                
                self.tyre_analyzer.reset()
                self.message = "Neuer Run gestartet. Sammle Daten..."
                self.has_visited_pits = False
            else:
                if not self.has_visited_pits:
                     pass 
                else:
                     self.message = "Bereit für neuen Run..." 
            return

        # If we are WAITING (e.g. just started app or came from Menu)
        if self.state == self.STATE_WAITING:
            self.state = self.STATE_GATHERING
            self.start_lap = laps_completed
            self.stint_start_odometer = data.mOdometerKM # Init odometer
            self.tyre_analyzer.reset()
            
        # Analysis Logic
        
        if self.state == self.STATE_GATHERING or self.state == self.STATE_CHECKING:
            
            # v1.1: Check Session State - If RACE, do NOT analyze for Setup
            # mSessionState: 0=Invalid, 1=Practice, 2=Test, 3=Quali, 4=Formation, 5=Race, 6=TimeAttack
            if data.mSessionState == 5: # RACE
                 self.message = f"RACE - {self.driven_distance_stint:.1f} km - {self.handling_status}"
                 return

            # v1.1: Check Distance Threshold
            if self.driven_distance_stint >= self.analysis_distance_threshold:
                
                # Perform Analysis
                analysis = self.get_analysis()
                
                # Check if we need changes
                needs_change = False
                for t in analysis['tyres'].values():
                    if "OK" not in t['action'] or "OK" not in t['camber_action']:
                        needs_change = True
                        break
                
                if needs_change:
                    self.state = self.STATE_BOX
                    self.has_visited_pits = False 
                    self.message = "BOX, Änderung Notwendig!"
                    
                    # v1.1: Compare with previous run if available
                    if self.previous_run_snapshot:
                        self.evaluate_setup_change(analysis)
                    
                    # Save this analysis as snapshot for NEXT run
                    self.previous_run_snapshot = analysis
                    
                else:
                    # If everything is OK, we can stay in GATHERING/CHECKING or just say OK
                    # But maybe we want to keep monitoring?
                    # Let's say "Setup OK" but keep monitoring (don't lock to BOX state unless user wants to stop)
                    # Actually, if it's OK, we might want to "lock" it as a "Good Run" or just keep updating.
                    # For now, let's keep updating but show "Setup OK".
                    self.message = f"Setup OK. ({self.driven_distance_stint:.1f} km)"
                    
                    # Also compare if we had a previous run (maybe we improved it to be OK?)
                    if self.previous_run_snapshot and self.setup_feedback is None:
                         self.evaluate_setup_change(analysis)

            else:
                # Not enough distance yet
                self.message = f"Analysiere... ({self.driven_distance_stint:.1f}/{self.analysis_distance_threshold:.0f}km) - {self.handling_status}"

    def check_handling_balance(self, data):
        # Slip Speed based analysis
        # FL=0, FR=1, RL=2, RR=3
        
        # Only check when moving fast enough and cornering
        if data.mSpeed < 10.0:
            self.handling_status = "NEUTRAL"
            return
            
        # Get absolute slip speeds
        slips = [abs(data.mTyreSlipSpeed[i]) for i in range(4)]
        
        # Avg Front Slip vs Avg Rear Slip
        front_slip = (slips[0] + slips[1]) / 2.0
        rear_slip = (slips[2] + slips[3]) / 2.0
        
        # Thresholds (need tuning, start with 0.5 m/s diff)
        threshold = 0.5 
        
        # Calculate Balance Value (Positive = OS, Negative = US)
        self.handling_value = rear_slip - front_slip
        
        if self.handling_value > threshold:
            self.handling_status = "OVERSTEER" # Heck bricht aus
        elif self.handling_value < -threshold:
            self.handling_status = "UNDERSTEER" # Schiebt über Vorderräder
        else:
            self.handling_status = "NEUTRAL"


    def evaluate_setup_change(self, current_analysis):
        """
        Compares current analysis with self.previous_run_snapshot 
        and sets self.setup_feedback.
        """
        if not self.previous_run_snapshot:
            return

        # Simple logic: Count how many "OK"s we have now vs before
        
        def count_ok(analysis):
            count = 0
            for t in analysis['tyres'].values():
                if "OK" in t['action']: count += 1
                if "OK" in t['camber_action']: count += 1
            return count
            
        prev_ok = count_ok(self.previous_run_snapshot)
        curr_ok = count_ok(current_analysis)
        
        if curr_ok > prev_ok:
            self.setup_feedback = "IMPROVED"
        elif curr_ok < prev_ok:
            self.setup_feedback = "WORSENED"
        else:
            self.setup_feedback = "NEUTRAL"
            
        print(f"DEBUG: Setup Evaluation: Prev OK={prev_ok}, Curr OK={curr_ok} -> {self.setup_feedback}")

    def get_message(self):
        return self.message
        
    def get_analysis(self):
        # Combine analysis from components
        tyre_analysis = self.tyre_analyzer.get_analysis()
        steering_rec = self.steering_analyzer.get_recommendation()
        
        return {
            'tyres': tyre_analysis,
            'steering': steering_rec,
            'ready': (self.state == self.STATE_BOX),
            'distance': self.driven_distance_stint,
            'distance': self.driven_distance_stint,
            'feedback': self.setup_feedback,
            'handling': self.handling_status,
            'handling_val': self.handling_value
        }
