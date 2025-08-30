# EMOTIV Cortex API — Python-Oriented Cheat Sheet
_Last updated: 2025-08-30 17:13 UTC_


> Scope: concise, implementation-ready API map for building Python backends with EMOTIV Cortex. Focus is on **what to call** and **in which order** when using the official JSON‑RPC **WebSocket** API from Python. (This is API-centric; choose any Python WebSocket client.)

---

## 1) Connection & Transport
- **Protocol:** JSON‑RPC over **WSS** (secure WebSocket).
- **Default endpoint (desktop):** `wss://localhost:6868`
- **Remote use (e.g., Jetson/RPi hosting Cortex):** WSS to the device’s IP/DNS on port **6868**.
- **Note:** Only **secure** WebSocket is supported (no `ws://`).

**Minimal lifecycle (conceptual):**
1. Open WSS.
2. Send JSON‑RPC requests (see methods below).
3. Receive JSON responses and **stream frames** after `subscribe`.

---

## 2) Core API Flow (happy path)
The usual order of calls for a streaming app:

1. `getCortexInfo` → sanity/version check.  
2. **Authentication:** `getUserLogin` → `requestAccess`/`hasAccessRight` → `authorize` (get **cortexToken**).  
3. **Headset:** `queryHeadsets` (and optionally `controlDevice` to connect).  
4. **Session:** `createSession` (with a specific headset). Then `updateSession` to **activate** (required for raw EEG).  
5. **Data:** `subscribe` to one or more streams; process frames.  
6. (Optional) **Training/Profile**: `getDetectionInfo` → `training` → `setupProfile` / `queryProfile`.  
7. (Optional) **Recording/Markers**: `createRecord` / `injectMarker` / `stopRecord` → `exportRecord`.  
8. **Cleanup:** `unsubscribe` / `updateSession` (close).

---

## 3) Authentication & Tokens
- `getUserLogin` — info about current login state in EMOTIV App/Launcher.
- `requestAccess` — request user approval for our App ID.
- `hasAccessRight` — check whether access was granted previously.
- `authorize` — returns **cortexToken**, used by most protected calls.
- `generateNewToken` — refresh/rotate token when needed.
- `getUserInformation` — user/account context.
- `getLicenseInfo` — check data permissions (e.g., raw EEG availability).

**Inputs (common):**
- `clientId`, `clientSecret` (from EMOTIV Developer portal).
- **Always pass** `cortexToken` to protected methods once authorized.

---

## 4) Headset Management
- `queryHeadsets` — discover headsets and their status (`discovered`, `connected`, etc.).
- `controlDevice` — connect/disconnect to a given headset when needed.
- `updateHeadset` — tweak headset parameters.
- `updateHeadsetCustomInfo` — store custom label/metadata on a headset.
- `syncWithHeadsetClock` — time-align (useful for precise timing pipelines).
- **Headset object** — schema reference for fields (id, sensors, status, etc.).

---

## 5) Sessions
- `createSession` — open a session bound to a **specific headset**.
- `updateSession` — **activate** or **close** the session.
- `querySessions` — list sessions for the current application.
- **Session object** — schema reference.

> Tip: For **raw EEG** (`eeg` stream) the session generally must be **activated** and license must permit it.

---

## 6) Data Subscription
- `subscribe` — begin receiving **data sample objects** for selected streams.
- `unsubscribe` — stop selected streams.

**Available streams:**  
- `eeg` — raw EEG (premium license).  
- `mot` — motion/IMU.  
- `dev` — device telemetry (battery, RSSI, contact).  
- `eq` — EEG contact quality per sensor.  
- `pow` — frequency band powers.  
- `met` — performance metrics.  
- `com` — mental commands.  
- `fac` — facial expressions.  
- `sys` — system/training events.

**Data sample object (generic):**
```
{ "<stream>": [...values...], "sid": "<session-id>", "time": 1725012345.678 }
```
> Column layout for `<stream>` is provided in the `subscribe` result (the `cols` array per stream).

---

