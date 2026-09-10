# 🚁 Drone-Based Crowd Monitoring System using ESP32

## 📌 Overview

This project implements a **low-cost, real-time crowd monitoring system** using multiple ESP32 devices mounted on drones.
Each ESP32 passively captures WiFi packets, extracts signal strength (RSSI), and sends data to a backend server, which estimates **device positions** and **crowd density**.

---

## 🎯 Objectives

* Detect nearby devices using WiFi packet sniffing
* Estimate relative position using RSSI-based trilateration
* Visualize detected devices in real-time using a GUI
* Provide crowd density estimation without cameras

---

## ⚙️ System Architecture

```
WiFi Devices → ESP32 Nodes → Backend (Flask) → Trilateration → GUI Visualization
```

---

## 🧩 Components

### 🔹 Hardware

* ESP32 (x3)
* Power Bank (for portability)
* Optional: Drone platform

### 🔹 Software

* Arduino IDE (ESP32 programming)
* Python (Flask backend)
* HTML + JavaScript (GUI)

---

## 📡 Working Principle

### 1. WiFi Packet Sniffing

* ESP32 operates in **promiscuous mode**
* Captures WiFi packets without connecting to devices
* Extracts:

  * MAC address
  * RSSI (signal strength)

---

### 2. RSSI to Distance

Distance is estimated using:

[
d = 10^{\frac{(TxPower - RSSI)}{10n}}
]

Where:

* `TxPower` ≈ -40 dBm
* `n` = environmental factor (2–4)

---

### 3. Trilateration

Using 3 ESP nodes:

[
(x - x_1)^2 + (y - y_1)^2 = r_1^2
]

[
(x - x_2)^2 + (y - y_2)^2 = r_2^2
]

[
(x - x_3)^2 + (y - y_3)^2 = r_3^2
]

Solving these gives the device position **(x, y)**.

---

### 4. Backend Processing

* Receives data from ESPs
* Matches same MAC across devices
* Converts RSSI → distance
* Computes position using trilateration

---

### 5. Visualization

* Real-time GUI using HTML Canvas
* Displays:

  * Red dots for devices
  * (x, y) coordinates
* Updates every second

---

## 📁 Project Structure

```
esp-drone-tracking/
│
├── esp_nodes/
│   ├── esp1/
│   ├── esp2/
│   └── esp3/
│
├── backend/
│   ├── app.py
│   ├── utils.py
│   ├── trilateration.py
│   └── requirements.txt
│
├── config/
│   └── node_positions.json
│
└── README.md
```

---

## 🚀 Setup Instructions

### 🔧 Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

---

### 📡 ESP Setup

1. Open Arduino IDE
2. Upload code to each ESP
3. Set:

```cpp
#define DEVICE_ID 1   // change for each ESP
```

4. Update:

```cpp
const char* serverUrl = "http://<YOUR_IP>:5000/endpoint";
```

---

### 🌐 Open GUI

```
http://<YOUR_IP>:5000/
```

---

## 📊 Example Output

* Backend:

```
Received: {'device_id': 1, 'mac': 'AA:BB:CC', 'rssi': -50}
📍 AA:BB:CC → (8.2, 5.6)
```

* GUI:

  * Red dots representing device positions
  * Live coordinate updates

---

## ⚠️ Challenges

* RSSI fluctuations (noise, reflections)
* MAC randomization (modern devices)
* ESP32 limitation (sniffing + transmission)

---

## ✅ Advantages

* Low-cost solution
* Privacy-preserving (no cameras)
* Portable (drone-based deployment)
* Real-time monitoring

---

## 🔮 Future Scope

* Heatmap visualization
* Kalman filtering for accuracy
* MQTT-based communication
* GPS integration for drones

---

## 👨‍💻 Authors

* Mohit Rajendra Patil

---

## 📌 Conclusion

This project demonstrates a scalable and privacy-friendly approach to **crowd monitoring using wireless signal analysis**, combining embedded systems, networking, and real-time visualization.
