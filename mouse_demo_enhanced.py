import os
import urllib.parse
import requests
from dotenv import load_dotenv

from flask import Flask, redirect, request, jsonify, session
import cortex
from cortex import Cortex

import pyautogui
import time
import threading
import sys
from collections import deque
from datetime import datetime


# Configuration constants
DURATION = 0.01  # Animation duration in seconds
PIXELS_PER_MOVE = 10

# Enhanced power monitoring configuration
POWER_THRESHOLD = 0.3  # Lowered from 0.5 for better sensitivity
ACTION_THRESHOLD = 0.5  # Higher threshold for actual actions
POWER_HISTORY_SIZE = 20  # Number of power readings to keep for averaging
UPDATE_RATE_LIMIT = 0.1  # Minimum time between power meter updates (seconds)

# Global flags and state
interrupted = False
mouse_control_active = False
last_power_update = 0


class PowerMonitor:
    """Enhanced power monitoring and visualization system."""

    def __init__(self, history_size=POWER_HISTORY_SIZE):
        self.power_history = deque(maxlen=history_size)
        self.last_update = 0
        self.update_interval = UPDATE_RATE_LIMIT

    def add_reading(self, power, action):
        """Add a new power reading to the history."""
        timestamp = time.time()
        self.power_history.append({
            'power': power,
            'action': action,
            'timestamp': timestamp
        })

        # Update display if enough time has passed
        if timestamp - self.last_update > self.update_interval:
            self.display_power_meter(power, action)
            self.last_update = timestamp

    def display_power_meter(self, current_power, current_action):
        """Display live power meter with visual feedback."""
        # Create ASCII power bar
        bar_length = 50
        filled_length = int(bar_length * min(current_power, 1.0))
        bar = '█' * filled_length + '░' * (bar_length - filled_length)

        # Get power statistics
        avg_power = self.get_average_power()
        max_power = self.get_max_power()

        # Color coding for different power levels
        if current_power > ACTION_THRESHOLD:
            power_status = "🔥 HIGH"
        elif current_power > POWER_THRESHOLD:
            power_status = "⚡ MED"
        else:
            power_status = "💤 LOW"

        # Clear previous line and display new meter
        print(f"\r🧠 [{bar}] {current_power:.3f} | Avg: {avg_power:.3f} | Max: {max_power:.3f} | {current_action:>8} | {power_status}", end="", flush=True)

        # Print newline for significant events
        if current_power > ACTION_THRESHOLD:
            print(f"\n🎯 ACTION TRIGGERED: {current_action} (power: {current_power:.3f})")

    def get_average_power(self):
        """Calculate average power from recent history."""
        if not self.power_history:
            return 0.0
        return sum(reading['power'] for reading in self.power_history) / len(self.power_history)

    def get_max_power(self):
        """Get maximum power from recent history."""
        if not self.power_history:
            return 0.0
        return max(reading['power'] for reading in self.power_history)

    def print_stats(self):
        """Print detailed power statistics."""
        if not self.power_history:
            print("\n📊 No power data available yet")
            return

        avg = self.get_average_power()
        max_val = self.get_max_power()
        min_val = min(reading['power'] for reading in self.power_history)
        recent_actions = [r['action'] for r in list(self.power_history)[-5:]]

        print(f"\n📊 POWER STATISTICS:")
        print(f"   Average: {avg:.3f}")
        print(f"   Max: {max_val:.3f}")
        print(f"   Min: {min_val:.3f}")
        print(f"   Recent Actions: {recent_actions}")


