class SteeringAnalyzer:
    def __init__(self):
        self.max_steering_per_lap = 0.0
        self.current_lap = -1
        self.recommendation = None
        self.last_recommendation = None

    def update(self, data, current_lap):
        # Check if we are in a new lap
        if current_lap != self.current_lap:
            # Analyze previous lap if it wasn't the first one
            if self.current_lap != -1:
                self._analyze_lap()
            
            # Reset for new lap
            self.current_lap = current_lap
            self.max_steering_per_lap = 0.0

        # Track max steering input (absolute value)
        # mSteering is usually -1.0 to 1.0
        steering_abs = abs(data.mSteering)
        if steering_abs > self.max_steering_per_lap:
            self.max_steering_per_lap = steering_abs

    def _analyze_lap(self):
        # Logic:
        # If max steering is very high (> 0.95), we are hitting the lock -> Increase Lock (make it more sensitive/more range? No, wait)
        # "Ein höherer Wert erhöht den Bewegungsgrad und macht die Lenkung reaktionsfreudiger, da für denselben Winkel weniger gedreht werden muss."
        # If we are hitting the physical lock (1.0), it means we needed MORE steering but couldn't turn the wheel enough? 
        # Or does it mean the car didn't turn enough?
        
        # Requirement: "Die engste Kurve auf der Strecke muss mit dem eingestellten Lenkeinschlag durchfahren werden können."
        # If we hit 100% steering, we might be struggling to turn.
        # If we only use 50% steering, we are not using the full resolution.
        
        # Let's assume:
        # > 95% usage: You are hitting the stops. You might need MORE steering ratio (higher lock value) to get more wheels turn for same input?
        # Actually, "Steering Lock" in setup usually means the maximum angle the wheels can turn.
        # If I hit 100% on my wheel, and the car turns enough, it's fine.
        # But if I have to cross my arms, maybe I want a faster ratio.
        
        # Lastenheft says:
        # "Ein höherer Wert erhöht den Bewegungsgrad und macht die Lenkung reaktionsfreudiger" (Higher Value = Faster Steering / More Angle per input)
        # "Ein niedrigerer Wert verringert den Bewegungsgrad" (Lower Value = Slower Steering)
        
        # So:
        # If I am hitting > 95% (Full Lock), maybe I want it to be MORE responsive so I don't have to turn as much?
        # OR, if I am hitting full lock, it means I am using the full range.
        
        # Let's stick to a simple heuristic:
        # If max_steering < 0.60 (60%): You are not turning the wheel much. The steering is very sensitive. 
        # You might want to LOWER the lock to make it smoother/less twitchy? 
        # "Ziel ist möglichst ideale Reaktionsfreudigkeit."
        
        # If max_steering > 0.98: You are hitting the stops. 
        # Recommendation: "Lenkeinschlag ERHÖHEN (Reaktionsfreudiger)" -> So you don't have to hit the stops?
        
        if self.max_steering_per_lap > 0.98:
            self.recommendation = "Lenkeinschlag ERHÖHEN (Mehr Winkel/Reaktionsfreudiger)"
        elif self.max_steering_per_lap < 0.60:
            self.recommendation = "Lenkeinschlag VERRINGERN (Weniger Winkel/Ruhiger)"
        else:
            self.recommendation = "Lenkeinschlag OK"
            
        self.last_recommendation = self.recommendation

    def get_recommendation(self):
        return self.last_recommendation
