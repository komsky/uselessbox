#!/usr/bin/env bash
set -euo pipefail

# Resolve the directory this script lives in (your repo root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
SERVICE_SRC="$SCRIPT_DIR/uselessbox.service"
SERVICE_DEST="/etc/systemd/system/uselessbox.service"

# Check for the service file
if [[ ! -f "$SERVICE_SRC" ]]; then
  echo "ERROR: could not find $SERVICE_SRC"
  exit 1
fi

echo "Copying service file to $SERVICE_DEST..."
sudo cp "$SERVICE_SRC" "$SERVICE_DEST"

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Enabling uselessbox.service to start on boot..."
sudo systemctl enable uselessbox.service

echo "Starting uselessbox.service now..."
sudo systemctl start uselessbox.service

echo "Done. Check status with: sudo systemctl status uselessbox.service"