## 7) Recording & Export
- `createRecord` — start a named recording (ties to a session/headset).
- `stopRecord` — stop recording; retrieve record id(s).
- `updateRecord` / `deleteRecord` — manage metadata/lifecycle.
- `queryRecords` / `getRecordInfos` — enumerate and inspect recordings.
- `exportRecord` — export to **EDF** or **CSV** (streams per license).
- `requestToDownloadRecordData` — async export retrieval utility.
- `configOptOut` — configure data handling opt-out.

---

## 8) Markers (Event Tagging)
- `injectMarker` — push a time-stamped marker into the active session.
- `updateMarker` — edit marker metadata post‑hoc.
- **Marker object** — schema reference.

> Use markers for stimuli onsets, robot actions, or user events to align downstream analysis.

---

## 9) Subjects (Optional, for studies)
- `createSubject`, `updateSubject`, `deleteSubjects`, `querySubjects`.
- `getDemographicAttributes` — available demographics fields.
- **Subject object** — schema reference.

---

## 10) BCI: Profiles, Training, Detections
- `getDetectionInfo` — discover supported actions/controls for a detection:
  - **Detections:** `"mentalCommand"`, `"facialExpression"`.
- `training` — control the training lifecycle:
  - `status`: `"start"`, `"accept"`, `"reject"`, `"reset"`, `"erase"`.
  - `action`: depends on detection (e.g., `"push"`, `"left"`, `"smile"`, etc.).
- `setupProfile` — create/load/unload/save profiles to persist training.
- `queryProfile`, `getCurrentProfile`, `loadGuestProfile` — profile management.

**Advanced BCI controls:**
- `getTrainedSignatureActions`, `getTrainingTime`  
- `facialExpressionSignatureType`, `facialExpressionThreshold`  
- `mentalCommandActiveAction`, `mentalCommandBrainMap`, `mentalCommandGetSkillRating`, `mentalCommandTrainingThreshold`, `mentalCommandActionSensitivity`

---

## 11) Warnings & Errors
- **Warning Objects:** e.g., streams auto‑canceled on disconnect; session auto‑closed; user login/logout; profile load/unload events, EULA acceptance.
- **Error Codes:** exhaustive map in docs—include licensing, session limits, invalid params, etc.
- **Typical recoveries:** reconnect WSS, refresh token, re‑authorize, re‑create session, re‑subscribe.

---

## 12) Typical Python App Sequence (pseudocode-ish, transport‑agnostic)
1. **Connect** WSS → `getCortexInfo`  
2. **Auth** → `getUserLogin` → `requestAccess` (first run) → `authorize` → `cortexToken`  
3. **Headset** → `queryHeadsets` → `controlDevice` (if needed)  
4. **Session** → `createSession` (bind headset) → `updateSession` (`status="active"`)  
5. **Stream** → `subscribe` to `[ "com", "fac", "met", ... ]`  
6. **(Optional)** `createRecord` and periodic `injectMarker`  
7. **Training/Profiles (optional)** → `getDetectionInfo` → `training` → `setupProfile`  
8. **Tear‑down** → `unsubscribe` → `updateSession` (`status="close"`)

---

## 13) Stream Notes & Practical Tips
- Start with **`com`** (mental commands) and **`fac`** (facial expressions) for interactive control; mix **`met`** for UX feedback (engagement/relaxation).  
- Add **debounce/hysteresis** to avoid command flicker (`"hold for N ms"` before action).  
- For raw **`eeg`**, ensure license permits and **session is active**.  
- Use **markers** to correlate app events with EEG/metrics for post‑hoc analysis or demos.  
- Keep an eye on **warning objects**; treat them as control‑plane signals to re‑sync.

---

## 14) Glossary (fast recall)
- **cortexToken** — bearer token from `authorize` (pass to protected calls).
- **Session** — binding between app and a headset; required for streaming.
- **Profile** — stored training signatures for BCI detections.
- **Streams** — `{eeg, mot, dev, eq, pow, met, com, fac, sys}`.
- **Cols** — column names returned by `subscribe` (interpret values in frames).