class MouseController:
    """Separate mouse control logic from data reception."""

    def __init__(self):
        self.active = False
        self.last_action = None
        self.last_power = 0.0
        self.control_thread = None
        self.keyboard_thread = None

    def start_control(self):
        """Start mouse control in a separate thread."""
        if self.active:
            return

        self.active = True
        self.control_thread = threading.Thread(target=self._control_loop, daemon=True)
        self.control_thread.start()

        # Start keyboard monitoring
        self.keyboard_thread = threading.Thread(target=self._monitor_escape_key, daemon=True)
        self.keyboard_thread.start()

    def stop_control(self):
        """Stop mouse control."""
        self.active = False
        global interrupted
        interrupted = True

    def update_command(self, action, power):
        """Update the current mouse command."""
        self.last_action = action
        self.last_power = power

    def _monitor_escape_key(self):
        """Monitor for escape key press in a separate thread."""
        try:
            import keyboard
            print("\n🎮 Mouse control active - Press ESC to stop movement...")
            keyboard.wait('esc')
            self.stop_control()
            print("\n⛔ Escape key detected! Stopping mouse control...")
        except ImportError:
            print("\nNote: 'keyboard' library not available. Use Ctrl+C to interrupt.")
        except Exception as e:
            print(f"Keyboard monitoring error: {e}")

    def _control_loop(self):
        """Main mouse control loop running in separate thread."""
        global interrupted

        try:
            # Disable PyAutoGUI fail-safe temporarily for smooth movement
            pyautogui.FAILSAFE = False

            print("\n🖱️  Mouse control started - move your cursor with mental commands!")

            while self.active and not interrupted:
                if self.last_power > ACTION_THRESHOLD and self.last_action:
                    dx, dy = 0, 0

                    # Map mental commands to mouse movements
                    if self.last_action == 'left':
                        dx = -1
                    elif self.last_action == 'right':
                        dx = 1
                    elif self.last_action == 'lift':
                        dy = -1
                    elif self.last_action == 'drop':
                        dy = 1
                    elif self.last_action == 'push':
                        # Click action
                        print("🖱️  CLICK!")
                        pyautogui.click()
                        continue

                    # Move mouse if there's a direction
                    if dx != 0 or dy != 0:
                        current_x, current_y = pyautogui.position()
                        new_x = current_x + (PIXELS_PER_MOVE * dx * self.last_power)
                        new_y = current_y + (PIXELS_PER_MOVE * dy * self.last_power)
                        pyautogui.moveTo(new_x, new_y, duration=0)

                time.sleep(DURATION)

        finally:
            # Re-enable PyAutoGUI fail-safe
            pyautogui.FAILSAFE = True
            print("\n🛑 Mouse control stopped")


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

# -----------------------------
# Flask / Spotify setup
# -----------------------------
load_dotenv()

app = Flask(__name__)
app.secret_key = 'Your Spotify Key'

# Global (in-memory) token for demo purposes
access_token_global = None

# Initialize global components
power_monitor = PowerMonitor()
mouse_controller = MouseController()

# -----------------------------
# Emotiv / Cortex setup copied from your working live.py
# -----------------------------
EMOTIV_CLIENT_ID = os.getenv("CLIENT_ID", "")
EMOTIV_CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")
PROFILE_NAME = os.getenv("PROFILE_NAME", "demo-app")  # Fixed default value
HEADSET_ID = os.getenv("HEADSET_ID", "")  # optional

def _require_config():
    missing = []
    if not EMOTIV_CLIENT_ID or not EMOTIV_CLIENT_SECRET:
        missing.append("CLIENT_ID / CLIENT_SECRET (Emotiv)")
    if not PROFILE_NAME:
        missing.append("PROFILE_NAME")
    if missing:
        raise RuntimeError(f"Missing required configuration: {', '.join(missing)}")

