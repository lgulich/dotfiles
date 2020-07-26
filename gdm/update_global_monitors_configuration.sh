#!/bin/sh -e

# GDM has two monitors.xml, the one in ~gdm/.config/ is used for the login 
# screen. To configure it, first configure the monitor layout via the 
# regular Ubuntu settings GUI. Then run this script to copy the monitors.xml
# file to the correct place.

sudo cp ~/.config/monitors.xml ~gdm/.config/monitors.xml
sudo chown gdm:gdm ~gdm/.config/monitors.xml

echo "If this does not work yet try uncommenting 'WaylandEnable=false' in 
/etc/gdm3/custom.conf"
