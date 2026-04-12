#!/bin/bash
echo "🔄 [Scale Revert] Scaling Edge Wild simulators back down to 1 instance..."
docker-compose up -d --scale edge-wild-1=1 --scale edge-wild-2=1 --scale edge-wild-3=1
