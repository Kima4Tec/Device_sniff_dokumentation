"""
Heatmap over MQTT-positioner
Kræver: pip install paho-mqtt matplotlib numpy

Kør: python heatmap.py
"""

import json
import threading
import ssl
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.animation import FuncAnimation
from collections import defaultdict
import paho.mqtt.client as mqtt
from datetime import datetime

# ===================== KONFIGURATION =====================
MQTT_HOST   = ""
MQTT_PORT   = 8883
MQTT_USER   = ""
MQTT_PASS   = ""
MQTT_TOPIC  = "/devices/device03/positions"
CA_CERT     = "ca_cert.h"

# Rum-dimensioner i meter
ROOM_W = 5.0
ROOM_H = 4.0

# Sensor-positioner (skal matche ESP32-koden)
SENSORS = [
    {"id": "ESP32_A", "x": 0.0, "y": 0.0, "color": "orange"},
    {"id": "ESP32_B", "x": 5.0, "y": 0.0, "color": "orange"},
    {"id": "ESP32_C", "x": 0.0, "y": 4.0, "color": "mediumpurple"},
]

# Heatmap opløsning (jo højere jo glattere men langsommere)
GRID_RES    = 100
# Heatmap radius per enhed (meter) — større = mere udvasket
HEAT_RADIUS = 0.8
# Heatmap falmer med denne faktor per opdatering
HEAT_DECAY  = 0.92
# Opdateringsinterval (ms)
UPDATE_MS   = 500

# ===================== DELT STATE =====================
lock         = threading.Lock()
positions    = {}   # devId → {"x": float, "y": float, "ts": str}
heatmap_grid = np.zeros((GRID_RES, GRID_RES))
msg_count    = 0

# ===================== MQTT CALLBACKS =====================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[MQTT] Forbundet til {MQTT_HOST}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        print(f"[MQTT] Abonnerer på {MQTT_TOPIC}")
    else:
        print(f"[MQTT] Forbindelsesfejl, rc={rc}")

def on_message(client, userdata, msg):
    global msg_count
    try:
        data = json.loads(msg.payload.decode())
        dev_id = data.get("devId")
        x      = float(data.get("x", 0))
        y      = float(data.get("y", 0))
        ts     = data.get("ts", "unknown")

        if not dev_id:
            return

        # Klem koordinater inden for rum
        x = max(0.0, min(ROOM_W, x))
        y = max(0.0, min(ROOM_H, y))

        with lock:
            positions[dev_id] = {"x": x, "y": y, "ts": ts}
            msg_count += 1

            # Tilføj til heatmap-grid
            gx = int((x / ROOM_W) * (GRID_RES - 1))
            gy = int((y / ROOM_H) * (GRID_RES - 1))

            # Gaussian blob rundt om position
            radius_cells = int((HEAT_RADIUS / ROOM_W) * GRID_RES)
            for dx in range(-radius_cells, radius_cells + 1):
                for dy in range(-radius_cells, radius_cells + 1):
                    nx, ny = gx + dx, gy + dy
                    if 0 <= nx < GRID_RES and 0 <= ny < GRID_RES:
                        dist = np.sqrt(dx**2 + dy**2)
                        val  = np.exp(-0.5 * (dist / (radius_cells * 0.4))**2)
                        heatmap_grid[ny, nx] += val

        print(f"[MSG #{msg_count}] {dev_id} @ ({x:.2f}, {y:.2f})  ts={ts}")

    except Exception as e:
        print(f"[MQTT] Parse fejl: {e} — payload: {msg.payload}")

def on_disconnect(client, userdata, rc):
    print(f"[MQTT] Afbrudt (rc={rc}) — genopretter...")

# ===================== MQTT SETUP =====================
def start_mqtt():
    client = mqtt.Client()
    client.on_connect    = on_connect
    client.on_message    = on_message
    client.on_disconnect = on_disconnect

    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASS)

    # TLS
    client.tls_set(
        ca_certs   = CA_CERT,
        tls_version = ssl.PROTOCOL_TLS
    )
    client.tls_insecure_set(False)

    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()
    return client

