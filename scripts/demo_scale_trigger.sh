#!/bin/bash
echo "🚀 [Scale Trigger] Scaling up Edge Wild simulators to 5 instances each..."
docker-compose up -d --scale edge-wild-1=5 --scale edge-wild-2=5 --scale edge-wild-3=5
echo "Notice processing metrics climbing smoothly in response to heavy traffic influx."