class LiveAdvance:
    """
    Copied (lightly adapted) from your working live.py. This is the spine that
    makes your trained profile actually load and emits live 'com' events.
    """
    def __init__(self, app_client_id, app_client_secret, **kwargs):
        self.c = Cortex(app_client_id, app_client_secret, debug_mode=True, **kwargs)
        self.c.bind(create_session_done=self.on_create_session_done)
        self.c.bind(query_profile_done=self.on_query_profile_done)
        self.c.bind(load_unload_profile_done=self.on_load_unload_profile_done)
        self.c.bind(save_profile_done=self.on_save_profile_done)
        self.c.bind(new_com_data=self.on_new_com_data)
        self.c.bind(get_mc_active_action_done=self.on_get_mc_active_action_done)
        self.c.bind(mc_action_sensitivity_done=self.on_mc_action_sensitivity_done)
        self.c.bind(inform_error=self.on_inform_error)

    def start(self, profile_name, headsetId=''):
        if profile_name == '':
            raise ValueError('Empty profile_name. The profile_name cannot be empty.')

        self.profile_name = profile_name
        self.c.set_wanted_profile(profile_name)

        if headsetId != '':
            self.c.set_wanted_headset(headsetId)

        self.c.open()

    # Profile ops
    def load_profile(self, profile_name):
        self.c.setup_profile(profile_name, 'load')

    def unload_profile(self, profile_name):
        self.c.setup_profile(profile_name, 'unload')

    def save_profile(self, profile_name):
        self.c.setup_profile(profile_name, 'save')

    def subscribe_data(self, streams):
        self.c.sub_request(streams)

    def get_active_action(self, profile_name):
        self.c.get_mental_command_active_action(profile_name)

    def get_sensitivity(self, profile_name):
        self.c.get_mental_command_action_sensitivity(profile_name)

    def set_sensitivity(self, profile_name, values):
        self.c.set_mental_command_action_sensitivity(profile_name, values)

    # ---- Cortex event handlers ----
    def on_create_session_done(self, *args, **kwargs):
        print('on_create_session_done')
        self.c.query_profile()

    def on_query_profile_done(self, *args, **kwargs):
        print('on_query_profile_done')
        self.profile_lists = kwargs.get('data')
        if self.profile_name in self.profile_lists:
            self.c.get_current_profile()
        else:
            self.c.setup_profile(self.profile_name, 'create')

    def on_load_unload_profile_done(self, *args, **kwargs):
        is_loaded = kwargs.get('isLoaded')
        print("on_load_unload_profile_done:", is_loaded)
        if is_loaded:
            self.get_active_action(self.profile_name)
        else:
            print(f'The profile {self.profile_name} is unloaded')
            self.profile_name = ''

    def on_save_profile_done(self, *args, **kwargs):
        print('Save profile', self.profile_name, "successfully")
        self.c.sub_request(['com'])
        # Power monitoring will start automatically when com data arrives
        print("\n🎯 Starting enhanced power monitoring...")

    def on_new_com_data(self, *args, **kwargs):
        # Default: just print. We'll override this in SpotifyLive.
        data = kwargs.get('data')
        print('Mental Command detected:', data)

    def on_get_mc_active_action_done(self, *args, **kwargs):
        data = kwargs.get('data')
        print('on_get_mc_active_action_done:', data)
        self.get_sensitivity(self.profile_name)

    def on_mc_action_sensitivity_done(self, *args, **kwargs):
        data = kwargs.get('data')
        print('on_mc_action_sensitivity_done:', data)
        if isinstance(data, list):
            # Reduced sensitivity values for better control
            sensitivity_1 = 5  # Reduced from 10
            sensitivity_2 = 2  # Increased from 1
            sensitivity_3 = 2  # Increased from 1
            sensitivity_4 = 2  # Increased from 1
            new_values = [sensitivity_1, sensitivity_2, sensitivity_3, sensitivity_4]
            print(f"Current sensitivity: {data}")
            print(f"Setting new sensitivity: {new_values}")
            self.set_sensitivity(self.profile_name, new_values)
        else:
            self.save_profile(self.profile_name)

    def on_inform_error(self, *args, **kwargs):
        error_data = kwargs.get('error_data')
        print(f"Error: {error_data}")
        if error_data:
            error_code = error_data.get('code')
            error_message = error_data.get('message', '')
            if error_code == cortex.ERR_PROFILE_ACCESS_DENIED:
                print('Get error', error_message, ". Disconnecting headset.")
                self.c.disconnect_headset()

# -----------------------------
# Enhanced Spotify-integrated Live
# -----------------------------
class SpotifyLive(LiveAdvance):
    """
    Extends the working LiveAdvance so that com events trigger Spotify actions.
    Maps:
      - 'lift'  (power > 0.5) -> pause
      - 'drop'  (power > 0.5) -> resume
      - 'neutral' -> no-op
    Adjust thresholds/action mapping as needed.
    """
    def __init__(self, app_client_id, app_client_secret, **kwargs):
        super().__init__(app_client_id, app_client_secret, **kwargs)

    def on_new_com_data(self, *args, **kwargs):
        global access_token_global, power_monitor
        data = kwargs.get('data', {}) or {}
        action = data.get('action')
        power = data.get('power', 0.0)
        print(f"[COM] action={action} power={power:.2f} time={data.get('time')}")

        # Add to power monitor for continuous feedback
        power_monitor.add_reading(power, action)

        if not access_token_global:
            # Mildly inconvenient truth, not sugar-coated.
            print("[Spotify] No access token yet. Log in at /login.")
            return

        # Threshold: 0.5 works well per your live script. Tweak if needed.

        print("power = ", power)

        if action == 'lift' and power > 0.5:
            print("🎯 LIFT detected -> Spotify PAUSE")
            # spotify_pause(access_token_global)
        elif action == 'drop' and power > 0.5:
            print("🔄 DROP detected -> Spotify RESUME")
            # spotify_resume(access_token_global)
        elif action == 'neutral':
            print("😐 Neutral state - no action")
        elif action == 'push' and power > 0.5:
            print("push")

        try:
            # Disable PyAutoGUI fail-safe temporarily for smooth movement
            pyautogui.FAILSAFE = False

            # Start keyboard monitoring thread
            keyboard_thread = threading.Thread(target=monitor_escape_key, daemon=True)
            keyboard_thread.start()

            # Main animation loop
            while not interrupted:
                # Get initial cursor position as circle center
                x, y = pyautogui.position()

                dx = 0
                dy = 0

                if action == 'left' and power > 0.5:
                    print("LEFT")
                    dx -= 1
                if action == 'right' and power > 0.5:
                    print("RIGHT")
                    dx += 1

                if action == 'lift' and power > 0.5:
                    print("lift")
                    dy -= 1
                if action == 'drop' and power > 0.5:
                    print("drop")
                    dy += 1

                if action == 'push' and power > 0.5:
                    print("push")

                # Calculate new position
                x += PIXELS_PER_MOVE * dx
                y += PIXELS_PER_MOVE * dy

                # Maintain frame rate
                time.sleep(DURATION)

        finally:
            # Re-enable PyAutoGUI fail-safe
            pyautogui.FAILSAFE = True


