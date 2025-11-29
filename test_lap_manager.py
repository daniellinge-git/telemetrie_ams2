import unittest
import os
from ams2_lap_manager import LapTimeManager

class TestLapTimeManager(unittest.TestCase):
    def setUp(self):
        self.filename = "test_laps.csv"
        if os.path.exists(self.filename):
            os.remove(self.filename)
        self.manager = LapTimeManager(self.filename)

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def test_save_and_load(self):
        # Save new record
        is_new = self.manager.save_best_lap("CarA", "TrackA", 90.5)
        self.assertTrue(is_new)
        
        # Verify load
        record = self.manager.get_best_lap("CarA", "TrackA")
        self.assertIsNotNone(record)
        self.assertEqual(record[0], 90.5)
        
        # Slower lap - should not update
        is_new = self.manager.save_best_lap("CarA", "TrackA", 91.0)
        self.assertFalse(is_new)
        record = self.manager.get_best_lap("CarA", "TrackA")
        self.assertEqual(record[0], 90.5)
        
        # Faster lap - should update
        is_new = self.manager.save_best_lap("CarA", "TrackA", 89.0)
        self.assertTrue(is_new)
        record = self.manager.get_best_lap("CarA", "TrackA")
        self.assertEqual(record[0], 89.0)

    def test_persistence(self):
        self.manager.save_best_lap("CarB", "TrackB", 100.0)
        
        # New instance, reload from file
        manager2 = LapTimeManager(self.filename)
        record = manager2.get_best_lap("CarB", "TrackB")
        self.assertIsNotNone(record)
        self.assertEqual(record[0], 100.0)

if __name__ == '__main__':
    unittest.main()
