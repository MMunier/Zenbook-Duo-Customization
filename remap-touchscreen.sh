#!/bin/sh
echo "hi" >> /tmp/debug
remap() {
    
    export XAUTHORITY="/home/pleb/.Xauthority"
    # active_display_count=$(xrandr -q | grep -v disconnected | grep connected | wc -l );
    # old_count=$active_display_count;
    # echo "$active_display_count" >> "/tmp/debug"
    # while [[ $active_display_count -eq $old_count ]]; do
    #     sleep "$1"
    #     active_display_count=$(xrandr -q | grep -v disconnected | grep connected | wc -l );  
    #    echo "$active_display_count" >> "/tmp/debug"
    # done	    
    sleep "$1"
    # echo "$active_display_count" >> "/tmp/debug"
    echo "Remapping" >> "/tmp/debug"
    xinput map-to-output "ELAN9008:00 04F3:2D55" "eDP1" >> /tmp/debug
    xinput map-to-output "ELAN9009:00 04F3:2C1B" "DP3" >> /tmp/debug
}

remap 0 &
remap 1 &
remap 2 &
remap 3 &
