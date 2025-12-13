import math

class PhaseDetector:
    """
    Determines the current driving phase (Corner Phase).
    Phases: STRAIGHT, BRAKING, TURN_IN, MID_CORNER, EXIT
    """
    def __init__(self):
        self.current_phase = "STRAIGHT"
        self.last_phase = "STRAIGHT"
    
    def update(self, data):
        """
        Updates the current phase based on telemetry data.
        """
        # Data extraction
        # speed = data.mSpeed * 3.6 # km/h
        brake = data.mUnfilteredBrake # 0.0 - 1.0
        throttle = data.mUnfilteredThrottle # 0.0 - 1.0
        # steering = abs(data.mSteering) # 0.0 - 1.0 (approx)
        
        # G-Forces (AMS2: X=Lateral, Z=Longitudinal)
        # Verify coordinate system! Usually: 
        # Z positive = braking? Or neg?
        # Let's rely on Pedals mostly for phase detection as G-force can be noisy.
        
        # Logic Priorities:
        # 1. Braking (High Brake Input) -> BRAKING
        # 2. Turn-In (Braking decreasing, Lateral G increasing / Steering increasing) -> TURN_IN
        # 3. Mid-Corner (Brake off, Throttle low/off, High Lateral G) -> MID_CORNER
        # 4. Exit (Throttle increasing, Steering decreasing) -> EXIT
        # 5. Straight (Throttle High, Steering Low) -> STRAIGHT
        
        prev_phase = self.current_phase
        
        # Thresholds
        BRAKE_THRES = 0.1
        THROTTLE_THRES = 0.1
        STEER_THRES = 0.05 # Deadzone
        LAT_G_THRES = 0.5 # G-Force threshold for cornering
        
        current_lat_g = abs(data.mLocalAcceleration[0]) # X is usually lateral
        
        # Phase Detection Logic
        if brake > BRAKE_THRES:
            # If we were in STRAIGHT or EXIT, we are now BRAKING
            # If we were MID_CORNER, maybe trail braking? Keep as is or switch?
            # Basic: Input dominant
            self.current_phase = "BRAKING"
            
        elif self.current_phase == "BRAKING":
            # If braking stops...
            if current_lat_g > LAT_G_THRES:
                self.current_phase = "TURN_IN" # Transition to turning
            else:
                self.current_phase = "STRAIGHT" # Just stopped braking on a straight
                
        elif self.current_phase == "TURN_IN":
            # If steering is stable/decreasing or throttle starts -> Mid/Exit
            if throttle > THROTTLE_THRES:
                if current_lat_g > LAT_G_THRES:
                     self.current_phase = "EXIT"
                else:
                     self.current_phase = "STRAIGHT"
            elif current_lat_g > LAT_G_THRES:
                 # Should we switch to MID_CORNER?
                 # Mid corner is often defined as the point of max lateral G or min speed.
                 # Let's stick to TURN_IN until we apply gas.
                 # OR: If brake is 0 and throttle is 0 -> COASTING/MID
                 if brake < 0.01 and throttle < 0.01:
                     self.current_phase = "MID_CORNER"
                     
        elif self.current_phase == "MID_CORNER":
            if throttle > THROTTLE_THRES:
                self.current_phase = "EXIT"
            elif current_lat_g < 0.2:
                self.current_phase = "STRAIGHT" # Lost speed/corner
                
        elif self.current_phase == "EXIT":
            if current_lat_g < 0.2 and throttle > 0.8:
                self.current_phase = "STRAIGHT"
            elif brake > BRAKE_THRES:
                self.current_phase = "BRAKING"
                
        elif self.current_phase == "STRAIGHT":
             if brake > BRAKE_THRES:
                 self.current_phase = "BRAKING"
             elif current_lat_g > LAT_G_THRES:
                 # Just turning without braking?
                 self.current_phase = "MID_CORNER" # Or Turn-in?
                 
        else:
            self.current_phase = "STRAIGHT"
            
        self.last_phase = prev_phase
        return self.current_phase


