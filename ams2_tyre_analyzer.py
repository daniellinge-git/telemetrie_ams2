import statistics
import time

class TyreAnalyzer:
    def __init__(self):
        self.history_duration = 90 # seconds to look back for stability (approx 1.5 laps)
        self.sample_rate = 1.0 # Hz
        
        self.last_game_time = -1.0
        self.internal_time = 0.0
        self.last_sample_internal_time = -1.0
        
        # History: [FL, FR, RL, RR]
        # Each: list of dicts with keys: time, avg, l, c, r
        self.history = [[], [], [], []]
        self.current_temps = [0.0, 0.0, 0.0, 0.0]
        
        # Updated Targets based on Lastenheft
        self.target_min = 75.0
        self.target_max = 85.0
        
        self.is_stable = [False] * 4
        self.stability_threshold = 3.0 # degrees Celsius variation allowed in history window
        
        self.tyre_names = ["FL", "FR", "RL", "RR"]

    def update(self, data):
        # Always capture current raw temps for live dashboard (even in menu/pits)
        self.current_temps = [
            data.mTyreTemp[0], data.mTyreTemp[1], data.mTyreTemp[2], data.mTyreTemp[3],
        ]
        
        # Robust Time Tracking
        # We accumulate delta_time to create a monotonic internal_time
        # This handles Pauses (dt=0) and Time Wraps/Resets (dt<0) gracefully
        
        current_game_time = data.mCurrentTime
        
        if self.last_game_time < 0:
            self.last_game_time = current_game_time
            return # Wait for next frame to have a delta
            
        dt = current_game_time - self.last_game_time
        self.last_game_time = current_game_time
        
        # If dt is negative (time wrap/reset), we ignore it (dt=0)
        if dt < 0: dt = 0
            
        # Check if valid driving state (GameState 2 = Playing)
        # Note: We still only UPDATE HISTORY in Playing mode
        if data.mGameState != 2: 
            return
            
        # Check if moving and not in pits
        # If we are NOT moving fast enough, we do NOT advance internal_time.
        # This "pauses" the history window so we don't lose data while standing still or driving slow.
        if data.mPitMode != 0 or data.mSpeed < 5.0:
            return

        # Only advance internal time if we are actually sampling/driving
        self.internal_time += dt
        
        # Only sample at defined rate
        if self.last_sample_internal_time < 0 or (self.internal_time - self.last_sample_internal_time) >= (1.0 / self.sample_rate):
             self.last_sample_internal_time = self.internal_time
        else:
             return

        # Collect Data (History)
        for i in range(4):
            t_avg = data.mTyreTemp[i]
            t_l = data.mTyreTempLeft[i]
            t_c = data.mTyreTempCenter[i]
            t_r = data.mTyreTempRight[i]
            
            self.history[i].append({
                'time': self.internal_time,
                'avg': t_avg,
                'l': t_l,
                'c': t_c,
                'r': t_r
            })
            
            # Limit history by COUNT, not time check (prevents shrinking between samples)
            # We want history_duration seconds at sample_rate Hz
            max_samples = int(self.history_duration * self.sample_rate)
            while len(self.history[i]) > max_samples:
                self.history[i].pop(0)
                
            self._check_stability(i)
            
    def _check_stability(self, i):
        if not self.history[i]:
            self.is_stable[i] = False
            return

        temps = [h['avg'] for h in self.history[i]]
        t_min = min(temps)
        t_max = max(temps)
        
        if (t_max - t_min) < self.stability_threshold:
            self.is_stable[i] = True
        else:
            self.is_stable[i] = False

    def get_analysis(self):
        # Return analysis regardless of stability, caller decides when to show it
        results = {}
        for i in range(4):
            # Fallback to current live temp if history empty
            avg_t = self.current_temps[i]
            
            # Defaults if no history
            status = "Waiting..."
            action = "-"
            reason = ""
            color = "white" # Neutral
            details = ""
            camber_action = "-"
            camber_reason = ""
            temp_inner = 0.0
            temp_outer = 0.0
            
            # If we have history, do the real analysis
            if self.history[i]:
                # Calculate averages over the history
                avg_t = statistics.mean([h['avg'] for h in self.history[i]])
                avg_l = statistics.mean([h['l'] for h in self.history[i]])
                avg_c = statistics.mean([h['c'] for h in self.history[i]])
                avg_r = statistics.mean([h['r'] for h in self.history[i]])
                
                # --- Pressure Analysis ---
                status = "OK"
                action = "Druck OK"
                reason = "Temperatur im Zielbereich"
                color = "green"
                
                if avg_t < self.target_min:
                    status = "Zu KALT"
                    action = "Druck VERRINGERN (-)"
                    reason = f"Temp ({avg_t:.1f}°C) zu niedrig (< {self.target_min}°C). Weniger Druck erhöht die Walkarbeit & Temperatur."
                    color = "blue"
                elif avg_t > self.target_max:
                    status = "Zu HEISS"
                    action = "Druck ERHÖHEN (+)"
                    reason = f"Temp ({avg_t:.1f}°C) zu hoch (> {self.target_max}°C). Mehr Druck verringert die Walkarbeit."
                    color = "red"
                
                # Check spread (Center vs Edges)
                edges_avg = (avg_l + avg_r) / 2
                spread_msg = ""
                
                if avg_c > (edges_avg + 3.0): 
                    spread_msg = " (Mitte heiß -> Überdruck?)"
                elif avg_c < (edges_avg - 3.0): 
                    spread_msg = " (Mitte kalt -> Unterdruck?)"
                    
                details = spread_msg
                
                # --- Camber Analysis ---
                is_left_side = (i == 0 or i == 2)
                is_front = (i == 0 or i == 1)
                
                if is_left_side:
                    temp_inner = avg_r
                    temp_outer = avg_l
                else:
                    temp_inner = avg_l
                    temp_outer = avg_r
                    
                delta = temp_inner - temp_outer
                
                camber_action = ""
                camber_reason = ""
                
                if is_front:
                    target_delta = 7.0
                    tolerance = 1.5
                    if delta < (target_delta - tolerance):
                        camber_action = "Sturz VERRINGERN (negativer)" 
                        camber_reason = f"Delta Innen-Außen ({delta:.1f}°C) zu klein (Ziel ~{target_delta}°C). Reifen liegt zu flach auf."
                    elif delta > (target_delta + tolerance):
                        camber_action = "Sturz ERHÖHEN (positiver)"
                        camber_reason = f"Delta Innen-Außen ({delta:.1f}°C) zu groß (Ziel ~{target_delta}°C). Reifen steht zu steil."
                else:
                    target_delta_min = 3.0
                    target_delta_max = 5.0
                    if delta < target_delta_min:
                        camber_action = "Sturz VERRINGERN (negativer)"
                        camber_reason = f"Delta Innen-Außen ({delta:.1f}°C) < {target_delta_min}°C. Zu wenig Sturz für Hinterachse."
                    elif delta > target_delta_max:
                        camber_action = "Sturz ERHÖHEN (positiver)"
                        camber_reason = f"Delta Innen-Außen ({delta:.1f}°C) > {target_delta_max}°C. Zu viel Sturz für Hinterachse."
                
                if not camber_action:
                    camber_action = "Sturz OK"
                    camber_reason = "Sturz-Temperaturverteilung optimal."

            results[self.tyre_names[i]] = {
                'temp': avg_t,
                'status': status,
                'action': action,
                'reason': reason,
                'details': details,
                'camber_action': camber_action,
                'camber_reason': camber_reason,
                'temp_inner': temp_inner,
                'temp_outer': temp_outer,
                'color': color
            }
            
        return results

    def reset(self):
        self.history = [[], [], [], []]
        self.is_stable = [False] * 4
        self.last_sample_internal_time = -1.0
        self.current_temps = [0.0, 0.0, 0.0, 0.0]
        # Do NOT reset targets or internal_time (monotonic)
        print("DEBUG: TyreAnalyzer RESET executed.")
