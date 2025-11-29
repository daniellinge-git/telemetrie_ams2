import csv
import os
import datetime

class LapTimeManager:
    def __init__(self, filename="best_laps.csv"):
        self.filename = filename
        self.best_laps = {} # Key: (car, track), Value: (time, date)
        self._load_laps()

    def _load_laps(self):
        if not os.path.exists(self.filename):
            return

        try:
            with open(self.filename, mode='r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    key = (row['Car'], row['Track'])
                    try:
                        time_val = float(row['Time'])
                        self.best_laps[key] = (time_val, row['Date'])
                    except ValueError:
                        continue
        except Exception as e:
            print(f"Error loading laps: {e}")

    def get_best_lap(self, car, track):
        return self.best_laps.get((car, track))

    def save_best_lap(self, car, track, lap_time):
        current_best = self.get_best_lap(car, track)
        
        # If we have a faster time or no time yet, save it
        if current_best is None or lap_time < current_best[0]:
            date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.best_laps[(car, track)] = (lap_time, date_str)
            self._write_to_csv()
            return True # New record
        return False

    def _write_to_csv(self):
        try:
            with open(self.filename, mode='w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Car', 'Track', 'Date', 'Time']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for (car, track), (time_val, date_str) in self.best_laps.items():
                    writer.writerow({
                        'Car': car,
                        'Track': track,
                        'Date': date_str,
                        'Time': f"{time_val:.3f}"
                    })
        except Exception as e:
            print(f"Error saving laps: {e}")
