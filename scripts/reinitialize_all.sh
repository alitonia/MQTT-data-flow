#!/bin/bash

# A master script to reset the entire environment and restart the simulation

# Determine the project root directory
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$PROJECT_DIR" || exit 1

echo "Master simulation reset triggered..."
# Run the clean script
./scripts/clean_data.sh

echo "Building and restarting the ecosystem..."
# Rebuild the core images to ensure all dashboard and data protocol changes are applied
docker-compose up -d --build

echo "Restart complete. Access Grafana at http://localhost:3000 (admin/admin)"
