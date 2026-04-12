#!/bin/bash
echo "🔄 [Network Revert] Starting HAProxy to restore network..."
docker start mqtt-lb
echo "Watch Edge logs flush buffer and Grafana virtually spike ingestion to backfill data."
