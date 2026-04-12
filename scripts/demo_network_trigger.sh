#!/bin/bash
echo "🚀 [Network Trigger] Stopping HAProxy Load Balancer to simulate total network loss..."
docker stop mqtt-lb
echo "Watch edge node logs for 'Disconnected' & 'Buffered compressed batch' indicating offline caching."
