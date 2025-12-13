import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QTabWidget, QPushButton, QCheckBox,
                             QListWidget, QListWidgetItem, QFrame, QSplitter)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette

# Matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Backend Imports
from ams2_reader import AMS2Reader
from ams2_race_engineer import RaceEngineer
from track_recorder import TrackRecorder
from ams2_lap_manager import LapTimeManager
from ams2_fuel_monitor import FuelMonitor
from ams2_wear_monitor import WearMonitor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AMS2 Telemetry Engineer v2.0")
        self.setGeometry(100, 100, 1000, 700)
        
        # Window Flags: Always on Top
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        
        # Backend Initialization
        self.reader = AMS2Reader()
        self.engineer = RaceEngineer()
        self.recorder = TrackRecorder()
        self.lap_manager = LapTimeManager()
        self.fuel_monitor = FuelMonitor()
        self.wear_monitor = WearMonitor()
        self.connected = False
        
        # State tracking
        self.last_lap = -1
        self.best_sectors = [0.0, 0.0, 0.0]
        self.first_update = True
        self.map_update_counter = 0

        # Styling
        self.apply_dark_theme()

        # UI Layout
        self.setup_ui()
        
        # Timer for polling
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(100) # 10Hz

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # --- Header ---
        header = QHBoxLayout()
        self.lbl_status = QLabel("WARTE...")
        self.lbl_status.setStyleSheet("font-weight: bold; color: yellow;")
        header.addWidget(self.lbl_status)
        
        self.chk_ontop = QCheckBox("Immer im Vordergrund")
        self.chk_ontop.setChecked(True)
        self.chk_ontop.stateChanged.connect(self.toggle_always_on_top)
        header.addWidget(self.chk_ontop)
        
        self.layout.addLayout(header)
        
        # --- Tabs ---
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Tab 1: Live Dashboard
        self.tab_live = QWidget()
        self.setup_live_tab()
        self.tabs.addTab(self.tab_live, "Live Dashboard")
        
        # Tab 2: Setup Engineer
        self.tab_setup = QWidget()
        self.setup_setup_tab()
        self.tabs.addTab(self.tab_setup, "Setup Ingenieur")
        
        # Tab 3: Track & Data
        self.tab_track = QWidget()
        self.setup_track_tab()
        self.tabs.addTab(self.tab_track, "Streckenkarte")

    def setup_live_tab(self):
        layout = QVBoxLayout(self.tab_live)
        
        # 1. Big Info Grid
        grid = QHBoxLayout()
        
        # Left: Times
        times_layout = QVBoxLayout()
        self.lbl_delta = QLabel("-0.000")
        self.lbl_delta.setFont(QFont("Arial", 40, QFont.Weight.Bold))
        self.lbl_delta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_delta.setStyleSheet("background-color: #333; color: white; padding: 10px; border-radius: 5px;")
        
        self.lbl_current_lap = QLabel("Aktuell: --:--.---")
        self.lbl_current_lap.setFont(QFont("Arial", 20))
        
        self.lbl_best_lap = QLabel("Beste: --:--.---")
        self.lbl_best_lap.setFont(QFont("Arial", 20))
        self.lbl_best_lap.setStyleSheet("color: #00ff00;")
        
        times_layout.addWidget(self.lbl_delta)
        times_layout.addWidget(self.lbl_current_lap)
        times_layout.addWidget(self.lbl_best_lap)
        grid.addLayout(times_layout)
        
        # Right: Tires & Status
        status_layout = QVBoxLayout()
        
        # Tyres Grid
        tyres_grid = QHBoxLayout()
        # Fronts
        self.lbl_fl = QLabel("FL\n--C")
        self.lbl_fr = QLabel("FR\n--C")
        # Rears
        self.lbl_rl = QLabel("RL\n--C")
        self.lbl_rr = QLabel("RR\n--C")
        
        for lbl in [self.lbl_fl, self.lbl_fr, self.lbl_rl, self.lbl_rr]:
            lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("background-color: #444; border: 1px solid #666; padding: 5px;")
            
        t_col1 = QVBoxLayout()
        t_col1.addWidget(self.lbl_fl)
        t_col1.addWidget(self.lbl_rl)
        
        t_col2 = QVBoxLayout()
        t_col2.addWidget(self.lbl_fr)
        t_col2.addWidget(self.lbl_rr)
        
        tyres_grid.addLayout(t_col1)
        tyres_grid.addLayout(t_col2)
        
        status_layout.addLayout(tyres_grid)
        grid.addLayout(status_layout)
        
        layout.addLayout(grid)
        
        # 2. Critical Message Banner
        self.lbl_message = QLabel("Warte auf Daten...")
        self.lbl_message.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.lbl_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_message.setStyleSheet("background-color: #222; color: #aaa; padding: 10px; margin-top: 10px;")
        layout.addWidget(self.lbl_message)
        
        # 3. Session Info
        info_layout = QHBoxLayout()
        self.lbl_dist = QLabel("Distanz: 0.0 km")
        self.lbl_phase = QLabel("Phase: -")
        self.lbl_handling = QLabel("Balance: -")
        
        info_layout.addWidget(self.lbl_dist)
        info_layout.addWidget(self.lbl_phase)
        info_layout.addWidget(self.lbl_handling)
        layout.addLayout(info_layout)
        
        layout.addStretch()

    def setup_setup_tab(self):
        layout = QVBoxLayout(self.tab_setup)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Problem List
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("Erkannte Probleme:"))
        self.problem_list = QListWidget()
        self.problem_list.currentItemChanged.connect(self.on_problem_selected)
        left_layout.addWidget(self.problem_list)
        
        # Right: Solution Wizard
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("Setup Empfehlung:"))
        self.txt_advice = QLabel("Wähle ein Problem um Details zu sehen.")
        self.txt_advice.setWordWrap(True)
        self.txt_advice.setStyleSheet("font-size: 14px; background-color: #2a2a2a; color: white; padding: 10px; border-radius: 5px;")
        self.txt_advice.setAlignment(Qt.AlignmentFlag.AlignTop)
        right_layout.addWidget(self.txt_advice)
        
        # Feedback Section
        self.lbl_feedback = QLabel("Stint Vergleich: NEUTRAL")
        self.lbl_feedback.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 20px;")
        right_layout.addWidget(self.lbl_feedback)
        
        right_layout.addStretch()
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)

    def setup_track_tab(self):
        layout = QVBoxLayout(self.tab_track)
        
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.figure.patch.set_facecolor('#2b2b2b')
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#2b2b2b')
        self.ax.axis('off')
        
        layout.addWidget(self.canvas)
        layout.addWidget(QLabel("Markers: Red=Lockup, Cyan=U-Steer, Orange=O-Steer"))

    def update_loop(self):
        if not self.connected:
            if self.reader.connect():
                self.connected = True
                # self.lbl_status.setText("CONNECTED") # Overwritten below
            else:
                self.lbl_status.setText("VERBINDE...")
                return

        data = self.reader.read()
        if not data: return
        
        # Debug Status
        state_map = {0: "EXIT", 1: "MENU", 2: "PLAYING", 3: "PAUSED"}
        gs = state_map.get(data.mGameState, str(data.mGameState))
        ss = data.mSessionState
        
        # Raw Data Check
        raw_t = data.mTyreTemp[0] if hasattr(data, 'mTyreTemp') else -99
        raw_time = data.mCurrentTime
        
        self.lbl_status.setText(f"CON | GS:{gs} | SS:{ss} | T:{raw_t:.1f} | Time:{raw_time:.1f}")
        
        # Debug FL Temp
        if self.map_update_counter % 10 == 0: # reduce spam
             print(f"DEBUG: FL Raw Temp: {raw_t}")
        
        # v2.0: Help Prompt if data is zeros
        if data.mGameState == 0 and data.mSessionState == 0 and raw_time == 0.0:
            self.lbl_message.setText("Keine Daten? 'Shared Memory' in AMS2 Optionen aktivieren -> System -> Project CARS 2")
            self.lbl_message.setStyleSheet("background-color: purple; color: white; font-size: 18px; font-weight: bold;")
            return # Skip other updates to avoid crashes on zero data
        
        try:
            # Update Components
            self.engineer.update(data)
            self.recorder.update(data)
            self.fuel_monitor.update(data)
            self.wear_monitor.update(data)
            
            # Update UI Tabs
            self.update_live_tab(data)
            
            # Only update Setup/Track if visible or periodically
            # (Optimization)
            current_idx = self.tabs.currentIndex()
            if current_idx == 1: # Setup
                self.update_setup_tab()
            elif current_idx == 2: # Track
                self.update_track_tab()

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.lbl_status.setText(f"ERROR: {str(e)}")
            self.lbl_status.setStyleSheet("font-weight: bold; color: red;")

    def update_live_tab(self, data):
        try:
            # Times
            self.lbl_current_lap.setText(f"Aktuell: {self.format_time(data.mCurrentTime)}")
            if data.mBestLapTime > 0:
                self.lbl_best_lap.setText(f"Beste: {self.format_time(data.mBestLapTime)}")
                
            # v2.1: Lap Feedback / Last Lap Analysis
            # Check for new lap
            current_lap = 0
            if data.mViewedParticipantIndex < 64:
                 current_lap = data.mParticipantInfo[data.mViewedParticipantIndex].mCurrentLap
            
            if current_lap > self.last_lap and self.last_lap != -1:
                # New Lap Started!
                last_time = data.mLastLapTime
                best_time = data.mBestLapTime
                
                # If we just set a new best, then last_time == best_time (approx)
                # Compare with PREVIOUS best? Hard to track without history.
                # Logic: If last_time <= best_time (with small margin), it's a PB.
                
                diff = last_time - best_time
                
                msg = ""
                if diff <= 0.05 and best_time > 0: # New Best (allow float jitter)
                    msg = f"Runde: {self.format_time(last_time)} (NEUE BESTZEIT!)"
                    self.lbl_message.setStyleSheet("background-color: green; color: white; font-weight: bold;")
                elif best_time > 0:
                     if diff < 1.0:
                         msg = f"Runde: {self.format_time(last_time)} (+{diff:.2f}s - Gut!)"
                         self.lbl_message.setStyleSheet("background-color: #333; color: green; font-weight: bold;")
                     else:
                         msg = f"Runde: {self.format_time(last_time)} (+{diff:.2f}s)"
                         self.lbl_message.setStyleSheet("background-color: #333; color: orange;")
                else:
                    msg = f"Runde: {self.format_time(last_time)}"
                    
                self.lbl_message.setText(msg)
                # Keep message for 10s? We rely on it not being overwritten quickly.
                # Other updates might overwrite it (e.g. status).
                # Force overwrite protection or separate label? 
                # For now, let's just set it. The 'engineer.get_message()' below might overwrite it 
                # if there is an active engineer message.
                # We can inject it into engineer message queue if we had one.
                
            self.last_lap = current_lap
                
            # Delta (Assume we can calculate or use existing?)
            # For prototype, we don't have perfect delta without a reference lap system.
            # Use simple sector delta logic if available, or just "-"
            # AMS2 doesn't give live delta in shared memory easily without reference lap.
            # We will leave as placeholder or use SplitTime if available?
            # mSplitTime might be available.
            if hasattr(data, 'mSplitTime') and data.mSplitTime != 0.0:
                delta = data.mSplitTime
                sign = "+" if delta > 0 else ""
                color = "#ff0000" if delta > 0 else "#00ff00"
                self.lbl_delta.setText(f"{sign}{delta:.3f}")
                self.lbl_delta.setStyleSheet(f"background-color: {color}; color: black; font-weight: bold; font-size: 40px;")
            else:
                 self.lbl_delta.setText("--.---")
                 self.lbl_delta.setStyleSheet("background-color: #333; color: white;")

            # Tires (Color Coded)
            analysis = self.engineer.get_analysis()
            
            tyre_info = analysis['tyres']
            labels = [self.lbl_fl, self.lbl_fr, self.lbl_rl, self.lbl_rr]
            keys = ["FL", "FR", "RL", "RR"]
            
            for i, key in enumerate(keys):
                if key in tyre_info:
                    info = tyre_info[key]
                    temp = info['temp']
                    color = info['color']
                    # Map logic color to hex
                    hex_col = "#ffffff"
                    if color == "blue": hex_col = "#00bfff"
                    elif color == "red": hex_col = "#ff4500"
                    elif color == "green": hex_col = "#00ff00"
                    
                    labels[i].setText(f"{key}\n{temp:.0f}C")
                    labels[i].setStyleSheet(f"background-color: #444; border: 2px solid {hex_col}; color: {hex_col}; font-weight: bold;")
                else:
                    labels[i].setText(f"{key}\nKEINE DATEN")

            # Message - Priority to Engineer
            # Message - Priority to Engineer, BUT allow Lap Feedback to persist if Engineer is "Scanning..."
            # Strategy: If engineer has "Important" message (BOX), overwrite.
            # If engineer has generic message ("Analyzing..."), ONLY overwrite if we haven't just finished a lap (msg timer?).
            # Simple hack: Prefixed messages.
            
            eng_msg = self.engineer.get_message()
            current_msg = self.lbl_message.text()
            
            # If current message is a "Result" (starts with "Runde:"), keep it unless Engineer screams BOX
            is_lap_result = current_msg.startswith("Runde:")
            
            if "BOX" in eng_msg:
                self.lbl_message.setText(eng_msg)
                self.lbl_message.setStyleSheet("background-color: red; color: white; font-weight: bold; font-size: 24px;")
            elif not is_lap_result or (is_lap_result and "BOX" in eng_msg): # Logic fix
                 # Show engineer status if we are not showing a lap result
                 # Or if engineer status is interesting?
                 # Let's show Engineer status only if NOT lap result.
                 if not is_lap_result:
                     self.lbl_message.setText(eng_msg)
                     self.lbl_message.setStyleSheet("background-color: #222; color: #aaa;")
                
            # Info
            dist = analysis.get('distance', 0.0)
            self.lbl_dist.setText(f"Distanz: {dist:.1f} km")
            
            # Phase (Debug)
            phase = self.engineer.core_engine.phase_detector.current_phase
            self.lbl_phase.setText(f"Phase: {phase}")

            # Balance
            bal = analysis['handling']
            self.lbl_handling.setText(f"Bal: {bal}")
            if bal == "OVERSTEER": self.lbl_handling.setStyleSheet("color: orange;")
            elif bal == "UNDERSTEER": self.lbl_handling.setStyleSheet("color: cyan;")
            else: self.lbl_handling.setStyleSheet("color: white;")
            
        except Exception as e:
            import traceback
            print("ERROR in Live Tab:")
            traceback.print_exc()
            self.lbl_message.setText(f"ERR: {str(e)}")
            self.lbl_message.setStyleSheet("background-color: purple; color: white;")

    def update_setup_tab(self):
        # Populate List with Core Events + Tyre Issues
        analysis = self.engineer.get_analysis()
        
        # Only update if item count changes to avoid flicker (simple check)
        # Or clear and rebuild? Qt is fast enough usually.
        # Better: Store last summary header
        
        summary = analysis['core_events']['summary']
        
        # Check current items
        current_rows = self.problem_list.count()
        
        # If active, we might want to refresh.
        self.problem_list.clear() # Brute force for now
        
        # 1. Tyres
        # 1. Tyres
        for t_name, t_info in analysis['tyres'].items():
            # Status Item
            status_text = f"Tyre {t_name}: {t_info['status']}"
            item = QListWidgetItem(status_text)
            
            is_ok = "OK" in t_info['action']
            if is_ok:
                item.setForeground(Qt.GlobalColor.green)
                # Ensure we have reason for OK items too
                reason = t_info.get('reason', 'Optimal.')
                item.setData(Qt.ItemDataRole.UserRole, f"{t_info['action']}\n{t_info['details']}|||{reason}")
            else:
                item.setForeground(Qt.GlobalColor.red)
                item.setData(Qt.ItemDataRole.UserRole, f"{t_info['action']}\n{t_info['details']}|||{t_info['reason']}")
            
            self.problem_list.addItem(item)

            # Camber Item
            camber_ok = "OK" in t_info['camber_action']
            item_c = QListWidgetItem(f"Camber {t_name}: {t_info['camber_action'].split(' ')[0] if camber_ok else 'Adjust'}")
            
            if camber_ok:
                item_c.setForeground(Qt.GlobalColor.green)
                 # Ensure we have reason for OK items too
                reason = t_info.get('camber_reason', 'Optimal.')
                item_c.setData(Qt.ItemDataRole.UserRole, f"{t_info['camber_action']}|||{reason}")
            else:
                item_c.setForeground(Qt.GlobalColor.red)
                item_c.setText(f"Camber {t_name}: Adjust") # Reset text to generic if bad
                item_c.setData(Qt.ItemDataRole.UserRole, f"{t_info['camber_action']}|||{t_info['camber_reason']}")
            
            self.problem_list.addItem(item_c)
                
        # 2. Core Events
        for name, info in summary.items():
            count = info['count']
            item = QListWidgetItem(f"{name} ({count}x)")
            item.setData(Qt.ItemDataRole.UserRole, f"{info['suggestion']}|||{info.get('reason', '')}")
            self.problem_list.addItem(item)
            
        # Feedback Label
        fb = analysis['feedback']
        if fb:
            self.lbl_feedback.setText(f"Stint Vergleich: {fb}")
        else:
            self.lbl_feedback.setText("Stint Vergleich: Sammle Ref-Daten...")

    def on_problem_selected(self, current, previous):
        if not current: return
        data = current.data(Qt.ItemDataRole.UserRole)
        
        # New Format: Tuple/List or String?
        # Let's assume the backend might send a dict or string.
        # But for list widget item, we usually store simple data.
        # If it's a string, just show it.
        # If we update backend to return "Advice|Reason", we can split.
        
        # Let's handle string with possible delimiter
        text = str(data)
        
        # Check if we have a delimiter (e.g. "|||") for Reason
        if "|||" in text:
            parts = text.split("|||")
            advice = parts[0]
            reason = parts[1] if len(parts) > 1 else ""
            
            full_text = f"<b>EMPFEHLUNG:</b><br>{advice}<br><br><b><i>GRUND:</i></b><br><i>{reason}</i>"
            self.txt_advice.setText(full_text)
        else:
            self.txt_advice.setText(text)

    def update_track_tab(self):
        self.map_update_counter += 1
        if self.map_update_counter < 10: return # Limit FPS
        self.map_update_counter = 0
        
        path = self.recorder.get_track_path()
        if not path: return
        
        self.ax.clear()
        
        # Draw Track
        x = [p[0] for p in path]
        z = [p[1] for p in path]
        self.ax.plot(x, z, color='white', linewidth=1)
        
        # Draw Events
        analysis = self.engineer.get_analysis()
        events = analysis['core_events']['events']
        
        # Separate by type for colors
        lockups_x, lockups_z = [], []
        under_x, under_z = [], []
        over_x, over_z = [], []
        
        for e in events:
            if "Lockup" in e['name']:
                lockups_x.append(e['x'])
                lockups_z.append(e['z'])
            elif "Understeer" in e['name']:
                under_x.append(e['x'])
                under_z.append(e['z'])
            elif "Oversteer" in e['name']:
                over_x.append(e['x'])
                over_z.append(e['z'])
                
        if lockups_x: self.ax.scatter(lockups_x, lockups_z, c='red', s=20, label='Lockup')
        if under_x: self.ax.scatter(under_x, under_z, c='cyan', s=20, label='Understeer')
        if over_x: self.ax.scatter(over_x, over_z, c='orange', s=20, label='Oversteer')
        
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        
        self.canvas.draw()

    def format_time(self, seconds):
        if seconds <= 0: return "--:--.---"
        m = int(seconds // 60)
        s = int(seconds % 60)
        ms = int((seconds * 1000) % 1000)
        return f"{m:02d}:{s:02d}.{ms:03d}"
        
    def toggle_always_on_top(self, state):
        if state == 2:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(15, 15, 15))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
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
