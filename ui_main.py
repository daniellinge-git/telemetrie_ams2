import customtkinter as ctk
import tkinter as tk

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MainWindow(ctk.CTk):
    """
    Presentation Layer for AMS2 Race Engineer.
    """
    def __init__(self, connector, engineer):
        super().__init__()

        self.connector = connector
        self.engineer = engineer
        
        # Window Setup
        self.title("AMS2 Race Engineer - Virtual Assistant")
        self.geometry("800x600")
        self.attributes("-topmost", True) # Always on Top
        
        # Grid Layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Tabs
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.tab_live = self.tab_view.add("Live-Ingenieur")
        self.tab_analysis = self.tab_view.add("Analyse")
        self.tab_telemetry = self.tab_view.add("Telemetrie")
        
        self._setup_live_tab()
        self._setup_analysis_tab()
        self._setup_telemetry_tab()
        
        # Start Loop
        self.after(16, self.update_cycle)

    def _setup_live_tab(self):
        # Status
        self.lbl_status = ctk.CTkLabel(self.tab_live, text="STATUS: Starting...", font=("Arial", 16, "bold"))
        self.lbl_status.pack(pady=10)
        
        # Advice Box
        self.txt_advice = ctk.CTkTextbox(self.tab_live, height=200, font=("Consolas", 14))
        self.txt_advice.pack(fill="x", padx=10, pady=10)
        self.txt_advice.insert("0.0", "Warte auf Fahrdaten...")
        self.txt_advice.configure(state="disabled")
        
        # Detailed Info
        self.lbl_detail = ctk.CTkLabel(self.tab_live, text="-")
        self.lbl_detail.pack(pady=5)

    def _setup_analysis_tab(self):
        self.lbl_analysis_title = ctk.CTkLabel(self.tab_analysis, text="Streckenkarte (Live)", font=("Arial", 14))
        self.lbl_analysis_title.pack(pady=5)
        
        # Track Map Canvas
        self.canvas_track = tk.Canvas(self.tab_analysis, bg="#2b2b2b", height=400, highlightthickness=0)
        self.canvas_track.pack(fill="both", expand=True, padx=10, pady=10)

    def _setup_telemetry_tab(self):
        self.lbl_telemetry = ctk.CTkLabel(self.tab_telemetry, text="Raw Data", font=("Consolas", 12))
        self.lbl_telemetry.pack(pady=10, padx=10)
        
    def update_cycle(self):
        # 1. Read Data
        data = self.connector.read_data()
        
        # 2. Process Logic
        logic_output = self.engineer.process_data(data)
        
        # 3. Update UI
        self._update_ui(data, logic_output)
        
        # Loop
        self.after(50, self.update_cycle) # 20Hz update for UI is enough

    def _update_ui(self, data, logic_output):
        # Update Live Tab
        self.lbl_status.configure(text=f"STATUS: {logic_output['state']}")
        
        # Update Advice
        msg = logic_output.get("message", "")
        suggestions = logic_output.get("suggestions", [])
        
        full_text = f"{msg}\n\n"
        if suggestions:
            full_text += "VORSCHLÄGE:\n" + "\n".join(suggestions)
            
        self.txt_advice.configure(state="normal")
        self.txt_advice.delete("0.0", "end")
        self.txt_advice.insert("0.0", full_text)
        self.txt_advice.configure(state="disabled")
        
        # Update Track Map (Simple Dot Drawing)
        # In a real app we would redraw the whole line or use a persistent line object.
        # For this MVP, we just draw the current position as a dot to trace the line.
        if data and logic_output['state'] != "WAITING":
            # Normalize coordinates?
            # We don't know the track bounds effectively without pre-mapping.
            # We can just center it relative to the canvas center (400, 200) assuming some scale.
            # Map Range: +/- 2000 meters?
            scale = 0.2 # Pixels per meter
            center_x, center_y = 400, 200
            
            # Get current pos
            pos = data.mParticipantInfo[data.mViewedParticipantIndex].mWorldPosition
            x = pos[0]
            z = pos[2] # Z is usually "forward/backward" in 3D, Y is up
            
            # Simple conversion to canvas
            # We need to center the map dynamically or just plot relative to start.
            # Let's simple plot relative to 0,0 world being center.
            c_x = center_x + (x * scale)
            c_y = center_y + (z * scale) # Invert Z?
            
            # Draw point
            r = 1
            self.canvas_track.create_oval(c_x-r, c_y-r, c_x+r, c_y+r, fill="cyan", outline="")

        # Update Telemetry Tab
        if data:
             tel_text = (
                 f"Speed: {data.mSpeed*3.6:.1f} km/h\n"
                 f"RPM: {data.mRpm:.0f}\n"
                 f"Gear: {data.mGear}\n"
                 f"Temp FL: {data.mTyreTemp[0]:.1f}°C\n"
                 f"Temp FR: {data.mTyreTemp[1]:.1f}°C\n"
                 f"Temp RL: {data.mTyreTemp[2]:.1f}°C\n"
                 f"Temp RR: {data.mTyreTemp[3]:.1f}°C\n"
             )
             self.lbl_telemetry.configure(text=tel_text)