---

## 15) References
- Official docs: Cortex API (method index, flows, stream schemas).  
- Example code: `Emotiv/cortex-example` (Python directory) for end‑to‑end usage patterns.


---

# 16) Python Call Examples — Minimal, LLM‑Friendly (2025-08-30 17:25 UTC)


Below are **copy‑ready** snippets showing an end‑to‑end Cortex session in Python, plus **raw JSON‑RPC** request/response templates.
We keep these small and explicit so an LLM (or a teammate) can assemble a backend quickly.

## 16.1 Install Options

```bash
# Option A: asyncio websockets (preferred for servers)
pip install websockets

# Option B: synchronous client (works in scripts/REPL)
pip install websocket-client
```
> Pick **one** approach below (A or B).

---

## 16.2 Option A — Asyncio + websockets

```python
import asyncio, json, itertools, ssl
import websockets

WSS_URL = "wss://localhost:6868"

def _id_counter():
    return itertools.count(1)

async def rpc(ws, method, params, idgen):
    req = {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": next(idgen)}
    await ws.send(json.dumps(req))
    while True:
        raw = await ws.recv()
        msg = json.loads(raw)
        # Slice out the response matching our id
        if msg.get("id") == req["id"]:
            if "error" in msg:
                raise RuntimeError(f"{method} error: {msg['error']}")
            return msg.get("result")
        else:
            # Stream frames or system events arrive here. Handle or stash as needed.
            # print("STREAM/EVENT:", msg)
            pass

async def stream_loop(ws):
    # Example of reading stream frames continuously
    while True:
        msg = json.loads(await ws.recv())
        if "com" in msg:    # mental command stream
            # msg['com'] is a list of values in the order given by 'cols' from subscribe result
            # Typically includes action + power/confidence
            print("COM:", msg["com"])
        elif "fac" in msg:  # facial expression stream
            print("FAC:", msg["fac"])
        elif "met" in msg:  # performance metrics
            print("MET:", msg["met"])
        # ... handle other streams (eeg, mot, pow, eq, dev) as needed

async def main(client_id, client_secret, streams=("com", "fac", "met")):
    ssl_ctx = ssl.create_default_context()
    async with websockets.connect(WSS_URL, ssl=ssl_ctx) as ws:
        ids = _id_counter()

        # 1) Info (optional sanity)
        info = await rpc(ws, "getCortexInfo", {}, ids)
        print("Cortex:", info)

        # 2) Auth: requestAccess (first run), authorize -> cortexToken
        # If access already granted, requestAccess is a no-op.
        await rpc(ws, "requestAccess", {"clientId": client_id, "clientSecret": client_secret}, ids)
        auth = await rpc(ws, "authorize", {"clientId": client_id, "clientSecret": client_secret}, ids)
        token = auth["cortexToken"]

        # 3) Headset discovery (connect if needed)
        hs_list = await rpc(ws, "queryHeadsets", {}, ids)
        assert hs_list, "No headsets found"
        headset_id = hs_list[0]["id"]
        # Optionally: await rpc(ws, "controlDevice", {"command": "connect", "headset": headset_id}, ids)

        # 4) Create + activate session
        sess = await rpc(ws, "createSession", {"cortexToken": token, "headset": headset_id, "status": "open"}, ids)
        sid = sess["id"]
        await rpc(ws, "updateSession", {"cortexToken": token, "session": sid, "status": "active"}, ids)

        # 5) Subscribe to streams
        sub = await rpc(ws, "subscribe", {"cortexToken": token, "session": sid, "streams": list(streams)}, ids)
        print("Subscribed:", sub)  # Contains 'cols' per stream

        # (Optional) Start a recording
        # rec = await rpc(ws, "createRecord", {"cortexToken": token, "session": sid, "title": "demo"}, ids)

        # 6) Read stream frames
        await stream_loop(ws)

        # (On shutdown) Unsubscribe + close session
        # await rpc(ws, "unsubscribe", {"cortexToken": token, "session": sid, "streams": list(streams)}, ids)
        # await rpc(ws, "updateSession", {"cortexToken": token, "session": sid, "status": "close"}, ids)

if __name__ == "__main__":
    # Replace with our EMOTIV App credentials
    asyncio.run(main(client_id="YOUR_CLIENT_ID", client_secret="YOUR_CLIENT_SECRET"))
```

