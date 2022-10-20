#!/bin/sh
active_users=$(users)
echo "hi" >> /tmp/debug
remap() {
    sleep "$1"
    for user in $active_users
    do
        export XAUTHORITY="/home/$user/.Xauthority"
        xinput map-to-output "ELAN9008:00 04F3:2D55" "eDP1" >> /tmp/debug
        xinput map-to-output "ELAN9009:00 04F3:2C1B" "DP3" >> /tmp/debug
    done
}

remap 1 &
