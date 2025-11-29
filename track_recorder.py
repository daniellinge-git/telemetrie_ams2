import math

class TrackRecorder:
    def __init__(self):
        self.track_data = [] # List of (x, z) tuples
        self.is_recording = False
        self.lap_distance = 0
        self.last_pos = None
        self.tightest_corner = None # (radius, x, z)
        
        # Thresholds
        self.min_dist_update = 2.0 # Meters between points
        
    def reset(self):
        self.track_data = []
        self.is_recording = False
        self.lap_distance = 0
        self.last_pos = None
        self.tightest_corner = None

    def update(self, data):
        # Only record if moving, on track, and NOT in pits
        # mPitMode: 0=None, 1=DrivingIn, 2=InPit, 3=DrivingOut, 4=Garage
        # Also ignore if lap is invalidated (as requested to avoid spins/off-track data)
        if data.mGameState != 2 or data.mSpeed < 1.0 or data.mPitMode != 0 or data.mLapInvalidated:
            return

        x = data.mParticipantInfo[data.mViewedParticipantIndex].mWorldPosition[0]
        z = data.mParticipantInfo[data.mViewedParticipantIndex].mWorldPosition[2]
        speed = data.mSpeed * 3.6 # km/h
        
        current_pos = (x, z, speed)
        
        if self.last_pos is None:
            self.last_pos = current_pos
            self.track_data.append(current_pos)
            return
            
        # Calculate distance from last point
        dist = math.sqrt((x - self.last_pos[0])**2 + (z - self.last_pos[1])**2)
        
        if dist >= self.min_dist_update:
            self.track_data.append(current_pos)
            self.lap_distance += dist
            self.last_pos = current_pos
            
            # Analyze Corner (Simple 3-point radius)
            if len(self.track_data) >= 3:
                self.analyze_corner()

    def analyze_corner(self):
        # Get last 3 points
        p1 = self.track_data[-3]
        p2 = self.track_data[-2]
        p3 = self.track_data[-1]
        
        # Calculate radius of circumcircle
        # Area of triangle = 0.5 * |x1(y2 - y3) + x2(y3 - y1) + x3(y1 - y2)|
        # Radius = (a * b * c) / (4 * Area)
        
        a = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
        b = math.sqrt((p3[0]-p2[0])**2 + (p3[1]-p2[1])**2)
        c = math.sqrt((p3[0]-p1[0])**2 + (p3[1]-p1[1])**2)
        
        area = 0.5 * abs(p1[0]*(p2[1]-p3[1]) + p2[0]*(p3[1]-p1[1]) + p3[0]*(p1[1]-p2[1]))
        
        if area > 0.1: # Avoid division by zero
            radius = (a * b * c) / (4 * area)
            
            # Filter straight lines (large radius)
            if radius < 200: 
                if self.tightest_corner is None or radius < self.tightest_corner[0]:
                    self.tightest_corner = (radius, p2[0], p2[1])

    def get_track_path(self):
        return self.track_data

    def get_tightest_corner(self):
        return self.tightest_corner
