import os
import base64
import requests
import time
import cv2
import numpy as np

CAMERA_FOLDER = "cameras"
os.makedirs(CAMERA_FOLDER, exist_ok=True)

# --- Camera save/load functions ---
def save_camera(name, ip, port, username, password):
    filename = os.path.join(CAMERA_FOLDER, f"{name}.txt")
    with open(filename, "w") as f:
        f.write(f"{ip}\n{port}\n{username}\n{password}")
    print(f"Camera '{name}' saved successfully!")

def load_cameras():
    files = [f for f in os.listdir(CAMERA_FOLDER) if f.endswith(".txt")]
    return {i+1: file for i, file in enumerate(files)}

def choose_camera():
    cameras = load_cameras()
    if cameras:
        print("Saved cameras:")
        for i, file in cameras.items():
            print(f"{i}: {file[:-4]}")
        choice = input("Select a camera by number or press Enter to input manually: ")
        if choice.isdigit() and int(choice) in cameras:
            with open(os.path.join(CAMERA_FOLDER, cameras[int(choice)])) as f:
                ip, port, username, password = [line.strip() for line in f.readlines()]
            return ip, port, username, password
    # Manual input fallback
    ip = input("IP: ")
    port = input("HTTP Port: ")
    username = input("Username: ")
    password = input("Password: ")
    save = input("Save this camera? (y/n): ").lower()
    if save == "y":
        name = input("Enter a name for this camera: ")
        save_camera(name, ip, port, username, password)
    return ip, port, username, password

# --- Main Program ---
ip, port, username, password = choose_camera()

# Encode credentials for Basic Auth
key = base64.b64encode(f"{username}:{password}".encode()).decode()
headers = {"Authorization": f"Basic {key}"}
snapshot_url = f"http://{ip}:{port}/ISAPI/Streaming/channels/101/picture"

# OpenCV window
window_name = f"HikVision Camera {ip}"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window_name, 800, 600)  # optional resize

refresh_interval = 1.0  # seconds
last_time = 0

try:
    while True:
        now = time.time()
        if now - last_time >= refresh_interval:
            last_time = now
            try:
                # Grab snapshot
                r = requests.get(snapshot_url, headers=headers, timeout=5)
                if r.status_code == 200:
                    np_arr = np.frombuffer(r.content, dtype=np.uint8)
                    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    if frame is not None:
                        cv2.imshow(window_name, frame)
                else:
                    print(f"Failed to get snapshot: {r.status_code}")
            except Exception as e:
                print(f"Error fetching snapshot: {e}")

        # Exit on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cv2.destroyAllWindows()
