#!/bin/bash

# Link in services
SOURCE_HOME=/home/neil/projects/dangle/DangleTeam
ln -s $SOURCE_HOME/services/mpu.service /etc/systemd/system
ln -s $SOURCE_HOME/services/dangleredboard.service /etc/systemd/system
ln -s $SOURCE_HOME/services/approxeng.service /etc/systemd/system
ln -s $SOURCE_HOME/services/eyes.service /etc/systemd/system
ln -s $SOURCE_HOME/services/menu.service /etc/systemd/system

# enable & start services
systemctl daemon-reload
systemctl enable mpu.service
systemctl start mpu.service
systemctl enable dangleredboard.service
systemctl start dangleredboard.service
systemctl enable approxeng.service
systemctl start approxeng.service
systemctl enable eyes.service
systemctl start eyes.service
systemctl enable menu.service
systemctl start menu.service

# View logs
journalctl -b0 --unit=mpu.service --unit=dangleredboard.service --unit=approxeng.service --unit=eyes.service --unit=menu.service
