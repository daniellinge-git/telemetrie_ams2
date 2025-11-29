import unittest
from ams2_tyre_analyzer import TyreAnalyzer
import time

class MockData:
    def __init__(self):
        self.mGameState = 2
        self.mPitMode = 0
        self.mSpeed = 20.0 # m/s
        self.mTyreTemp = [0.0]*4
        self.mTyreTempLeft = [0.0]*4
        self.mTyreTempCenter = [0.0]*4
        self.mTyreTempRight = [0.0]*4

class TestTyreAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = TyreAnalyzer()
        # Speed up history for testing
        self.analyzer.history_duration = 2 
        self.analyzer.sample_rate = 10.0 # 10Hz sampling for test
        
    def feed_data(self, temp, duration, spread=0, laps=5):
        # spread > 0 means center is hotter
        data = MockData()
        steps = int(duration * 10) + 5
        
        for _ in range(steps):
            data.mTyreTemp = [temp]*4
            data.mTyreTempCenter = [temp + spread]*4
            data.mTyreTempLeft = [temp - spread]*4
            data.mTyreTempRight = [temp - spread]*4
            
            self.analyzer.update(data, laps_completed=laps)
            time.sleep(0.1) # Simulate time passing

    def test_cold_tyres(self):
        print("\nTesting Cold Tyres...")
        self.feed_data(80.0, 3.0) # 3 seconds of 80C
        
        status = self.analyzer.get_status()
        print(f"Status: {status}")
        self.assertIn("stabil", status)
        
        analysis = self.analyzer.get_analysis()
        self.assertIsNotNone(analysis)
        print(f"Analysis FL: {analysis['FL']}")
        self.assertEqual(analysis['FL']['status'], "Zu KALT")
        self.assertIn("VERRINGERN", analysis['FL']['action'])

    def test_hot_tyres(self):
        print("\nTesting Hot Tyres...")
        self.analyzer.reset()
        self.feed_data(95.0, 3.0)
        
        analysis = self.analyzer.get_analysis()
        self.assertIsNotNone(analysis)
        print(f"Analysis FL: {analysis['FL']}")
        self.assertEqual(analysis['FL']['status'], "Zu HEISS")
        self.assertIn("ERHÖHEN", analysis['FL']['action'])

    def test_ok_tyres(self):
        print("\nTesting OK Tyres...")
        self.analyzer.reset()
        self.feed_data(88.0, 3.0)
        
        analysis = self.analyzer.get_analysis()
        self.assertIsNotNone(analysis)
        print(f"Analysis FL: {analysis['FL']}")
        self.assertEqual(analysis['FL']['status'], "OK")

    def test_center_hot(self):
        print("\nTesting Center Hot (Overpressure)...")
        self.analyzer.reset()
        # Avg 88, Center +4 (92), Edges -4 (84)
        self.feed_data(88.0, 3.0, spread=4.0)
        
        analysis = self.analyzer.get_analysis()
        self.assertIsNotNone(analysis)
        print(f"Analysis FL: {analysis['FL']}")
        self.assertEqual(analysis['FL']['status'], "OK")
        self.assertIn("Mitte heiß", analysis['FL']['details'])

    def test_camber_front_ok(self):
        print("\nTesting Camber Front OK...")
        self.analyzer.reset()
        # Front Left: Inner (Right side of tyre) should be ~7C hotter than Outer (Left side)
        # Temp = 88, Inner = 91.5, Outer = 84.5 (Delta = 7.0)
        
        data = MockData()
        steps = 35 # > 3s
        
        for _ in range(steps):
            # FL
            data.mTyreTemp[0] = 88.0
            data.mTyreTempRight[0] = 91.5 # Inner for FL
            data.mTyreTempLeft[0] = 84.5  # Outer for FL
            data.mTyreTempCenter[0] = 88.0
            
            self.analyzer.update(data)
            time.sleep(0.1)
            
        analysis = self.analyzer.get_analysis()
        self.assertIsNotNone(analysis)
        print(f"Analysis FL: {analysis['FL']}")
        self.assertEqual(analysis['FL']['camber_action'], "Sturz OK")

    def test_camber_front_need_more_negative(self):
        print("\nTesting Camber Front Need More Negative...")
        self.analyzer.reset()
        # Front Left: Inner only 2C hotter (Delta = 2.0, Target 7.0)
        # Inner = 89, Outer = 87
        
        data = MockData()
        steps = 35
        
        for _ in range(steps):
            data.mTyreTemp[0] = 88.0
            data.mTyreTempRight[0] = 89.0 # Inner
            data.mTyreTempLeft[0] = 87.0  # Outer
            data.mTyreTempCenter[0] = 88.0
            
            self.analyzer.update(data)
            time.sleep(0.1)
            
        analysis = self.analyzer.get_analysis()
        print(f"Analysis FL: {analysis['FL']}")
        self.assertIn("VERRINGERN", analysis['FL']['camber_action']) # More negative

    def test_stability_states(self):
        print("\nTesting Stability States...")
        self.analyzer.reset()
        
        # 1. Gathering Phase (Laps < 2)
        data = MockData()
        self.analyzer.update(data, laps_completed=0)
        status = self.analyzer.get_status()
        print(f"Status (Lap 0): {status}")
        self.assertIn("Sammle Daten", status)
        
        self.analyzer.update(data, laps_completed=1)
        status = self.analyzer.get_status()
        print(f"Status (Lap 1): {status}")
        self.assertIn("Sammle Daten", status)
        
        # 2. Checking Phase (Lap 2, but unstable data)
        # Simulate unstable data by alternating temps
        for i in range(20):
            data.mTyreTemp = [80.0 + (i%5)]*4 # 80, 81, 82, 83, 84...
            self.analyzer.update(data, laps_completed=2)
            time.sleep(0.1)
            
        status = self.analyzer.get_status()
        print(f"Status (Lap 2, Unstable): {status}")
        self.assertIn("Noch eine Runde", status)
        
        # 3. Stable Phase
        # Feed stable data
        for _ in range(40):
            data.mTyreTemp = [88.0]*4
            self.analyzer.update(data, laps_completed=3)
            time.sleep(0.1)
            
        status = self.analyzer.get_status()
        print(f"Status (Lap 3, Stable): {status}")
        self.assertIn("Bitte in die Box", status)
        
        # Check if analysis is available
        analysis = self.analyzer.get_analysis()
        self.assertIsNotNone(analysis)

    def test_reset_stability(self):
        print("\nTesting Reset Stability...")
        self.analyzer.reset()
        
        # Drive 2 laps -> Check
        data = MockData()
        self.analyzer.update(data, laps_completed=0) # Start lap = 0
        self.analyzer.update(data, laps_completed=2) # 2 laps driven
        self.assertEqual(self.analyzer.current_state, self.analyzer.STATE_CHECKING)
        
        # Reset (e.g. Pit Stop)
        print("Resetting...")
        self.analyzer.reset()
        self.assertEqual(self.analyzer.current_state, self.analyzer.STATE_GATHERING)
        
        # Still lap 2 in game, but should be lap 0 for analyzer
        self.analyzer.update(data, laps_completed=2) 
        status = self.analyzer.get_status()
        print(f"Status (Lap 2, Reset): {status}")
        self.assertIn("Runde 0/2", status)
        
        # Drive 2 more laps (Lap 4)
        self.analyzer.update(data, laps_completed=4)
        status = self.analyzer.get_status()
        print(f"Status (Lap 4): {status}")
        # Should be checking now
        self.assertEqual(self.analyzer.current_state, self.analyzer.STATE_CHECKING)

if __name__ == '__main__':
    unittest.main()
