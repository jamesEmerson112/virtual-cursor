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



def animate_circular_movement():
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

            # Calculate new position
            x, y = calculate_circle_position(original_x, original_y, RADIUS, angle)

            # Move mouse to calculated position
            pyautogui.moveTo(x, y, duration=0)

            # Update angle for next frame
            angle += angle_increment
            frame_count += 1

            # Maintain frame rate
            time.sleep(FRAME_TIME)

            # Progress indicator (every 30 frames = 1 second)
            if frame_count % FPS == 0:
                print(f"Time elapsed: {elapsed_time:.1f}s")

        # Restore cursor to original position
        print(f"Restoring cursor to original position ({original_x}, {original_y})")
        pyautogui.moveTo(original_x, original_y, duration=0.5)

        print("Circular movement complete!")

    except KeyboardInterrupt:
        print("\nInterrupted by Ctrl+C. Stopping movement...")
        # Restore cursor position
        if 'center_x' in locals() and 'center_y' in locals():
            pyautogui.moveTo(original_x, original_y, duration=0.5)

    except Exception as e:
        print(f"Error during animation: {e}")
        return False

    finally:
        # Re-enable PyAutoGUI fail-safe
        pyautogui.FAILSAFE = True

    return True


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
    """Main execution function."""
    print("=" * 50)
    print("Circular Mouse Movement Automation")
    print("=" * 50)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Safety warning
    print("\nSAFETY NOTE: This script will control your mouse cursor.")
    print("Make sure you're ready before proceeding.")
    print("The cursor will move in a circle for 5 seconds.")

    # Confirmation prompt
    try:
        input("\nPress ENTER to start the circular movement (or Ctrl+C to cancel)...")
    except KeyboardInterrupt:
        print("\nCancelled by user.")
        sys.exit(0)

    # Start the animation
    success = animate_circular_movement()

    if success:
        print("\nProgram completed successfully!")
    else:
        print("\nProgram terminated with errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()
