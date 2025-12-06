class FuelMonitor:
    def __init__(self):
        self.fuel_history = [] # List of fuel used per lap
        self.last_lap_fuel = -1.0
        self.current_lap = -1
        self.fuel_capacity = 0.0
        
    def update(self, data):
        if data.mGameState != 2: return # Only track when playing
        
        self.fuel_capacity = data.mFuelCapacity
        current_fuel = 0.0
        
        # Improved Fuel Logic (v1.1)
        # mFuelLevel is typically a ratio (0.0 - 1.0)
        # mFuelCapacity is typically in Liters
        
        if data.mFuelCapacity > 0:
             # If capacity is known, we can be smarter
             # v1.1 Fix: Assume mFuelLevel is LITERS if it's > 1.0 OR if we are just careful.
             # Actually, AMS2 Shared Memory docs say mFuelLevel is "Fuel level (0..1)". 
             # BUT users report it acting weirdly. 
             # Let's try to assume it is Liter if it matches Capacity scale, otherwise Ratio.
             
             if data.mFuelLevel > 1.0:
                  # If > 1.0, it MUST be Liters
                  current_fuel = data.mFuelLevel
             elif data.mFuelLevel <= 1.0:
                  # It COULD be Liters (running dry) or Ratio.
                  # If Capacity is 100L, 1.0L is very low. 1.0 Ratio is Full.
                  # Logic: If mFuelValue * Capacity == mFuelValue, then mFuelValue is Liters? No.
                  
                  # Safer approach:
                  # If we believe it is Ratio:
                  fuel_as_ratio = data.mFuelLevel * data.mFuelCapacity
                  
                  # How to distinguish 0.5 Liters from 50% (0.5 Ratio)?
                  # We can't easily. But 0.5L is basically empty. 
                  # Most likely it IS Ratio (0.0-1.0).
                  # The bug reported: "Verbrauch nicht korrekt" might be due to Avg Consumption calc.
                  
                  current_fuel = fuel_as_ratio
             else:
                  current_fuel = data.mFuelLevel
        else:
             # Fallback if capacity is 0 (shouldn't happen usually)
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