### Action mapping (Arduino serial) — add-on snippet
```python
import serial, time

ser = serial.Serial("/dev/ttyACM0", 115200, timeout=0)

def send_robot(cmd_char: str):
    ser.write((cmd_char + "\n").encode())

# Example usage inside stream_loop:
# if detected_action == "push" and power > 0.6 for >200ms -> send_robot("F")
```

---

## 16.3 Option B — Synchronous (websocket-client)

```python
import json, itertools, ssl
from websocket import create_connection

WSS_URL = "wss://localhost:6868"

def _id_counter(): return itertools.count(1)

def rpc(ws, method, params, ids):
    req = {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": next(ids)}
    ws.send(json.dumps(req))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == req["id"]:
            if "error" in msg:
                raise RuntimeError(f"{method} error: {msg['error']}")
            return msg.get("result")
        else:
            # Stream/event frame; handle if needed
            pass

def main(client_id, client_secret):
    ws = create_connection(WSS_URL, sslopt={"cert_reqs": ssl.CERT_REQUIRED})
    ids = _id_counter()

    info = rpc(ws, "getCortexInfo", {}, ids)
    rpc(ws, "requestAccess", {"clientId": client_id, "clientSecret": client_secret}, ids)
    auth = rpc(ws, "authorize", {"clientId": client_id, "clientSecret": client_secret}, ids)
    token = auth["cortexToken"]

    hs = rpc(ws, "queryHeadsets", {}, ids)
    headset_id = hs[0]["id"]

    sess = rpc(ws, "createSession", {"cortexToken": token, "headset": headset_id, "status": "open"}, ids)
    sid = sess["id"]
    rpc(ws, "updateSession", {"cortexToken": token, "session": sid, "status": "active"}, ids)

    rpc(ws, "subscribe", {"cortexToken": token, "session": sid, "streams": ["com", "fac", "met"]}, ids)

    while True:
        msg = json.loads(ws.recv())
        if "com" in msg:
            print("COM:", msg["com"])
        elif "fac" in msg:
            print("FAC:", msg["fac"])
        elif "met" in msg:
            print("MET:", msg["met"])

if __name__ == "__main__":
    main(client_id="YOUR_CLIENT_ID", client_secret="YOUR_CLIENT_SECRET")
```

---

## 16.4 Raw JSON‑RPC Templates (Requests / Responses)

> Replace placeholders in ALL CAPS. Numeric `id` can be any unique integer per request.

**Get info**
```json
{ "jsonrpc": "2.0", "method": "getCortexInfo", "params": {}, "id": 1 }
```
**Response (example)**
```json
{ "id": 1, "jsonrpc": "2.0", "result": { "apiVersion": "3.x.x", "serverVersion": "x.y.z" } }
```

**Request access (first run)**
```json
{ "jsonrpc": "2.0", "method": "requestAccess", "params": { "clientId": "APP_ID", "clientSecret": "APP_SECRET" }, "id": 2 }
```

**Authorize (get cortexToken)**
```json
{ "jsonrpc": "2.0", "method": "authorize", "params": { "clientId": "APP_ID", "clientSecret": "APP_SECRET" }, "id": 3 }
```
**Response**
```json
{ "id": 3, "jsonrpc": "2.0", "result": { "cortexToken": "TOKEN", "expires_in": 86400 } }
```

**Query headsets**
```json
{ "jsonrpc": "2.0", "method": "queryHeadsets", "params": {}, "id": 4 }
```

**Create + activate session**
```json
{ "jsonrpc": "2.0", "method": "createSession", "params": { "cortexToken": "TOKEN", "headset": "HEADSET_ID", "status": "open" }, "id": 5 }
```
```json
{ "jsonrpc": "2.0", "method": "updateSession", "params": { "cortexToken": "TOKEN", "session": "SESSION_ID", "status": "active" }, "id": 6 }
```

