# Local High Availability HAProxy with Docker Compose

To successfully eliminate the HAProxy gateway as a Single Point of Failure locally using **strictly Docker Compose** (avoiding Kubernetes or Docker Swarm overhead), you replicate enterprise VIP (Virtual IP) failover using `keepalived` directly inside the containers.

## The Architecture
Instead of one isolated `mqtt-lb` container, we split it into an active-passive mirror:
1. `haproxy-master`
2. `haproxy-backup`

Both containers run a custom Docker image bundling `haproxy` and `keepalived` simultaneously. `Keepalived` actively monitors HAProxy's health. If `haproxy-master` crashes, shuts down, or locks up, `keepalived` instantly "steals" a shared **Virtual IP (VIP)** and assigns it identically to `haproxy-backup` in milliseconds.

---

## Technical Implementation Guide

### 1. Dockerfile (HAProxy + Keepalived)
You cannot use the raw default HAProxy image. You create a tiny `/haproxy-ha/Dockerfile` that installs the networking daemon:

```dockerfile
FROM haproxy:alpine
USER root
RUN apk add --no-cache keepalived
# Script to launch Keepalived in the background, and HAProxy in the foreground
COPY start.sh /start.sh
RUN chmod +x /start.sh
ENTRYPOINT ["/start.sh"]
```

### 2. Docker Compose Additions
To execute VIP failovers, Docker explicitly requires you forcibly grant `NET_ADMIN` capabilities to the containers so they have kernel-level permission to rewrite the Docker Bridge subnet live.

```yaml
version: '3.8'

services:
  haproxy-master:
    build: 
      context: ./haproxy-ha
    container_name: haproxy_master
    cap_add:
      - NET_ADMIN       # Extremely important: Allows IP stealing
      - NET_BROADCAST
    environment:
      - STATE=MASTER
      - PRIORITY=100
      - VIP=172.20.0.100  # Explicit Floating IP inside the docker network
    networks:
      iot_net:
        ipv4_address: 172.20.0.10

  haproxy-backup:
    build: 
      context: ./haproxy-ha
    container_name: haproxy_backup
    cap_add:
      - NET_ADMIN
      - NET_BROADCAST
    environment:
      - STATE=BACKUP
      - PRIORITY=50
      - VIP=172.20.0.100
    networks:
      iot_net:
        ipv4_address: 172.20.0.11
        
networks:
  iot_net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### 3. Edge Node Modification
Currently, your Python edge nodes attempt to connect via Docker's internal DNS using `MQTT_BROKER=haproxy`.
In this hardened configuration, you hardcode the Edge variables to target the floating Virtual IP directly:
`MQTT_BROKER=172.20.0.100`

---

## How It Proves Resiliency Live
1. You run `docker stop haproxy_master`.
2. The `keepalived` daemon running inside `haproxy_backup` immediately detects the heartbeat death.
3. It instantly binds `172.20.0.100` to its own operational interface.
4. Your Paho MQTT Edge clients experience the connection drop, wait their standard 5 seconds, attempt to reconnect to `172.20.0.100`... and are instantly accepted cleanly by the backup node **without you having to shift a single line of python code**.
