import os
import base64
import requests
import time
import cv2
import numpy as np
import xml.etree.ElementTree as ET

CAMERA_FOLDER = "cameras"
os.makedirs(CAMERA_FOLDER, exist_ok=True)

# ---------- Camera save/load ----------
def save_camera(name, ip, port, username, password):
    with open(os.path.join(CAMERA_FOLDER, f"{name}.txt"), "w") as f:
        f.write(f"{ip}\n{port}\n{username}\n{password}")
    print(f"Camera '{name}' saved!")

def load_cameras():
    files = [f for f in os.listdir(CAMERA_FOLDER) if f.endswith(".txt")]
    return {i + 1: f for i, f in enumerate(files)}

def choose_camera():
    cams = load_cameras()
    if cams:
        print("Saved cameras:")
        for i, f in cams.items():
            print(f"{i}: {f[:-4]}")
        choice = input("Select camera or press Enter for manual: ")
        if choice.isdigit() and int(choice) in cams:
            with open(os.path.join(CAMERA_FOLDER, cams[int(choice)])) as f:
                return [line.strip() for line in f.readlines()]

    ip = input("IP: ")
    port = input("HTTP Port: ")
    username = input("Username: ")
    password = input("Password: ")

    if input("Save this camera? (y/n): ").lower() == "y":
        save_camera(input("Camera name: "), ip, port, username, password)

    return ip, port, username, password

# ---------- Fetch channels ----------
def fetch_channels(ip, port, headers):
    url = f"http://{ip}:{port}/ISAPI/Streaming/channels"
    channels = []
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            for ch in root.findall("StreamingChannel"):
                cid = ch.find("id").text
                channels.append((cid, ""))
    except Exception as e:
        print("ISAPI channel fetch failed:", e)
    return channels

# ---------- Main ----------
ip, port, username, password = choose_camera()

auth = base64.b64encode(f"{username}:{password}".encode()).decode()
headers = {"Authorization": f"Basic {auth}"}

channels = fetch_channels(ip, port, headers)

# 🔥 FALLBACK FOR 32-CHANNEL NVR
if not channels:
    print("Falling back to 32-channel layout")
    channels = [(f"{i}01", f"Camera {i}") for i in range(1, 33)]

print(f"\nLoaded {len(channels)} channels")

channel_index = 0
channel = channels[channel_index][0]

window = f"HikVision {ip}"
cv2.namedWindow(window, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window, 900, 600)

refresh = 1.0
last = 0

print("\nControls:")
print(" n = next channel")
print(" p = previous channel")
print(" m = manual channel input")
print(" q = quit")

try:
    while True:
        now = time.time()
        if now - last >= refresh:
            last = now
            url = f"http://{ip}:{port}/ISAPI/Streaming/channels/{channel}/picture"
            try:
                r = requests.get(url, headers=headers, timeout=5)
                if r.status_code == 200:
                    frame = cv2.imdecode(
                        np.frombuffer(r.content, np.uint8),
                        cv2.IMREAD_COLOR
                    )
                    if frame is not None:
                        cv2.putText(
                            frame,
                            f"Channel: {channel}",
                            (15, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 255, 0),
                            2,
                            cv2.LINE_AA
                        )
                        cv2.imshow(window, frame)
            except Exception as e:
                print("Snapshot error:", e)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break

        elif key == ord('n'):
            channel_index = (channel_index + 1) % len(channels)
            channel = channels[channel_index][0]
            print(f"→ Channel {channel}")

        elif key == ord('p'):
            channel_index = (channel_index - 1) % len(channels)
            channel = channels[channel_index][0]
            print(f"← Channel {channel}")

        elif key == ord('m'):
            manual = input("Enter channel ID (e.g. 1701): ").strip()
            match = [c for c in channels if c[0] == manual]
            if match:
                channel_index = channels.index(match[0])
                channel = manual
                print(f"Switched to {channel}")
            else:
                print("Invalid channel")

finally:
    cv2.destroyAllWindows()
