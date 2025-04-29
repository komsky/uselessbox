#!/bin/bash
# install.sh - Complete installation of the useless service

SERVICE_FILE="/home/komsky/useless/useless.service"
TARGET_DIR="/etc/systemd/system"

# Check if the service file exists
if [ ! -f "$SERVICE_FILE" ]; then
  echo "Error: Service file not found at $SERVICE_FILE"
  exit 1
fi

echo "Copying service file to $TARGET_DIR..."
sudo cp "$SERVICE_FILE" "$TARGET_DIR/"

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Enabling the useless service to start at boot..."
sudo systemctl enable useless.service

echo "Starting the useless service..."
sudo systemctl start useless.service

echo "Installation complete."
