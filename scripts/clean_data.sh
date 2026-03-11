#!/bin/bash

# Clean script to purge all environmental data, volumes, and persistent buffers

# Determine the project root directory (one level up from this script's directory)
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$PROJECT_DIR" || exit 1

echo "Stopping and removing all Docker containers, networks, and volumes..."
docker-compose down -v --remove-orphans

echo "Removing any local SQLite buffer files (buffer_*.db, buffer.db)..."
# Find and remove any leftover buffer databases in the root or edge folders
find . -name "buffer*.db" -type f -delete
find . -name "buffer*.db-journal" -type f -delete

echo "Purging any local application logs or temp files..."
# Clear standard temp directories if they exist
[ -d "edge/logs" ] && rm -rf edge/logs/*
[ -d "cloud/logs" ] && rm -rf cloud/logs/*

# Mosquitto data (if any was created on the host accidentally)
[ -f "mosquitto/mosquitto.db" ] && rm "mosquitto/mosquitto.db"

echo "Data purge complete."
echo "You can now run 'docker-compose up --build' to start with a fresh state."
