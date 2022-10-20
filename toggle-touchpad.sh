#!/bin/sh
device_id='ELAN1200:00 04F3:3168 Touchpad'
device_state=$(xinput list-props "$device_id" | grep -Po "(?<=Device Enabled \\(184\\):\\t)\d+")
if [[ $device_state -eq "1" ]]; then
    xinput disable "$device_id"
else
    xinput enable "$device_id"
fi