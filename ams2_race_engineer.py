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
        if data.mGameState != 2:
            # If we are already in BOX mode, do NOT reset, so the UI can show the analysis!
            if self.state == self.STATE_BOX:
                return
            
            # Otherwise, reset
            self.state = self.STATE_WAITING
            self.message = "Warte auf Start..."
            return

        # If we just started driving (or reset)
        if self.state == self.STATE_WAITING:
            self.state = self.STATE_GATHERING
            self.start_lap = laps_completed
            self.tyre_analyzer.reset()
            
        laps_driven = laps_completed - self.start_lap
        
        if self.state == self.STATE_GATHERING:
            if laps_driven >= self.min_laps:
                self.state = self.STATE_CHECKING
            else:
                self.message = f"Sammle Daten (Runde {laps_driven}/{self.min_laps})..."
                
        if self.state == self.STATE_CHECKING:
            # Check Stability
            if self.tyre_analyzer.are_all_stable():
                self.state = self.STATE_BOX
                self.message = "Bitte in die Box kommen!"
            else:
                self.message = "Noch eine Runde. Werte zu unkonstant!"
                
        if self.state == self.STATE_BOX:
            self.message = "Bitte in die Box kommen!"
            # If user keeps driving, we stay here.
            # If user goes to pause menu, the main app handles the display.

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
