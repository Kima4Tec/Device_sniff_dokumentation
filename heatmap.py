"""
Heatmap over UDP-positioner fra master ESP32
Kræver: pip install matplotlib numpy

Kør: python heatmap.py
"""

import json
import socket
import threading
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime

# ===================== KONFIGURATION =====================
UDP_HOST  = "0.0.0.0"   # Lyt på alle interfaces
UDP_PORT  = 5005         # Skal matche UDP_PORT i master.cpp

# Rum-dimensioner i meter
ROOM_W = 5.0
ROOM_H = 4.0

# Sensor-positioner (skal matche ESP32-koden)
SENSORS = [
    {"id": "ESP32_A", "x": 0.0, "y": 0.0, "color": "orange"},
    {"id": "ESP32_B", "x": 5.0, "y": 0.0, "color": "orange"},
    {"id": "Master",  "x": 0.0, "y": 4.0, "color": "mediumpurple"},
]

GRID_RES    = 100    # Heatmap opløsning
HEAT_RADIUS = 0.8    # Meters radius per enhed
HEAT_DECAY  = 0.92   # Heatmap falmer pr. frame
UPDATE_MS   = 500    # Opdateringsinterval

# ===================== DELT STATE =====================
lock         = threading.Lock()
positions    = {}
heatmap_grid = np.zeros((GRID_RES, GRID_RES))
msg_count    = 0

# ===================== UDP LISTENER =====================
def udp_listener():
    global msg_count
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((UDP_HOST, UDP_PORT))
    print(f"[UDP] Lytter på port {UDP_PORT}")

    while True:
        try:
            data, addr = sock.recvfrom(512)
            msg = json.loads(data.decode("utf-8"))
            dev_id = msg.get("devId")
            x      = float(msg.get("x", 0))
            y      = float(msg.get("y", 0))
            ts     = msg.get("ts", "unknown")

            if not dev_id:
                continue

            x = max(0.0, min(ROOM_W, x))
            y = max(0.0, min(ROOM_H, y))

            with lock:
                positions[dev_id] = {"x": x, "y": y, "ts": ts}
                msg_count += 1

                # Tilføj Gaussian blob til heatmap
                gx = int((x / ROOM_W) * (GRID_RES - 1))
                gy = int((y / ROOM_H) * (GRID_RES - 1))
                radius_cells = int((HEAT_RADIUS / ROOM_W) * GRID_RES)
                for dx in range(-radius_cells, radius_cells + 1):
                    for dy in range(-radius_cells, radius_cells + 1):
                        nx, ny = gx + dx, gy + dy
                        if 0 <= nx < GRID_RES and 0 <= ny < GRID_RES:
                            dist = np.sqrt(dx**2 + dy**2)
                            val  = np.exp(-0.5 * (dist / max(radius_cells * 0.4, 1))**2)
                            heatmap_grid[ny, nx] += val

            print(f"[#{msg_count}] {dev_id} @ ({x:.2f}, {y:.2f})  fra {addr[0]}")

        except json.JSONDecodeError as e:
            print(f"[UDP] Ugyldig JSON: {e}")
        except Exception as e:
            print(f"[UDP] Fejl: {e}")

# ===================== PLOT SETUP =====================
fig, ax = plt.subplots(figsize=(9, 7))
fig.patch.set_facecolor("#0e1117")
ax.set_facecolor("#161b24")

plt.title("Positionsoverblik — live", color="white", fontsize=13, pad=12)
ax.set_xlim(0, ROOM_W)
ax.set_ylim(0, ROOM_H)
ax.set_xlabel("Meter (x)", color="#6b7a99")
ax.set_ylabel("Meter (y)", color="#6b7a99")
ax.tick_params(colors="#6b7a99")
for spine in ax.spines.values():
    spine.set_edgecolor("#242b38")

ax.set_xticks(np.arange(0, ROOM_W + 1, 1))
ax.set_yticks(np.arange(0, ROOM_H + 1, 1))
ax.grid(color="#1e2530", linewidth=0.5)

heat_img = ax.imshow(
    heatmap_grid,
    origin="lower",
    extent=[0, ROOM_W, 0, ROOM_H],
    cmap="inferno",
    alpha=0.75,
    vmin=0, vmax=5,
    aspect="auto",
    interpolation="gaussian",
)

# Sensor-markører
for s in SENSORS:
    ax.plot(s["x"], s["y"], "s", color=s["color"], markersize=10, zorder=5)
    ax.annotate(s["id"], (s["x"], s["y"]),
        textcoords="offset points", xytext=(6, 6),
        color=s["color"], fontsize=8)

device_scatter = ax.scatter([], [], c="cyan", s=60, zorder=6,
    edgecolors="white", linewidths=0.5)
device_labels  = []

status_text = ax.text(
    0.01, 0.98, "", transform=ax.transAxes,
    color="#6b7a99", fontsize=8, va="top", fontfamily="monospace"
)

# ===================== ANIMATION =====================
def update(frame):
    global heatmap_grid

    with lock:
        heatmap_grid   *= HEAT_DECAY
        heat_img.set_data(heatmap_grid.copy())
        heat_img.set_clim(vmin=0, vmax=max(1.0, heatmap_grid.max()))
        pos_snapshot    = dict(positions)
        count           = msg_count

    for lbl in device_labels:
        lbl.remove()
    device_labels.clear()

    if pos_snapshot:
        xs = [p["x"] for p in pos_snapshot.values()]
        ys = [p["y"] for p in pos_snapshot.values()]
        device_scatter.set_offsets(np.c_[xs, ys])
        for dev_id, p in pos_snapshot.items():
            lbl = ax.annotate(dev_id, (p["x"], p["y"]),
                textcoords="offset points", xytext=(5, 5),
                color="cyan", fontsize=7, fontfamily="monospace")
            device_labels.append(lbl)
    else:
        device_scatter.set_offsets(np.empty((0, 2)))

    status_text.set_text(
        f"Enheder: {len(pos_snapshot)}  |  Pakker: {count}  |  {datetime.now().strftime('%H:%M:%S')}"
    )
    return heat_img, device_scatter, status_text

# ===================== MAIN =====================
if __name__ == "__main__":
    print("=" * 48)
    print("  Heatmap starter")
    print(f"  Lytter på UDP port : {UDP_PORT}")
    print(f"  Rum                : {ROOM_W} x {ROOM_H} m")
    print("=" * 48)

    t = threading.Thread(target=udp_listener, daemon=True)
    t.start()

    ani = FuncAnimation(fig, update,
        interval=UPDATE_MS, blit=False, cache_frame_data=False)

    plt.tight_layout()
    plt.show()
    print("[EXIT] Afsluttet")
