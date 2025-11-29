class WearMonitor:
    def __init__(self):
        self.wear_history = [[], [], [], []] # FL, FR, RL, RR
        self.last_wear = [0.0] * 4
        self.current_lap = -1
        self.tyre_names = ["FL", "FR", "RL", "RR"]
        
    def update(self, data):
        if data.mGameState != 2: return
        
        # Check Lap Change
        if 0 <= data.mViewedParticipantIndex < data.mNumParticipants:
            lap = data.mParticipantInfo[data.mViewedParticipantIndex].mCurrentLap
            
            if self.current_lap == -1:
                self.current_lap = lap
                for i in range(4):
                    self.last_wear[i] = data.mTyreWear[i]
                return
                
            if lap > self.current_lap:
                # Lap finished
                for i in range(4):
                    current = data.mTyreWear[i]
                    # Wear increases? (0.0 -> 1.0)
                    # If current > last, wear increased.
                    delta = current - self.last_wear[i]
                    
                    # Handle tire change (wear goes down)
                    if current < self.last_wear[i]:
                        delta = 0 # Reset or ignore
                        
                    if delta > 0:
                        self.wear_history[i].append(delta)
                        if len(self.wear_history[i]) > 5:
                            self.wear_history[i].pop(0)
                            
                    self.last_wear[i] = current
                
                self.current_lap = lap
                
    def get_status(self, current_wear):
        # current_wear is list of 4 floats
        status = {}
        for i in range(4):
            avg_wear_per_lap = 0.0
            if self.wear_history[i]:
                avg_wear_per_lap = sum(self.wear_history[i]) / len(self.wear_history[i])
            
            # Remaining life
            # Assume 1.0 is dead.
            # Remaining wear budget = 1.0 - current
            # Or maybe we want to stop at 0.9?
            # Let's assume 1.0 is max wear.
            remaining_life = 1.0 - current_wear[i]
            remaining_laps = 999.0
            
            if avg_wear_per_lap > 0.0001: # Avoid div by zero
                remaining_laps = remaining_life / avg_wear_per_lap
                
            status[self.tyre_names[i]] = {
                'wear_percent': current_wear[i] * 100.0,
                'per_lap': avg_wear_per_lap * 100.0,
                'remaining_laps': remaining_laps
            }
        return status
