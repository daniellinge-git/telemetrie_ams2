class FuelMonitor:
    def __init__(self):
        self.fuel_history = [] # List of fuel used per lap
        self.last_lap_fuel = -1.0
        self.current_lap = -1
        self.fuel_capacity = 0.0
        
    def update(self, data):
        if data.mGameState != 2: return # Only track when playing
        
        self.fuel_capacity = data.mFuelCapacity
        current_fuel = data.mFuelLevel * data.mFuelCapacity # mFuelLevel is 0.0-1.0 usually? Or Liters?
        # AMS2 mFuelLevel is usually absolute liters in PC2/AMS2 API?
        # Let's check structs. mFuelLevel is float. mFuelCapacity is float.
        # Usually mFuelLevel is ratio (0-1) and Capacity is Liters.
        # BUT in some docs mFuelLevel is Liters.
        # Let's assume mFuelLevel is Liters for now based on typical usage, 
        # but if it's <= 1.0 and capacity is > 1.0, it's a ratio.
        
        # Safe check:
        if data.mFuelCapacity > 0:
             if data.mFuelLevel <= 1.0 and data.mFuelCapacity > 10.0:
                 # It's likely a ratio
                 current_fuel = data.mFuelLevel * data.mFuelCapacity
             else:
                 # It's likely liters
                 current_fuel = data.mFuelLevel
        else:
             current_fuel = data.mFuelLevel
             
        # Lap Change Detection
        # We need to rely on the main app to tell us when a lap finished, 
        # OR we track it ourselves.
        # Let's track it ourselves via participant info
        if 0 <= data.mViewedParticipantIndex < data.mNumParticipants:
            lap = data.mParticipantInfo[data.mViewedParticipantIndex].mCurrentLap
            
            if self.current_lap == -1:
                self.current_lap = lap
                self.last_lap_fuel = current_fuel
                return
                
            if lap > self.current_lap:
                # Lap finished
                fuel_used = self.last_lap_fuel - current_fuel
                if fuel_used > 0:
                    self.fuel_history.append(fuel_used)
                    # Keep last 5 laps
                    if len(self.fuel_history) > 5:
                        self.fuel_history.pop(0)
                
                self.current_lap = lap
                self.last_lap_fuel = current_fuel
            else:
                # Same lap, just update last fuel if we refueled?
                # If fuel went UP, we refueled. Reset last_lap_fuel
                if current_fuel > self.last_lap_fuel + 1.0: # +1 Liter tolerance
                    self.last_lap_fuel = current_fuel
                    self.fuel_history = [] # Reset history on refuel? Maybe not.
                    
    def get_status(self, current_fuel_level, capacity):
        # Handle unit conversion if needed (same logic as update)
        current_liters = current_fuel_level
        if capacity > 0 and current_fuel_level <= 1.0 and capacity > 10.0:
            current_liters = current_fuel_level * capacity
            
        avg_consumption = 0.0
        if self.fuel_history:
            avg_consumption = sum(self.fuel_history) / len(self.fuel_history)
            
        remaining_laps = 0.0
        if avg_consumption > 0:
            remaining_laps = current_liters / avg_consumption
            
        return {
            'liters': current_liters,
            'per_lap': avg_consumption,
            'remaining_laps': remaining_laps
        }
