#!/usr/bin/env python3
"""
Circular Mouse Movement Automation
==================================
Automatically moves the mouse cursor in a circle for 5 seconds.
Press ESC to interrupt the movement at any time.

Features:
- Circular movement centered on current cursor position
- 5-second duration with smooth 30 FPS animation
- Escape key interrupt capability
- Safety fail-safe mechanisms
- Automatic cursor position restoration
"""

import pyautogui
import math
import time
import threading
import sys

# Configuration constants
DURATION = 0.01 # Animation duration in seconds
PIXELS_PER_MOVE = 10

# Global flag for interrupt handling
interrupted = False


def monitor_escape_key():
    """Monitor for escape key press in a separate thread."""
    global interrupted
    try:
        import keyboard
        print("Press ESC to interrupt the movement at any time...")
        keyboard.wait('esc')
        interrupted = True
        print("\nEscape key detected! Stopping movement...")
    except ImportError:
        print("Note: 'keyboard' library not available. Use Ctrl+C to interrupt.")
    except Exception as e:
        print(f"Keyboard monitoring error: {e}")



def mouse_move():
    """Main animation loop for circular mouse movement."""
    global interrupted

    try:
        # Disable PyAutoGUI fail-safe temporarily for smooth movement
        pyautogui.FAILSAFE = False

        # Start keyboard monitoring thread
        keyboard_thread = threading.Thread(target=monitor_escape_key, daemon=True)
        keyboard_thread.start()

        # Main animation loop
        while not interrupted:
            # Get initial cursor position as circle center
            original_x, original_y = pyautogui.position()

            dx = 0
            dy = 0

            if (TODO: MOVING LEFT):
                dx -= 1
            if (TODO: MOVING RIGHT):
                dx += 1

            if (TODO: MOVING UP):
                dy -= 1
            if (TODO: MOVING DOWN):
                dy += 1

            # Calculate new position
            x += PIXELS_PER_MOVE * dx
            y += PIXELS_PER_MOVE * dy

            # Move mouse to calculated position
            pyautogui.moveTo(x, y, duration=0)

            # Maintain frame rate
            time.sleep(DURATION)

    finally:
        # Re-enable PyAutoGUI fail-safe
        pyautogui.FAILSAFE = True


def check_dependencies():
    """Check if required dependencies are available."""
    missing_deps = []

    try:
        import pyautogui
    except ImportError:
        missing_deps.append('pyautogui')

    try:
        import keyboard
    except ImportError:
        print("Warning: 'keyboard' library not found. ESC key interrupt won't work.")
        print("Install with: pip install keyboard")
        print("Alternative: Use Ctrl+C to interrupt.\n")

    if missing_deps:
        print(f"Missing required dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install -r requirements.txt")
        return False

    return True


def main():
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Start the animation
    mouse_move()

if __name__ == "__main__":
    main()
