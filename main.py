import os
import time
import threading
from dotenv import load_dotenv

import pyautogui
import cortex
from cortex import Cortex

# -----------------------------
# Emotiv / Cortex setup copied from your working live.py
# -----------------------------
# CHANGE THESE 3 to your stuff
# EMOTIV_CLIENT_ID = "jzf127BybqiWOFRWjSxowugu69fpezjdcsjFHV2v"
# EMOTIV_CLIENT_SECRET = "zIn8t5PMBpX50xvIHUCpwNpaKl20ZFEFnBY6duMN5Ycth6s78W5a45VMDZSlkGcFS5Wqtm0jPhJhnl0k9Fc2cAtoT1evCsI1BA1UhUARNSiWWcV2JifXnfKps1dlTOEx"
# PROFILE_NAME = "p"

EMOTIV_CLIENT_ID="82AJi1KIYQvfc5vCK1jMEOGZEGyMPqA8Rqpvojfe"
EMOTIV_CLIENT_SECRET="Zjdote3b8w2hxNDaearMcinzfUDXe5yeJPozmuEolPZ2ptTs8unFyu3WmBN0w85hzUCelWtBcOl33jO4vD1iSVEw9R524DWt0WfbXo7bUUkScHgAMpjzAcegXNepb1cC"
PROFILE_NAME="James"
HEADSET_ID="INSIGHT2-A3D20A08"

SPEED = 50
timeDelay = 3  # seconds to ignore BCI commands after mouse movement
# HEADSET_ID = os.getenv("HEADSET_ID", "")  # optional


mouse_x, mouse_y = 0, 0
last_mouse_movement = 0



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
        self.c.bind(new_met_data=self.on_new_met_data)
        self.c.bind(new_pow_data=self.on_new_pow_data)
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
        self.c.sub_request(['com', 'met', 'pow'])


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
    def on_new_met_data(self, *args, **kwargs):
        data = kwargs.get('data', {})
        metrics = data.get('met', [])
        timestamp = data.get('time')

        # The order of metrics is fixed: ["stress", "engagement", "interest", "relaxation", "excitement", "focus"]
        if metrics:
            print(f"[MET] time={timestamp} stress={metrics[0]:.2f} engage={metrics[1]:.2f} "
                f"interest={metrics[2]:.2f} relax={metrics[3]:.2f} "
                f"excite={metrics[4]:.2f} focus={metrics[5]:.2f}")

    def on_new_pow_data(self, *args, **kwargs):
        data = kwargs.get('data', {})
        powers = data.get('pow', [])
        timestamp = data.get('time')

        # Band powers: ["theta", "alpha", "lowBeta", "highBeta", "gamma"]
        if powers:
            print(f"[POW] time={timestamp} theta={powers[0]:.2f} alpha={powers[1]:.2f} "
                f"lowBeta={powers[2]:.2f} highBeta={powers[3]:.2f} gamma={powers[4]:.2f}")


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
      - 'push'  (power > 0.5) -> pause
      - 'drop'  (power > 0.5) -> resume
      - 'neutral' -> no-op
    Adjust thresholds/action mapping as needed.
    """
    def __init__(self, app_client_id, app_client_secret, **kwargs):
        super().__init__(app_client_id, app_client_secret, **kwargs)

    def on_new_com_data(self, *args, **kwargs):
        global mouse_x, mouse_y
        global last_mouse_movement


        data = kwargs.get('data', {}) or {}
        action = data.get('action')
        power = data.get('power', 0.0)
        print(f"[COM] action={action} power={power:.2f} time={data.get('time')}")

        # If mouse moved in last 5 seconds, ignore BCI commands to avoid conflicts.
        if last_mouse_movement > time.time() - timeDelay:
            return

        mouse_x, mouse_y = pyautogui.position()
        displacement = round(SPEED * power)
        # Threshold: 0.5 works well per your live script. Tweak if needed.

        if action == 'push':
            print("PUUUUSH")
            mouse_y -= displacement

        elif action == 'pull':
            mouse_y += displacement

        elif action == 'left':
            mouse_x -= displacement

        elif action == 'right':
            mouse_x += displacement

        elif action == 'drop':
            pyautogui.click()

        pyautogui.moveTo(mouse_x, mouse_y, duration=0)

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

def mouse_checking_thread():
    global mouse_x, mouse_y, last_mouse_movement
    mouse_x, mouse_y = pyautogui.position()

    while True:
        new_mouse_x, new_mouse_y = pyautogui.position()

        if (new_mouse_x, new_mouse_y) != (mouse_x, mouse_y):
            mouse_x, mouse_y = new_mouse_x, new_mouse_y

            last_mouse_movement = time.time()

        time.sleep(0.1)

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    thread = threading.Thread(target=mouse_checking_thread)
    thread.start()

    _require_config()
    # Note: We kick off Emotiv after Spotify login so commands can do something immediately.
    # If you prefer to start Emotiv immediately, uncomment the next line:
    start_emotiv_live()
    # app.run(host="127.0.0.1", port=5000, debug=True)