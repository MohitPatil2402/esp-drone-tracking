import json
import os
import time
import threading
from collections import defaultdict, deque

from trilateration import rssi_to_distance, trilaterate_ls

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, '..', 'config', 'node_positions.json')
LOG_PATH    = os.path.join(BASE_DIR, '..', 'data', 'logs.json')

with open(CONFIG_PATH) as _f:
    NODE_POS = json.load(_f)

RSSI_WINDOW = 5    # readings to average per (mac, node) pair
HISTORY_LEN = 30   # max position trail length per device
STALE_SEC   = 60   # seconds before a device is considered gone

_lock  = threading.Lock()
_rssi  = defaultdict(lambda: defaultdict(lambda: deque(maxlen=RSSI_WINDOW)))
_meta  = {}        # mac -> {first_seen, last_seen, node_rssi}
_pos   = {}        # mac -> {x, y, ts}
_hist  = defaultdict(lambda: deque(maxlen=HISTORY_LEN))


def process_data(data):
    """
    Ingest one RSSI reading from an ESP node, smooth it, and attempt to
    compute / update the device position via weighted least-squares trilateration.
    Returns the (x, y) position tuple on success, else None.
    """
    mac       = data["mac"]
    device_id = str(data["device_id"])
    rssi      = int(data["rssi"])
    now       = time.time()

    with _lock:
        buf = _rssi[mac][device_id]
        buf.append(rssi)
        avg_rssi = sum(buf) / len(buf)

        if mac not in _meta:
            _meta[mac] = {"first_seen": now, "node_rssi": {}}
        m = _meta[mac]
        m["last_seen"]            = now
        m["node_rssi"][device_id] = round(avg_rssi, 1)

        needed = list(NODE_POS.keys())
        if not all(k in m["node_rssi"] for k in needed):
            return None

        positions_list = [NODE_POS[k] for k in needed]
        distances      = [rssi_to_distance(m["node_rssi"][k]) for k in needed]

        try:
            pos = trilaterate_ls(positions_list, distances)
        except Exception as e:
            print(f"[trilaterate] {mac}: {e}")
            return None

        if pos:
            _pos[mac] = {"x": pos[0], "y": pos[1], "ts": now}
            _hist[mac].append({"x": pos[0], "y": pos[1]})
            _log_async(mac, pos, m["node_rssi"])

        return pos


def get_positions():
    now = time.time()
    with _lock:
        return {
            mac: {**p, "age": round(now - p["ts"], 1)}
            for mac, p in _pos.items()
            if now - p["ts"] < STALE_SEC
        }


def get_devices():
    now = time.time()
    with _lock:
        out = {}
        for mac, m in _meta.items():
            age = now - m.get("last_seen", now)
            if age < STALE_SEC:
                out[mac] = {
                    "node_rssi":  dict(m["node_rssi"]),
                    "first_seen": round(m["first_seen"]),
                    "last_seen":  round(m["last_seen"]),
                    "age":        round(age, 1),
                }
        return out


def get_history(mac):
    with _lock:
        return list(_hist.get(mac, []))


def get_nodes():
    return NODE_POS


def _log_async(mac, pos, rssi_data):
    threading.Thread(target=_write_log, args=(mac, pos, rssi_data), daemon=True).start()


def _write_log(mac, pos, rssi_data):
    entry = {"ts": time.time(), "mac": mac, "pos": list(pos), "rssi": dict(rssi_data)}
    try:
        try:
            with open(LOG_PATH) as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []
        logs.append(entry)
        if len(logs) > 1000:
            logs = logs[-1000:]
        with open(LOG_PATH, 'w') as f:
            json.dump(logs, f)
    except Exception as e:
        print(f"[log] {e}")
