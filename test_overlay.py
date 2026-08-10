import sys
from PyQt6.QtWidgets import QApplication
from productivity_guardian.ui.break_overlay import BreakOverlay

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    
    # Start a break that lasts for 3 minutes (180 seconds)
    print("Starting break overlay for 3 minutes...")
    print("Action required: Do not touch the keyboard or mouse.")
    print("Observe if the screen blanks or the laptop suspends during this time.")
    
    overlay = BreakOverlay(duration_seconds=180)
    overlay.break_finished.connect(app.quit)
    overlay.start()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
