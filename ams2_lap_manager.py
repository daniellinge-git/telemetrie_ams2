import csv
import os
import datetime

class LapTimeManager:
    def __init__(self, filename="best_laps.csv"):
        self.filename = filename
        self.best_laps = {} # Key: (car, track), Value: {'time': float, 'date': str, 'session': str}
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
                        # Handle legacy CSVs without Session column
                        session = row.get('Session', 'Unknown')
                        self.best_laps[key] = {
                            'time': time_val, 
                            'date': row['Date'],
                            'session': session
                        }
                    except ValueError:
                        continue
        except Exception as e:
            print(f"Error loading laps: {e}")

    def get_best_lap(self, car, track):
        return self.best_laps.get((car, track))

    def save_best_lap(self, car, track, lap_time, session_type="Unknown"):
        current_best = self.get_best_lap(car, track)
        
        # If we have a faster time or no time yet, save it
        if current_best is None or lap_time < current_best['time']:
            date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.best_laps[(car, track)] = {
                'time': lap_time, 
                'date': date_str,
                'session': session_type
            }
            self._write_to_csv()
            return True # New record
        return False

    def _write_to_csv(self):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with open(self.filename, mode='w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['Car', 'Track', 'Date', 'Time', 'Session']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                    writer.writeheader()
                    for (car, track), data in self.best_laps.items():
                        writer.writerow({
                            'Car': car,
                            'Track': track,
                            'Date': data['date'],
                            'Time': f"{data['time']:.3f}",
                            'Session': data['session']
                        })
                return # Success
            except PermissionError:
                if attempt < max_retries - 1:
                    print(f"Permission denied saving CSV. Retrying in 1s... ({attempt+1}/{max_retries})")
                    import time
                    time.sleep(1)
                else:
                    print(f"ERROR: Could not save '{self.filename}'. Is it open in Excel? Please close it.")
            except Exception as e:
                print(f"Error saving laps: {e}")
                break
