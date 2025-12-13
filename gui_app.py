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
        self.lbl_status = QLabel("WAITING...")
        self.lbl_status.setStyleSheet("font-weight: bold; color: yellow;")
        header.addWidget(self.lbl_status)
        
        self.chk_ontop = QCheckBox("Always on Top")
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
        self.tabs.addTab(self.tab_setup, "Setup Engineer")
        
        # Tab 3: Track & Data
        self.tab_track = QWidget()
        self.setup_track_tab()
        self.tabs.addTab(self.tab_track, "Track Map")

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
        
        self.lbl_current_lap = QLabel("Current: --:--.---")
        self.lbl_current_lap.setFont(QFont("Arial", 20))
        
        self.lbl_best_lap = QLabel("Best: --:--.---")
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
        self.lbl_message = QLabel("Awaiting Data...")
        self.lbl_message.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.lbl_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_message.setStyleSheet("background-color: #222; color: #aaa; padding: 10px; margin-top: 10px;")
        layout.addWidget(self.lbl_message)
        
        # 3. Session Info
        info_layout = QHBoxLayout()
        self.lbl_dist = QLabel("Dist: 0.0 km")
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
        left_layout.addWidget(QLabel("Detected Problems:"))
        self.problem_list = QListWidget()
        self.problem_list.currentItemChanged.connect(self.on_problem_selected)
        left_layout.addWidget(self.problem_list)
        
        # Right: Solution Wizard
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("Setup Advice:"))
        self.txt_advice = QLabel("Select a problem to see advice.")
        self.txt_advice.setWordWrap(True)
        self.txt_advice.setStyleSheet("font-size: 14px; background-color: #2a2a2a; padding: 10px; border-radius: 5px;")
        self.txt_advice.setAlignment(Qt.AlignmentFlag.AlignTop)
        right_layout.addWidget(self.txt_advice)
        
        # Feedback Section
        self.lbl_feedback = QLabel("Stint Comparison: NEUTRAL")
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
                self.lbl_status.setText("CONNECTING...")
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
        
        # v2.0: Help Prompt if data is zeros
        if data.mGameState == 0 and data.mSessionState == 0 and raw_time == 0.0:
            self.lbl_message.setText("No Data? Enable 'Shared Memory' in AMS2 Options -> System -> Project CARS 2")
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
            self.lbl_current_lap.setText(f"Current: {self.format_time(data.mCurrentTime)}")
            if data.mBestLapTime > 0:
                self.lbl_best_lap.setText(f"Best: {self.format_time(data.mBestLapTime)}")
                
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
                    labels[i].setText(f"{key}\nNO DATA")

            # Message - Priority to Engineer
            msg = self.engineer.get_message()
            if "BOX" in msg:
                self.lbl_message.setText(msg)
                self.lbl_message.setStyleSheet("background-color: red; color: white; font-weight: bold; font-size: 24px;")
            else:
                self.lbl_message.setText(msg)
                self.lbl_message.setStyleSheet("background-color: #222; color: #aaa;")
                
            # Info
            dist = analysis.get('distance', 0.0)
            self.lbl_dist.setText(f"Dist: {dist:.1f} km")
            
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
        for t_name, t_info in analysis['tyres'].items():
            if "OK" not in t_info['action']:
                item = QListWidgetItem(f"Tyre {t_name}: {t_info['status']}")
                item.setData(Qt.ItemDataRole.UserRole, f"{t_info['action']}\n{t_info['details']}")
                self.problem_list.addItem(item)
            if "OK" not in t_info['camber_action']:
                item = QListWidgetItem(f"Camber {t_name}: Adjust")
                item.setData(Qt.ItemDataRole.UserRole, t_info['camber_action'])
                self.problem_list.addItem(item)
                
        # 2. Core Events
        for name, info in summary.items():
            count = info['count']
            item = QListWidgetItem(f"{name} ({count}x)")
            item.setData(Qt.ItemDataRole.UserRole, info['suggestion'])
            self.problem_list.addItem(item)
            
        # Feedback Label
        fb = analysis['feedback']
        if fb:
            self.lbl_feedback.setText(f"Stint Comparison: {fb}")
        else:
            self.lbl_feedback.setText("Stint Comparison: Ref Gathering...")

    def on_problem_selected(self, current, previous):
        if not current: return
        advice = current.data(Qt.ItemDataRole.UserRole)
        self.txt_advice.setText(advice)

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
