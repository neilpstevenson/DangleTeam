#!/bin/sh
FIND_FILE="/boot/firmware/config.txt"

if [ `grep -c "camera_auto_detect=1" $FIND_FILE` -ne '0' ];then
    sudo sed -i "s/\(^camera_auto_detect=1\)/camera_auto_detect=0/" /boot/config.txt
fi
if [ `grep -c "camera_auto_detect=0" $FIND_FILE` -lt '1' ];then
    sudo bash -c 'echo camera_auto_detect=0 >> /boot/config.txt'
fi
if [ `grep -c "dtoverlay=arducam-pivariety,media-controller=0" $FIND_FILE` -lt '1' ];then
    sudo bash -c 'echo dtoverlay=arducam-pivariety,media-controller=0 >> /boot/config.txt'
fi

if [ $(dpkg -l | grep -c arducam-tof-sdk-dev) -lt 1 ]; then
    echo "Add Arducam_ppa repositories."
    curl -s --compressed "https://arducam.github.io/arducam_ppa/KEY.gpg" | sudo apt-key add -
    sudo curl -s --compressed -o /etc/apt/sources.list.d/arducam_list_files.list "https://arducam.github.io/arducam_ppa/arducam_list_files.list"
fi