**Subscribe to streams**
```json
{ "jsonrpc": "2.0", "method": "subscribe", "params": { "cortexToken": "TOKEN", "session": "SESSION_ID", "streams": ["com","fac","met"] }, "id": 7 }
```
**Response (example — includes column metadata)**
```json
{
  "id": 7, "jsonrpc": "2.0",
  "result": {
    "com": { "cols": ["time", "action", "power"] },
    "fac": { "cols": ["time", "eyeAct", "upperFaceAct", "lowerFaceAct", "eyebrow", "smile", "clench", "smirk", "laugh"] },
    "met": { "cols": ["time", "engagement", "excitement", "longTermExcitement", "relaxation", "interest", "stress"] }
  }
}
```

**Example stream frame (mental command)**
```json
{ "com": [1725012345.678, "push", 0.62], "sid": "SESSION_ID", "time": 1725012345.678 }
```

**Inject a marker**
```json
{ "jsonrpc": "2.0", "method": "injectMarker", "params": { "cortexToken": "TOKEN", "session": "SESSION_ID", "label": "robot_forward", "value": "FWD", "port": "python", "time": 1725012345.700 }, "id": 8 }
```

**Training (start → accept)**
```json
{ "jsonrpc": "2.0", "method": "training", "params": { "cortexToken": "TOKEN", "detection": "mentalCommand", "action": "push", "status": "start", "session": "SESSION_ID" }, "id": 9 }
```
```json
{ "jsonrpc": "2.0", "method": "training", "params": { "cortexToken": "TOKEN", "detection": "mentalCommand", "action": "push", "status": "accept", "session": "SESSION_ID" }, "id": 10 }
```

**Profiles (save)**
```json
{ "jsonrpc": "2.0", "method": "setupProfile", "params": { "cortexToken": "TOKEN", "headset": "HEADSET_ID", "profile": "demo_profile", "status": "save" }, "id": 11 }
```

**Unsubscribe + close**
```json
{ "jsonrpc": "2.0", "method": "unsubscribe", "params": { "cortexToken": "TOKEN", "session": "SESSION_ID", "streams": ["com","fac","met"] }, "id": 12 }
```
```json
{ "jsonrpc": "2.0", "method": "updateSession", "params": { "cortexToken": "TOKEN", "session": "SESSION_ID", "status": "close" }, "id": 13 }
```

---

## 16.5 Minimal Debounce / Threshold Pattern (Python pseudocode)

```python
last_action, last_ts = None, 0.0
HOLD_MS = 250
THRESH = 0.6  # command power

def decide(action, power, now_ms):
    global last_action, last_ts
    if power >= THRESH:
        if action == last_action and (now_ms - last_ts) >= HOLD_MS:
            last_ts = now_ms
            return action   # stable signal
        else:
            last_action = action
            last_ts = now_ms
    return None
```

---

## 16.6 Safety Override (Facial Expression → STOP)

```python
# If a "smile" or "clench" is detected with sufficient intensity, send STOP to robot.
if fac_detects_smile_above_threshold(msg):
    send_robot("S")   # stop
```

---

## 16.7 Errors & Reconnect Skeleton

```python
async def safe_call(call, retries=3):
    for i in range(retries):
        try:
            return await call()
        except Exception as e:
            if i == retries - 1:
                raise
            await asyncio.sleep(0.5 * (i + 1))  # backoff

# Apply to authorize/createSession/subscribe, etc.
```

---

## 16.8 Tiny HTTP/WebSocket Status (Optional)
If a judge/audience needs a live status panel, serve one from Python or pipe to Node‑RED dashboard:

```python
# Python side: expose a /status JSON endpoint with current action/power
# Node-RED side: poll that endpoint or receive via WebSocket and render gauges.
```

---

> End of examples. Keep this section close to the top of our repo for quickest onboarding.
