import statistics
import time

class TyreAnalyzer:
    def __init__(self):
        self.history_duration = 30 # seconds to look back for stability
        self.sample_rate = 1.0 # Hz
        self.last_sample_time = 0
        
        # History: [FL, FR, RL, RR]
        # Each: list of dicts with keys: time, avg, l, c, r
        self.history = [[], [], [], []]
        
        self.target_min = 85.0
        self.target_max = 90.0
        
        self.is_stable = [False] * 4
        self.stability_threshold = 3.0 # degrees Celsius variation allowed in history window
        
        self.tyre_names = ["FL", "FR", "RL", "RR"]
        
        # New: Stability State Machine
        self.STATE_GATHERING = "GATHERING" # First 2 laps
        self.STATE_CHECKING = "CHECKING"   # Analyzing variance
        self.STATE_STABLE = "STABLE"       # Ready for pit
        self.STATE_UNSTABLE = "UNSTABLE"   # Needs more laps
        
        self.current_state = self.STATE_GATHERING
        self.laps_completed = 0
        self.min_laps_required = 2
        self.start_lap = 0 # Lap count when we started gathering

    def update(self, data, laps_completed):
        current_time = time.time()
        
        # Update lap count
        self.laps_completed = laps_completed
        
        # Initialize start_lap if we just reset
        if self.start_lap == -1:
            self.start_lap = laps_completed
        
        # State Transition: GATHERING -> CHECKING
        # Check if we have driven enough laps SINCE the last reset
        laps_driven_since_reset = self.laps_completed - self.start_lap
        
        if self.current_state == self.STATE_GATHERING and laps_driven_since_reset >= self.min_laps_required:
            self.current_state = self.STATE_CHECKING
        
        # Only sample at defined rate
        if current_time - self.last_sample_time < (1.0 / self.sample_rate):
            return

        self.last_sample_time = current_time
        
        # Check if valid driving state (GameState 2 = Playing)
        if data.mGameState != 2: 
            return
            
        # Check if moving and not in pits
        if data.mPitMode != 0 or data.mSpeed < 5.0:
            if data.mPitMode != 0:
                self.reset()
            return

        # Collect Data
        for i in range(4):
            t_avg = data.mTyreTemp[i]
            t_l = data.mTyreTempLeft[i]
            t_c = data.mTyreTempCenter[i]
            t_r = data.mTyreTempRight[i]
            
            self.history[i].append({
                'time': current_time,
                'avg': t_avg,
                'l': t_l,
                'c': t_c,
                'r': t_r
            })
            
            while self.history[i] and (current_time - self.history[i][0]['time'] > self.history_duration):
                self.history[i].pop(0)
                
            self._check_stability(i)
            
        # Update State based on stability
        if self.current_state == self.STATE_CHECKING:
            if all(self.is_stable):
                self.current_state = self.STATE_STABLE
            else:
                # If we have enough history but still not stable, we might need to stay in checking/unstable
                # For now, let's toggle between CHECKING and UNSTABLE for feedback
                # Actually, let's keep it simple: If in checking phase and not stable -> Unstable
                pass 

    def _check_stability(self, i):
        # Need at least 80% of the history window filled
        if len(self.history[i]) < (self.history_duration * self.sample_rate * 0.8):
            self.is_stable[i] = False
            return
            
        temps = [h['avg'] for h in self.history[i]]
        
        if (max(temps) - min(temps)) < self.stability_threshold:
            self.is_stable[i] = True
        else:
            self.is_stable[i] = False

    def reset(self):
        self.history = [[], [], [], []]
        self.is_stable = [False] * 4
        self.current_state = self.STATE_GATHERING
        self.start_lap = -1 # Will be set on next update
        # Note: We don't reset laps_completed here as that comes from the game

    def get_status_message(self):
        if self.current_state == self.STATE_GATHERING:
            laps_driven = self.laps_completed - self.start_lap if self.start_lap != -1 else 0
            # Ensure we don't show negative numbers
            laps_driven = max(0, laps_driven)
            return f"Sammle Daten (Runde {laps_driven}/{self.min_laps_required})..."
        
        elif self.current_state == self.STATE_CHECKING or self.current_state == self.STATE_UNSTABLE:
            if all(self.is_stable):
                self.current_state = self.STATE_STABLE
                return "Bitte in die Box kommen!"
            else:
                return "Noch eine Runde. Werte zu unkonstant!"
                
        elif self.current_state == self.STATE_STABLE:
            return "Bitte in die Box kommen!"
            
        return "Status unbekannt"

    def get_status(self):
        # Legacy method for compatibility, redirects to new message logic
        return self.get_status_message()

    def get_analysis(self):
        # Only return analysis if we are STABLE
        if self.current_state != self.STATE_STABLE:
            return None
            
        results = {}
        for i in range(4):
            # Calculate averages over the history
            avg_t = statistics.mean([h['avg'] for h in self.history[i]])
            avg_l = statistics.mean([h['l'] for h in self.history[i]])
            avg_c = statistics.mean([h['c'] for h in self.history[i]])
            avg_r = statistics.mean([h['r'] for h in self.history[i]])
            
            # --- Pressure Analysis ---
            status = "OK"
            action = "Druck OK"
            color = "green"
            
            if avg_t < self.target_min:
                status = "Zu KALT"
                action = "Druck VERRINGERN (-)"
                color = "blue"
            elif avg_t > self.target_max:
                status = "Zu HEISS"
                action = "Druck ERHÖHEN (+)"
                color = "red"
            
            # Check spread (Center vs Edges) for pressure fine-tuning
            edges_avg = (avg_l + avg_r) / 2
            spread_msg = ""
            
            if avg_c > (edges_avg + 3.0): 
                spread_msg = " (Mitte heiß -> Überdruck?)"
            elif avg_c < (edges_avg - 3.0): 
                spread_msg = " (Mitte kalt -> Unterdruck?)"
            
            # --- Camber Analysis ---
            # Determine Inner/Outer based on wheel position
            # FL (0) & RL (2): Left side of car -> Inner is Right side of tyre (TempRight), Outer is Left side (TempLeft)
            # FR (1) & RR (3): Right side of car -> Inner is Left side of tyre (TempLeft), Outer is Right side of tyre (TempRight)
            
            is_left_side = (i == 0 or i == 2)
            is_front = (i == 0 or i == 1)
            
            if is_left_side:
                temp_inner = avg_r
                temp_outer = avg_l
            else:
                temp_inner = avg_l
                temp_outer = avg_r
                
            delta = temp_inner - temp_outer
            
            # Target Deltas
            # Front: Inner 7C > Outer
            # Rear: Inner 3-5C > Outer
            
            camber_action = ""
            
            if is_front:
                target_delta = 7.0
                tolerance = 1.5
                if delta < (target_delta - tolerance):
                    # Delta too small (Inner not hot enough) -> Need more negative camber to heat inside
                    camber_action = "Sturz VERRINGERN (negativer)" 
                elif delta > (target_delta + tolerance):
                    # Delta too big (Inner too hot) -> Need less negative camber
                    camber_action = "Sturz ERHÖHEN (positiver)"
            else:
                target_delta_min = 3.0
                target_delta_max = 5.0
                if delta < target_delta_min:
                    camber_action = "Sturz VERRINGERN (negativer)"
                elif delta > target_delta_max:
                    camber_action = "Sturz ERHÖHEN (positiver)"
            
            if not camber_action:
                camber_action = "Sturz OK"

            results[self.tyre_names[i]] = {
                'temp': avg_t,
                'status': status,
                'action': action,
                'details': spread_msg,
                'camber_action': camber_action,
                'temp_inner': temp_inner,
                'temp_outer': temp_outer,
                'color': color
            }
            
        return results
