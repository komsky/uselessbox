#!/usr/bin/env bash
set -euo pipefail

echo "Stopping uselessbox.service..."
sudo systemctl stop uselessbox.service

# If you also want to prevent it from starting on boot, uncomment:
# echo "Disabling uselessbox.service..."
# sudo systemctl disable uselessbox.service

echo "Done. You can verify with: sudo systemctl status uselessbox.service"
sudo systemctl status uselessbox.service
