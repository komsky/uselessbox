#!/bin/bash

SERVICE_FILE="toggle_switch.service"
TARGET_DIR="/etc/systemd/system"
TARGET_FILE="$TARGET_DIR/$SERVICE_FILE"

# Check if the service file exists in the current directory
if [ ! -f "$SERVICE_FILE" ]; then
    echo "Error: $SERVICE_FILE not found in the current directory."
    exit 1
fi

echo "Copying $SERVICE_FILE to $TARGET_DIR..."
sudo cp "$SERVICE_FILE" "$TARGET_DIR" || { echo "Failed to copy the service file."; exit 1; }

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Enabling $SERVICE_FILE..."
sudo systemctl enable "$SERVICE_FILE"

echo "Starting $SERVICE_FILE..."
sudo systemctl start "$SERVICE_FILE"

echo "Service installation complete. Here is the service status:"
sudo systemctl status "$SERVICE_FILE" --no-pager
