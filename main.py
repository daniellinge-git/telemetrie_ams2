from telemetry_connector import AMS2Connector
from race_engineer import RaceEngineer
from ui_main import MainWindow

def main():
    print("Starting AMS2 Race Engineer...")
    
    # 1. Init Data Layer
    connector = AMS2Connector()
    
    # 2. Init Logic Layer
    engineer = RaceEngineer()
    
    # 3. Init Presentation Layer (UI)
    # Pass dependencies to UI so it can drive the update loop
    app = MainWindow(connector, engineer)
    
    # 4. Start Event Loop
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        # Cleanup
        connector.close()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
