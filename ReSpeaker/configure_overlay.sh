#!/bin/bash

CONFIG_FILE="/boot/firmware/config.txt"

# Lines to add
LINE1="dtoverlay=respeaker-2mic-v2_0-overlay"
LINE2="dtoverlay=i2s-mmap"

# Check and add LINE1 if missing
if ! grep -Fxq "$LINE1" "$CONFIG_FILE"; then
    echo "$LINE1" | sudo tee -a "$CONFIG_FILE" > /dev/null
    echo "Added: $LINE1"
else
    echo "Already present: $LINE1"
fi

# Check and add LINE2 if missing
if ! grep -Fxq "$LINE2" "$CONFIG_FILE"; then
    echo "$LINE2" | sudo tee -a "$CONFIG_FILE" > /dev/null
    echo "Added: $LINE2"
else
    echo "Already present: $LINE2"
fi

echo "Done updating $CONFIG_FILE."
