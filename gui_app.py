import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QTabWidget, QPushButton, QCheckBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette

# Placeholder for Matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Backend Imports
from ams2_reader import AMS2Reader
from ams2_race_engineer import RaceEngineer
from track_recorder import TrackRecorder
from ams2_lap_manager import LapTimeManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AMS2 Telemetry Engineer")
        self.setGeometry(100, 100, 800, 600)
        
        # Window Flags: Always on Top
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        
        # Backend Initialization
        self.reader = AMS2Reader()
        self.engineer = RaceEngineer()
        self.recorder = TrackRecorder()
        self.lap_manager = LapTimeManager()
        self.connected = False
        
        # State tracking
        self.last_lap = -1
        
        # Main Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Header / Status Bar
        self.header_layout = QHBoxLayout()
        self.status_label = QLabel("GAME STATE: WAITING...")
        self.status_label.setStyleSheet("font-weight: bold; color: yellow; font-size: 14px;")
        self.header_layout.addWidget(self.status_label)
        
        self.always_on_top_cb = QCheckBox("Always on Top")
        self.always_on_top_cb.setChecked(True)
        self.always_on_top_cb.stateChanged.connect(self.toggle_always_on_top)
        self.header_layout.addWidget(self.always_on_top_cb)
        
        self.layout.addLayout(self.header_layout)
        
        # Tabs
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Tab 1: Session / Engineer
        self.tab_session = QWidget()
        self.setup_session_tab()
        self.tabs.addTab(self.tab_session, "Session & Setup")
        
        # Tab 2: Track Map
        self.tab_track = QWidget()
        self.setup_track_tab()
        self.tabs.addTab(self.tab_track, "Track Map")
        
        # Tab 3: Laps
        self.tab_laps = QWidget()
        self.setup_laps_tab()
        self.tabs.addTab(self.tab_laps, "Lap Times")
        
        # Styling
        self.apply_dark_theme()
        
        # Timer for polling
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(100) # 10Hz

    def setup_session_tab(self):
        layout = QVBoxLayout(self.tab_session)
        
        # Timing Grid
        timing_layout = QVBoxLayout()
        
        # Row 1: Current & Best
        row1 = QHBoxLayout()
        self.lbl_current_lap = QLabel("Current: --:--.---")
        self.lbl_current_lap.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.lbl_best_lap = QLabel("Best: --:--.---")
        self.lbl_best_lap.setStyleSheet("font-size: 18px; font-weight: bold; color: #00ff00;")
        row1.addWidget(self.lbl_current_lap)
        row1.addWidget(self.lbl_best_lap)
        timing_layout.addLayout(row1)
        
        # Row 2: Sectors
        row2 = QHBoxLayout()
        self.lbl_s1 = QLabel("S1: --.---")
        self.lbl_s2 = QLabel("S2: --.---")
        self.lbl_s3 = QLabel("S3: --.---")
        row2.addWidget(self.lbl_s1)
        row2.addWidget(self.lbl_s2)
        row2.addWidget(self.lbl_s3)
        timing_layout.addLayout(row2)
        
        layout.addLayout(timing_layout)
        
        layout.addWidget(QLabel("")) # Spacer
        
        self.engineer_label = QLabel("Race Engineer Feedback")
        self.engineer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #00ff00;")
        layout.addWidget(self.engineer_label)
        
        self.feedback_text = QLabel("Waiting for data...")
        self.feedback_text.setWordWrap(True)
        self.feedback_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.feedback_text.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.feedback_text)
        
        layout.addStretch()

    def setup_track_tab(self):
        layout = QVBoxLayout(self.tab_track)
        
        # Matplotlib Figure
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.figure.patch.set_facecolor('#2b2b2b') # Match dark theme
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#2b2b2b')
        self.ax.tick_params(colors='white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['right'].set_color('white')
        
        layout.addWidget(self.canvas)
        
        self.track_status_label = QLabel("Drive a lap to record track map...")
        layout.addWidget(self.track_status_label)

    def setup_laps_tab(self):
        layout = QVBoxLayout(self.tab_laps)
        
        self.laps_label = QLabel("Session Laps")
        self.laps_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.laps_label)
        
        # Table for laps
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        self.laps_table = QTableWidget()
        self.laps_table.setColumnCount(4) # Added Setup Column
        self.laps_table.setHorizontalHeaderLabels(["Lap", "Time", "Sector 1", "Setup / Notes"]) 
        self.laps_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.laps_table)
        
        # Best Lap Label
        self.best_lap_label = QLabel("Best Lap: --:--.---")
        self.best_lap_label.setStyleSheet("font-weight: bold; color: #00ff00;")
        layout.addWidget(self.best_lap_label)

    def update_session_tab(self, data):
        # Update Timing
        self.lbl_current_lap.setText(f"Current: {self.format_time(data.mCurrentTime)}")
        
        # Best Lap (Session Best)
        # mBestLapTime might be 0 if none yet, or use our manager
        best_time = data.mBestLapTime
        if best_time > 0:
            self.lbl_best_lap.setText(f"Best: {self.format_time(best_time)}")
        
        # Sectors
        # Helper to colorize sector times
        def set_sector_label(label, current, best, prefix):
            if current <= 0:
                label.setText(f"{prefix}: --.---")
                label.setStyleSheet("color: white;")
                return
                
            text = f"{prefix}: {current:.3f}"
            
            # If we have a best time to compare against
            if best > 0:
                if current <= best:
                    # Faster or equal (Green)
                    label.setStyleSheet("color: #00ff00; font-weight: bold;")
                else:
                    # Slower (Red)
                    label.setStyleSheet("color: #ff0000; font-weight: bold;")
            else:
                # No best time yet, just white
                label.setStyleSheet("color: white;")
                
            label.setText(text)

        set_sector_label(self.lbl_s1, data.mCurrentSector1Time, data.mPersonalFastestSector1Time, "S1")
        set_sector_label(self.lbl_s2, data.mCurrentSector2Time, data.mPersonalFastestSector2Time, "S2")
        set_sector_label(self.lbl_s3, data.mCurrentSector3Time, data.mPersonalFastestSector3Time, "S3")

        # Always check for urgent engineer messages first
        msg = self.engineer.get_message()
        
        if data.mGameState == 3: # Pause
            analysis = self.engineer.get_analysis()
            
            # Prio 1: If Engineer wants to Box, show that clearly!
            if "Box" in msg:
                 self.feedback_text.setText(f"<h2 style='color:red'>!!! {msg} !!!</h2><br>Check Setup Recommendations below.")
            
            if analysis['ready']:
                text = self.feedback_text.text() if "Box" in msg else "<b>PAUSE MODE - SETUP ANALYSIS</b><br><br>"
                if "Box" in msg: text += "<br><hr><br>"
                
                # Tyres
                text += "<b>TYRES:</b><br>"
                tyre_info = analysis['tyres']
                for tyre in ["FL", "FR", "RL", "RR"]:
                    if tyre in tyre_info:
                        info = tyre_info[tyre]
                        text += f"{tyre}: {info['temp']:.1f}C - {info['action']}<br>"
                        if info['camber_action']:
                            text += f"&nbsp;&nbsp;-> {info['camber_action']}<br>"
                
                # Steering
                if analysis['steering']:
                    text += f"<br><b>STEERING:</b> {analysis['steering']}<br>"
                
                self.feedback_text.setText(text)
            else:
                # If not ready but we have a message (e.g. "One more lap"), show it
                if msg and msg != "Daten werden gesammelt...":
                    self.feedback_text.setText(f"<b>RACE ENGINEER:</b><br>{msg}<br><br>(Analysis not fully ready yet)")
                else:
                    self.feedback_text.setText("PAUSED. Not enough data for analysis yet.<br>Drive at least 2 clean laps.")
        
        elif data.mGameState == 2: # Playing
            self.feedback_text.setText(f"<b>RACE ENGINEER:</b><br>{msg}")
        
        else:
            self.feedback_text.setText("Waiting for session...")

    def toggle_always_on_top(self, state):
        if state == 2: # Checked
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def update_loop(self):
        if not self.connected:
            if self.reader.connect():
                self.connected = True
                self.status_label.setText("CONNECTED")
                self.status_label.setStyleSheet("font-weight: bold; color: green; font-size: 14px;")
            else:
                self.status_label.setText("CONNECTING...")
                self.status_label.setStyleSheet("font-weight: bold; color: orange; font-size: 14px;")
                return

        data = self.reader.read()
        if data:
            # Game State Logic
            if data.mGameState == 1:
                state_str = "MENU"
            elif data.mGameState == 2:
                state_str = "PLAYING"
            elif data.mGameState == 3:
                state_str = "PAUSED"
            else:
                state_str = f"STATE {data.mGameState}"
            
            self.status_label.setText(f"GAME STATE: {state_str}")
            
            # --- Update Components ---
            self.engineer.update(data)
            self.recorder.update(data)
            
            # --- Lap Management ---
            car_name = data.mCarName.decode('utf-8', errors='ignore').strip()
            track_name = data.mTrackLocation.decode('utf-8', errors='ignore').strip()
            
            # Check for new lap
            viewed_idx = data.mViewedParticipantIndex
            if 0 <= viewed_idx < data.mNumParticipants:
                current_lap = data.mParticipantInfo[viewed_idx].mCurrentLap
                
                # If lap changed or just started
                if current_lap > self.last_lap:
                    # Try to save last lap time if valid
                    if data.mLastLapTime > 0:
                        session_type = data.mSessionState 
                        self.lap_manager.save_best_lap(car_name, track_name, data.mLastLapTime, str(session_type))
                        
                        # Capture active recommendation for the log
                        # We use the engineer's last known analysis or message as a proxy for "Setup Changes"
                        # Ideally, we'd know if the user actually changed something, but we can't.
                        # So we log what the engineer *suggested* prior to this lap.
                        note = "-"
                        analysis = self.engineer.get_analysis()
                        if analysis['ready']:
                             # Summarize briefly
                             actions = []
                             for t in analysis['tyres'].values():
                                 if "Druck" in t['action'] or "Sturz" in t['camber_action']:
                                     actions.append("Tyres")
                             if analysis['steering']: actions.append("Steering")
                             if actions:
                                 note = "Rec: " + ", ".join(set(actions))
                        
                        self.add_lap_to_table(self.last_lap, data.mLastLapTime, note)
                    
                    self.last_lap = current_lap
                    self.update_best_lap_label(car_name, track_name)
            
            # --- UI Updates ---
            self.update_session_tab(data)
            
            # Update Track Map periodically (e.g. every 10th frame) or if recording
            if self.recorder.track_data:
                self.update_track_map()

    def add_lap_to_table(self, lap_num, time_val, note="-"):
        from PyQt6.QtWidgets import QTableWidgetItem
        row = self.laps_table.rowCount()
        self.laps_table.insertRow(row)
        
        # Format time
        m = int(time_val // 60)
        s = int(time_val % 60)
        ms = int((time_val * 1000) % 1000)
        time_str = f"{m:02d}:{s:02d}.{ms:03d}"
        
        self.laps_table.setItem(row, 0, QTableWidgetItem(str(lap_num)))
        self.laps_table.setItem(row, 1, QTableWidgetItem(time_str))
        self.laps_table.setItem(row, 2, QTableWidgetItem("-")) # Sector placeholder
        self.laps_table.setItem(row, 3, QTableWidgetItem(note))

    def update_best_lap_label(self, car, track):
        best = self.lap_manager.get_best_lap(car, track)
        if best:
            self.best_lap_label.setText(f"Best Lap: {best['time']:.3f} ({best['date']})")

    def update_track_map(self):
        # This can be expensive, so maybe optimize later
        path = self.recorder.get_track_path()
        if not path: return
        
        self.ax.clear()
        
        # Extract data
        x = [p[0] for p in path]
        z = [p[1] for p in path]
        speeds = [p[2] for p in path]
        
        # Color Mapping
        # Slow < 80 km/h (Red), Med < 160 (Yellow), Fast > 160 (Green)
        colors = []
        for s in speeds:
            if s < 80:
                colors.append('red')
            elif s < 160:
                colors.append('yellow')
            else:
                colors.append('green')
        
        # Scatter plot for colored points
        self.ax.scatter(x, z, c=colors, s=2)
        
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.ax.set_facecolor('#2b2b2b')
        
        # Mark tightest corner
        corner = self.recorder.get_tightest_corner()
        if corner:
            self.ax.plot(corner[1], corner[2], 'wo', markersize=8) # White circle background
            self.ax.text(corner[1], corner[2], "!", color='red', fontsize=12, fontweight='bold', ha='center', va='center')
        
        self.canvas.draw()

    def format_time(self, seconds):
        if seconds <= 0: return "--:--.---"
        m = int(seconds // 60)
        s = int(seconds % 60)
        ms = int((seconds * 1000) % 1000)
        return f"{m:02d}:{s:02d}.{ms:03d}"

    def apply_dark_theme(self):
        # Simple Dark Palette
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        
        self.setPalette(palette)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