# ===================== PLOT SETUP =====================
fig, ax = plt.subplots(figsize=(9, 7))
fig.patch.set_facecolor("#0e1117")
ax.set_facecolor("#161b24")

plt.title("Positionsoverblik", color="white", fontsize=13, pad=12)
ax.set_xlim(0, ROOM_W)
ax.set_ylim(0, ROOM_H)
ax.set_xlabel("Meter (x)", color="#6b7a99")
ax.set_ylabel("Meter (y)", color="#6b7a99")
ax.tick_params(colors="#6b7a99")
for spine in ax.spines.values():
    spine.set_edgecolor("#242b38")

# Grid
ax.set_xticks(np.arange(0, ROOM_W + 1, 1))
ax.set_yticks(np.arange(0, ROOM_H + 1, 1))
ax.grid(color="#1e2530", linewidth=0.5)

# Heatmap image
heat_img = ax.imshow(
    heatmap_grid,
    origin    = "lower",
    extent    = [0, ROOM_W, 0, ROOM_H],
    cmap      = "inferno",
    alpha     = 0.75,
    vmin      = 0,
    vmax      = 5,
    aspect    = "auto",
    interpolation = "gaussian",
)

# Sensor-markører
for s in SENSORS:
    ax.plot(s["x"], s["y"], "s", color=s["color"], markersize=10, zorder=5)
    ax.annotate(s["id"], (s["x"], s["y"]),
        textcoords="offset points", xytext=(6, 6),
        color=s["color"], fontsize=8)

# Device-punkter og labels (opdateres i animation)
device_scatter = ax.scatter([], [], c="cyan", s=60, zorder=6, edgecolors="white", linewidths=0.5)
device_labels  = []

# Status-tekst
status_text = ax.text(
    0.01, 0.98, "", transform=ax.transAxes,
    color="#6b7a99", fontsize=8, va="top",
    fontfamily="monospace"
)

# ===================== ANIMATION =====================
def update(frame):
    global heatmap_grid

    with lock:
        # Fade heatmap
        heatmap_grid *= HEAT_DECAY
        heat_img.set_data(heatmap_grid.copy())
        heat_img.set_clim(vmin=0, vmax=max(1.0, heatmap_grid.max()))

        # Opdater device-punkter
        pos_snapshot = dict(positions)
        count        = msg_count

    # Ryd gamle labels
    for lbl in device_labels:
        lbl.remove()
    device_labels.clear()

    if pos_snapshot:
        xs = [p["x"] for p in pos_snapshot.values()]
        ys = [p["y"] for p in pos_snapshot.values()]
        device_scatter.set_offsets(np.c_[xs, ys])

        for dev_id, p in pos_snapshot.items():
            lbl = ax.annotate(
                dev_id,
                (p["x"], p["y"]),
                textcoords="offset points",
                xytext=(5, 5),
                color="cyan",
                fontsize=7,
                fontfamily="monospace",
            )
            device_labels.append(lbl)
    else:
        device_scatter.set_offsets(np.empty((0, 2)))

    status_text.set_text(
        f"Enheder: {len(pos_snapshot)}  |  Beskeder: {count}  |  {datetime.now().strftime('%H:%M:%S')}"
    )

    return heat_img, device_scatter, status_text

# ===================== MAIN =====================
if __name__ == "__main__":
    print("=" * 48)
    print("  Heatmap starter")
    print(f"  Broker : {MQTT_HOST}:{MQTT_PORT}")
    print(f"  Topic  : {MQTT_TOPIC}")
    print(f"  Rum    : {ROOM_W} x {ROOM_H} m")
    print("=" * 48)

    mqtt_client = start_mqtt()

    ani = FuncAnimation(
        fig, update,
        interval = UPDATE_MS,
        blit     = False,
        cache_frame_data = False,
    )

    plt.tight_layout()
    plt.show()

    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    print("[EXIT] Afsluttet")
