from collections import defaultdict
from trilateration import rssi_to_distance, trilaterate
import json
import time

with open("../config/node_positions.json") as f:
    NODE_POS = json.load(f)

device_data = defaultdict(dict)
positions = {}

TIME_WINDOW = 10  # seconds

def process_data(data):
    mac = data["mac"]
    device_id = str(data["device_id"])
    rssi = data["rssi"]
    now = time.time()

    device_data[mac][device_id] = {
        "rssi": rssi,
        "time": now
    }

    needed = ["1", "2", "3"]
    if all(d in device_data[mac] for d in needed):
        times_ok = all(now - device_data[mac][d]["time"] <= TIME_WINDOW for d in needed)

        if times_ok:
            try:
                r1 = rssi_to_distance(device_data[mac]["1"]["rssi"])
                r2 = rssi_to_distance(device_data[mac]["2"]["rssi"])
                r3 = rssi_to_distance(device_data[mac]["3"]["rssi"])

                p1 = NODE_POS["1"]
                p2 = NODE_POS["2"]
                p3 = NODE_POS["3"]

                pos = trilaterate(p1, p2, p3, r1, r2, r3)

                if pos:
                    positions[mac] = pos
                    print(f"📍 {mac} -> {pos}")

            except Exception as e:
                print("Error:", e)

def get_positions():
    return positions