class AnalysisEngine:
    def __init__(self):
        self.phase_detector = PhaseDetector()
        self.events = [] # List of detected problems
        self.active_problems = {} # Current problems being detected (to debounce)
        
        # Constants
        self.MIN_SPEED = 20.0 # km/h
        
    def update(self, data):
        if data.mGameState != 2: return # Only Playing
        
        # Speed Check
        speed_kmh = data.mSpeed * 3.6
        if speed_kmh < self.MIN_SPEED: return
        
        # 1. Update Phase
        phase = self.phase_detector.update(data)
        
        # 2. Run Checks based on Phase
        if phase == "BRAKING":
            self.check_braking(data)
        elif phase == "TURN_IN":
            self.check_turn_in(data)
        elif phase == "EXIT":
            self.check_exit(data)
            
        # 3. Always check General stuff (Tyres, Bottoming)
        self.check_general(data)
        
    def check_braking(self, data):
        # A. Front Lockup
        # Wheel Speed < Car Speed (Significantly)
        # FL=0, FR=1, RL=2, RR=3
        
        speed = data.mSpeed # m/s (approx)
        if speed < 5.0: return
        
        # Simple Logic: If front wheels are much slower than car speed (e.g. 30% slower)
        # And brake is pressed
        
        fl_speed = abs(data.mTyreRPS[0] * data.mTyreRadius[0]) # approx speed m/s
        fr_speed = abs(data.mTyreRPS[1] * data.mTyreRadius[1])
        
        slip_ratio_fl = (speed - fl_speed) / max(speed, 0.1)
        slip_ratio_fr = (speed - fr_speed) / max(speed, 0.1)
        
        LOCKUP_THRES = 0.4 # 40% slip
        
        if slip_ratio_fl > LOCKUP_THRES or slip_ratio_fr > LOCKUP_THRES:
            self.add_event("Front Lockup", "Bremsbalance nach HINTEN", "BRAKING", data)

        # B. Rear Lockup (Instability)
        rl_speed = abs(data.mTyreRPS[2] * data.mTyreRadius[2])
        rr_speed = abs(data.mTyreRPS[3] * data.mTyreRadius[3])
        
        slip_ratio_rl = (speed - rl_speed) / max(speed, 0.1)
        slip_ratio_rr = (speed - rr_speed) / max(speed, 0.1)
        
        if slip_ratio_rl > LOCKUP_THRES or slip_ratio_rr > LOCKUP_THRES:
             self.add_event("Rear Lockup", "Bremsbalance nach VORNE", "BRAKING", data)
             
    def check_turn_in(self, data):
        # Understeer Entry
        # High Steering Angle but Low Yaw Rate/Rotation?
        # Difficult to measure without good vehicle model.
        # Alternative: Compare Front vs Rear Slip Angles (if available) or Slip Speeds.
        
        # AMS2 provides mTyreSlipSpeed.
        # Understeer: Front Slip >> Rear Slip
        
        slips = [abs(data.mTyreSlipSpeed[i]) for i in range(4)]
        front_slip = (slips[0] + slips[1]) / 2
        rear_slip = (slips[2] + slips[3]) / 2
        
        US_THRES = 1.0 # m/s difference
        
        if front_slip > (rear_slip + US_THRES):
            self.add_event("Understeer Entry", "Stabi (ARB) vorne WEICHER", "TURN_IN", data)
            
        # Oversteer Entry (Lift-off)
        OS_THRES = 1.0
        if rear_slip > (front_slip + OS_THRES):
             self.add_event("Oversteer Entry", "Diff-Coast ERHÖHEN (mehr Sperre)", "TURN_IN", data)

    def check_exit(self, data):
        # Power Oversteer
        # High Throttle + High Rear Slip + Yaw
        throttle = data.mUnfilteredThrottle
        if throttle < 0.5: return # Need power
        
        slips = [abs(data.mTyreSlipSpeed[i]) for i in range(4)]
        front_slip = (slips[0] + slips[1]) / 2
        rear_slip = (slips[2] + slips[3]) / 2
        
        POS_THRES = 1.5 # Needs to be significant
        
        if rear_slip > (front_slip + POS_THRES):
             self.add_event("Power Oversteer", "Diff-Power REDUZIEREN (weniger Sperre)", "EXIT", data)
             
        # Understeer Exit (Pushing wide)
        if front_slip > (rear_slip + POS_THRES):
             self.add_event("Understeer Exit", "Diff-Power ERHÖHEN (mehr Sperre)", "EXIT", data)

    def check_general(self, data):
        # Bottoming
        # Suspension travel at limit?
        pass

    def add_event(self, name, suggestion, phase, data=None):
        # Debounce: Don't spam events.
        # We need a cooldown or "Active" check.
        # Ideally, we log this per Corner.
        # For this prototype: Push to a list if not recently added.
        import time
        now = time.time()
        
        # Key: Name
        last_time = self.active_problems.get(name, 0)
        
        if (now - last_time) > 5.0: # 5 seconds cooldown per event type
            self.active_problems[name] = now
            
            event_data = {
                "time": now,
                "name": name,
                "suggestion": suggestion,
                "phase": phase,
                "x": 0.0, 
                "z": 0.0
            }
            
            if data and hasattr(data, 'mParticipantInfo'):
                 # Get Position
                 idx = data.mViewedParticipantIndex
                 if 0 <= idx < data.mNumParticipants and idx < 64:
                     pos = data.mParticipantInfo[idx].mWorldPosition
                     event_data["x"] = pos[0]
                     event_data["z"] = pos[2]
            
            self.events.append(event_data)
            print(f"EVENT DETECTED: {name} ({phase}) -> {suggestion}")

    def get_analysis_summary(self):
        # Aggregate events
        summary = {}
        for e in self.events:
            n = e['name']
            if n not in summary:
                summary[n] = {'count': 0, 'suggestion': e['suggestion']}
            summary[n]['count'] += 1
            
        return {'summary': summary, 'events': self.events}
    
    def reset(self):
        self.events = []
        self.active_problems = {}
