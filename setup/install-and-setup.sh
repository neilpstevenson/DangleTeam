#!/bin/bash
# This script installs all the necessary packages
# and gets the necessary github repositories
# for Dangly Too PiWars 2024
#

# Create our base directory structure
cd
mkdir projects projects/dangle

# Set up git
git config --global user.email "neil.github@secureness.co.uk"
git config --global user.name "Neil Stevenson"
git config credential.helper store

# Get the Dangle code
cd projects/dangle
GITUSER="neilpstevenson"
git clone "https://$GITUSER@github.com/neilpstevenson/DangleTeam.git"
git checkout DanglyToo
# Note: password can be changed using 
# git remote set-url origin "https://user:pass@github.com/..."
# or by using 
# git config credential.helper store
# Then on next pull/push it will save the username and PAT/password

# Build the MPU code exe
cd ~/projects/dangle/DangleTeam/common/mpu
make -f Makefile9250

# Get the ArcuCam repository and install. This also installs OpenCV and related packages
cd
git clone https://github.com/ArduCAM/Arducam_tof_camera.git
cd Arducam_tof_camera
./Install_dependencies.sh
# This also installs:
#  sudo apt install -y arducam-config-parser-dev arducam-usb-sdk-dev arducam-tof-sdk-dev
#  sudo apt-get install cmake -y
#  sudo apt install libopencv-dev -y

# For Bullseye, we need a slightly different installation to config.txt
cd ~/projects/dangle/DangleTeam/setup
./Arducam_tof_camera_config.sh

# If example CPP code required, compile here
# ./compile.sh

# Install any further packages needed
sudo apt install -y libopenjp2-7-dev fonts-dejavu libpython3-dev libjpeg-dev 
sudo apt install -y pigpiod
# OpenCV python libraries
sudo apt install -y liblapack-dev libatlas-base-dev
sudo apt install -y python3-opencv libopenblas-dev 
#sudo apt install -y libcblas-dev libhdf5-dev libhdf5-serial-dev libjasper-dev 
#sudo apt install -y libqtgui4 libqt4-test
sudo apt install -y python3-picamera2

# Required for neopixel????
sudo apt install -y python3-pyaudio

# Start the pigpiod deamon
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

# Create the vitual Python environment
python3 -m venv ~/redboard

# Activate the environment
source ~/redboard/bin/activate

# ApproxEng library (for bluetooth controllers etc)
#approxeng.input

# Install the remaining Pyhon libraries into the environment
cd ~/projects/dangle/DangleTeam/setup
pip install -r py-requirements.txt

# Need to manually link opencv into env
ln -s /usr/lib/python3/dist-packages/cv2.* ~/redboard/lib/python3.11/site-packages/
ln -s /usr/lib/python3/dist-packages/picamera2 ~/redboard/lib/python3.11/site-packages/
ln -s /usr/lib/python3/dist-packages/libcamera ~/redboard/lib/python3.11/site-packages/
ln -s /usr/lib/python3/dist-packages/v4l2* ~/redboard/lib/python3.11/site-packages/
ln -s /usr/lib/python3/dist-packages/prctl.py ~/redboard/lib/python3.11/site-packages/
ln -s /usr/lib/python3/dist-packages/_prctl.* ~/redboard/lib/python3.11/site-packages/
ln -s /usr/lib/python3/dist-packages/piexif* ~/redboard/lib/python3.11/site-packages/
ln -s /usr/lib/python3/dist-packages/pidng* ~/redboard/lib/python3.11/site-packages/
ln -s /usr/lib/python3/dist-packages/simplejpeg* ~/redboard/lib/python3.11/site-packages/
ln -s /usr/lib/python3/dist-packages/av* ~/redboard/lib/python3.11/site-packages/
ln -s /usr/lib/python3/dist-packages/pykms ~/redboard/lib/python3.11/site-packages/


# Start the Dangle services
cd ~/projects/dangle/DangleTeam/services
sudo ./install.sh

