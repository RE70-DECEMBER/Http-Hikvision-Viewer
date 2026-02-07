import os

# Install GTK libraries and pkg-config
os.system("sudo apt update -y")
os.system("sudo apt install -y libgtk2.0-dev pkg-config")

# Install OpenCV for Python
os.system("sudo apt install -y python3-opencv")
os.system("pip install opencv-python --break-system-packages")