# -----------------------------
# Enhanced Flask Routes
# -----------------------------
@app.route('/')
def home():
    return '''
    <h1>Enhanced Virtual Cursor Demo</h1>
    <h2>Features:</h2>
    <ul>
        <li>🧠 Live power monitoring with visual meter</li>
        <li>🖱️ Original embedded mouse control system</li>
        <li>📊 Power history and statistics</li>
        <li>🎵 Spotify integration (lift/drop commands)</li>
        <li>🎮 Real-time mental command feedback</li>
    </ul>
    <h2>Controls:</h2>
    <ul>
        <li><strong>Mental Commands:</strong> lift, drop, left, right, push</li>
        <li><strong>Power Threshold:</strong> 0.5 (hardcoded as original)</li>
        <li><strong>ESC:</strong> Stop mouse control</li>
    </ul>
    <h2>Status:</h2>
    <p>Power Monitor: <strong>READY</strong></p>
    <a href="/start">🚀 Start Enhanced Demo</a>
    '''

@app.route('/start')
def start_demo():
    try:
        start_emotiv_live()
        return '<h1>✅ Enhanced Demo Started!</h1><p>Check your console for live power feedback.</p><a href="/">← Back</a>'
    except Exception as e:
        return f'<h1>❌ Error starting demo:</h1><p>{str(e)}</p><a href="/">← Back</a>'

@app.route('/stats')
def show_stats():
    """Web endpoint to show power statistics."""
    if not power_monitor.power_history:
        return '<h1>📊 No data available yet</h1><a href="/">← Back</a>'

    avg = power_monitor.get_average_power()
    max_val = power_monitor.get_max_power()
    min_val = min(reading['power'] for reading in power_monitor.power_history)

    return f'''
    <h1>📊 Live Power Statistics</h1>
    <ul>
        <li><strong>Average Power:</strong> {avg:.3f}</li>
        <li><strong>Maximum Power:</strong> {max_val:.3f}</li>
        <li><strong>Minimum Power:</strong> {min_val:.3f}</li>
        <li><strong>Readings Count:</strong> {len(power_monitor.power_history)}</li>
        <li><strong>Mouse Control:</strong> {"ACTIVE" if mouse_controller.active else "INACTIVE"}</li>
    </ul>
    <a href="/stats">🔄 Refresh</a> | <a href="/">← Back</a>
    '''

# -----------------------------
# Boot Enhanced Emotiv Live
# -----------------------------
_emotiv_instance = None

def start_emotiv_live():
    global _emotiv_instance

    if _emotiv_instance is not None:
        print("[Emotiv] Live already started.")
        return

    print("=" * 60)
    print("🚀 STARTING ENHANCED VIRTUAL CURSOR DEMO")
    print("=" * 60)
    print(f"⚙️  Configuration:")
    print(f"   Power Threshold: {POWER_THRESHOLD}")
    print(f"   Action Threshold: {ACTION_THRESHOLD}")
    print(f"   Profile: {PROFILE_NAME}")
    print(f"   Update Rate: {UPDATE_RATE_LIMIT}s")
    print("=" * 60)

    _emotiv_instance = SpotifyLive(EMOTIV_CLIENT_ID, EMOTIV_CLIENT_SECRET)
    _emotiv_instance.start(PROFILE_NAME, HEADSET_ID)

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    _require_config()

    print("🎯 Enhanced Virtual Cursor Demo")
    print("Visit http://127.0.0.1:5000 for web interface")
    print("Or uncomment the line below to start immediately:")

    # Uncomment to start immediately without web interface
    # start_emotiv_live()

    app.run(host="127.0.0.1", port=5000, debug=True)
