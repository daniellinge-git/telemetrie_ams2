import unittest
from unittest.mock import MagicMock
from ams2_race_engineer import RaceEngineer
from ams2_fuel_monitor import FuelMonitor
from ams2_structs import SharedMemory

class TestV1_1(unittest.TestCase):
    def test_fuel_monitor_liters(self):
        monitor = FuelMonitor()
        data = SharedMemory()
        data.mGameState = 2
        data.mFuelCapacity = 100.0
        
        # Test 1: Ratio input (0.5 = 50L)
        data.mFuelLevel = 0.5
        monitor.update(data)
        # Internal logic keeps track of consumption, but we want to check interpreted level
        status = monitor.get_status(data.mFuelLevel, data.mFuelCapacity)
        # With my fix, if <= 1.0, it treats as Ratio (0.5 * 100 = 50L)
        self.assertAlmostEqual(status['liters'], 50.0)

        # Test 2: Liter input (>1.0)
        data.mFuelLevel = 60.0 # 60 Liters
        monitor.update(data)
        status = monitor.get_status(data.mFuelLevel, data.mFuelCapacity)
        self.assertAlmostEqual(status['liters'], 60.0)
        
    def test_handling_balance(self):
        eng = RaceEngineer()
        data = SharedMemory()
        data.mGameState = 2
        data.mSpeed = 50.0 # Fast enough
        
        # Test Understeer: Front Slip > Rear Slip
        # Slip speeds (m/s)
        data.mTyreSlipSpeed[0] = 2.0 # FL
        data.mTyreSlipSpeed[1] = 2.0 # FR
        data.mTyreSlipSpeed[2] = 0.5 # RL
        data.mTyreSlipSpeed[3] = 0.5 # RR
        
        eng.check_handling_balance(data)
        self.assertEqual(eng.handling_status, "UNDERSTEER")
        
        # Test Oversteer: Rear Slip > Front Slip
        data.mTyreSlipSpeed[0] = 0.5
        data.mTyreSlipSpeed[1] = 0.5
        data.mTyreSlipSpeed[2] = 2.0
        data.mTyreSlipSpeed[3] = 2.0
        
        eng.check_handling_balance(data)
        self.assertEqual(eng.handling_status, "OVERSTEER")
        
    def test_session_type(self):
        eng = RaceEngineer()
        data = SharedMemory()
        data.mGameState = 2
        data.mSessionState = 5 # Race
        eng.driven_distance_stint = 15.0 # > 10.0 threshold
        eng.state = "GATHERING"
        
        eng.update(data)
        
        # Should stay in GATHERING or just NOT trigger BOX
        self.assertNotEqual(eng.state, "BOX")
        self.assertIn("RACE", eng.message)
        
    def test_distance_trigger(self):
        eng = RaceEngineer()
        data = SharedMemory()
        data.mGameState = 2
        data.mSessionState = 1 # Practice
        
        # Reset state to avoid "WAITING" -> "GATHERING" reset logic
        eng.state = "GATHERING"
        eng.stint_start_odometer = 100.0
        data.mOdometerKM = 105.0 # 5km driven
        
        eng.update(data)
        self.assertNotEqual(eng.state, "BOX")
        
        data.mOdometerKM = 112.0 # 12km driven (>10)
        
        # Populate Tyre History to ensure Analysis returns results
        # We need "Zu HEISS" (Too Hot) to trigger change
        # avg > 85
        hot_tyre = [{'time': 0, 'avg': 100, 'l': 100, 'c': 100, 'r': 100}]
        eng.tyre_analyzer.history = [hot_tyre, hot_tyre, hot_tyre, hot_tyre]
        
        # NOTE: logic requires at least 80% history filled for stability?
        # ams2_tyre_analyzer: len(history) < (90 * 1.0 * 0.8) -> Unstable.
        # But get_analysis() returns results REGARDLESS of stability, 
        # checking "if not self.history[i]: continue".
        # So having 1 sample is enough to get a result.
        
        eng.update(data)
        
        # Debug print if it fails
        if eng.state != "BOX":
            print(f"State: {eng.state}")
            print(f"Message: {eng.message}")
            print(f"Analysis: {eng.get_analysis()}")
            
        self.assertEqual(eng.state, "BOX")


if __name__ == '__main__':
    unittest.main()
