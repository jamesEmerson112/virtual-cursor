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

# -----------------------------
# Flask / Spotify setup
# -----------------------------
load_dotenv()

app = Flask(__name__)
app.secret_key = 'Your Spotify Key'

# Global (in-memory) token for demo purposes
access_token_global = None

# -----------------------------
# Emotiv / Cortex setup copied from your working live.py
# -----------------------------
EMOTIV_CLIENT_ID = os.getenv("CLIENT_ID", "")
EMOTIV_CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")
PROFILE_NAME = os.getenv("PROFILE_NAME", "TRAW spins")
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

    def on_save_profile_done (self, *args, **kwargs):
        print('Save profile', self.profile_name, "successfully")
        self.c.sub_request(['com'])

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
            # Your working script expects 4 values. We'll keep that contract.
            sensitivity_1 = 6
            sensitivity_2 = 1
            sensitivity_3 = 1
            sensitivity_4 = 1
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
# Spotify-integrated Live
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
        global access_token_global
        data = kwargs.get('data', {}) or {}
        action = data.get('action')
        power = data.get('power', 0.0)
        print(f"[COM] action={action} power={power:.2f} time={data.get('time')}")

        if not access_token_global:
            # Mildly inconvenient truth, not sugar-coated.
            print("[Spotify] No access token yet. Log in at /login.")
            return

        # Threshold: 0.5 works well per your live script. Tweak if needed.
        if action == 'lift' and power > 0.5:
            print("🎯 LIFT detected -> Spotify PAUSE")
            # spotify_pause(access_token_global)
        elif action == 'drop' and power > 0.5:
            print("🔄 DROP detected -> Spotify RESUME")
            # spotify_resume(access_token_global)
        elif action == 'neutral':
            print("😐 Neutral state - no action")


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

                if action == 'left' and power > 0.5:
                    dx -= 1
                if action == 'right' and power > 0.5:
                    dx += 1

                if action == 'lift' and power > 0.5:
                    dy -= 1
                if action == 'drop' and power > 0.5:
                    dy += 1

                # Calculate new position
                x += PIXELS_PER_MOVE * dx
                y += PIXELS_PER_MOVE * dy

                # Maintain frame rate
                time.sleep(DURATION)

        finally:
            # Re-enable PyAutoGUI fail-safe
            pyautogui.FAILSAFE = True



# -----------------------------
# Boot Emotiv Live (using the working flow)
# -----------------------------
_emotiv_instance = None

def start_emotiv_live():
    global _emotiv_instance

    if _emotiv_instance is not None:
        print("[Emotiv] Live already started.")
        return
    print("[Emotiv] Starting live session…")
    _emotiv_instance = SpotifyLive(EMOTIV_CLIENT_ID, EMOTIV_CLIENT_SECRET)
    _emotiv_instance.start(PROFILE_NAME, HEADSET_ID)

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

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    _require_config()
    # Note: We kick off Emotiv after Spotify login so commands can do something immediately.
    # If you prefer to start Emotiv immediately, uncomment the next line:
    # start_emotiv_live()
    app.run(host="127.0.0.1", port=5000, debug=True)