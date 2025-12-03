# Cartographer Metrics Service

A microservice for publishing consistent network topology metrics to Redis pub/sub for consumption by other services and real-time dashboards.

## Overview

The Metrics Service aggregates data from multiple sources (health service, backend) and publishes comprehensive network topology snapshots to Redis. Other services can subscribe to these channels for real-time updates.

## Features

- **Topology Snapshots**: Complete network topology with all node metrics
- **Health Status**: Device health, uptime, and connectivity information
- **DNS Metrics**: Reverse DNS and hostname resolution data
- **ISP Metrics**: Gateway test IPs and speed test results
- **Node Connections**: Connection graph with speed and latency information
- **Real-time Updates**: WebSocket and Redis pub/sub for live data
- **User Notes**: Custom notes attached to network nodes

## Data Published

Each topology snapshot includes:

| Category | Data Points |
|----------|-------------|
| **Node Identity** | ID, name, IP, hostname, role |
| **Topology** | Parent connections, connection speeds, depth |
| **Health** | Status (healthy/degraded/unhealthy/unknown), last check time |
| **Connectivity** | Ping metrics (latency, packet loss, jitter), DNS resolution |
| **Uptime** | 24h uptime %, average latency, check pass/fail counts |
| **ISP (Gateways)** | Test IPs with metrics, last speed test results |
| **Metadata** | Notes, version, created/updated timestamps |

## Redis Channels

| Channel | Event Types | Description |
|---------|-------------|-------------|
| `metrics:topology` | `full_snapshot`, `node_update` | Topology and node updates |
| `metrics:health` | `health_update` | Health status changes |
| `metrics:speedtest` | `speed_test_result` | Speed test completions |

## API Endpoints

### Snapshots

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/metrics/snapshot` | Get latest snapshot from memory |
| POST | `/api/metrics/snapshot/generate` | Generate new snapshot |
| POST | `/api/metrics/snapshot/publish` | Generate and publish to Redis |
| GET | `/api/metrics/snapshot/cached` | Get last snapshot from Redis |

### Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/metrics/config` | Get service configuration |
| POST | `/api/metrics/config` | Update publishing config |

### Data Access

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/metrics/summary` | Lightweight summary for dashboards |
| GET | `/api/metrics/nodes/{id}` | Get specific node metrics |
| GET | `/api/metrics/connections` | Get all node connections |
| GET | `/api/metrics/gateways` | Get gateway ISP information |

### Speed Test

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/metrics/speed-test` | Trigger ISP speed test |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `/api/metrics/ws` | Real-time updates via WebSocket |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `REDIS_DB` | `0` | Redis database number |
| `HEALTH_SERVICE_URL` | `http://localhost:8001` | Health service URL |
| `BACKEND_SERVICE_URL` | `http://localhost:8000` | Backend service URL |
| `METRICS_PUBLISH_INTERVAL` | `30` | Seconds between publishes |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis (if not running)
docker run -d -p 6379:6379 redis:7-alpine

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

## Docker

```bash
# Build
docker build -t cartographer-metrics .

# Run
docker run -d \
  -p 8003:8003 \
  -e REDIS_URL=redis://redis:6379 \
  -e HEALTH_SERVICE_URL=http://health:8001 \
  -e BACKEND_SERVICE_URL=http://app:8000 \
  cartographer-metrics
```

## Event Schema

### Full Snapshot Event

```json
{
  "event_type": "full_snapshot",
  "timestamp": "2024-01-15T10:30:00Z",
  "payload": {
    "snapshot_id": "uuid",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": 1,
    "total_nodes": 15,
    "healthy_nodes": 12,
    "degraded_nodes": 2,
    "unhealthy_nodes": 1,
    "unknown_nodes": 0,
    "nodes": {
      "192.168.1.1": {
        "id": "192.168.1.1",
        "name": "Main Router",
        "ip": "192.168.1.1",
        "role": "gateway/router",
        "status": "healthy",
        "ping": {
          "success": true,
          "latency_ms": 1.5,
          "packet_loss_percent": 0
        },
        "uptime": {
          "uptime_percent_24h": 99.8,
          "avg_latency_24h_ms": 1.6
        },
        "isp_info": {
          "gateway_ip": "192.168.1.1",
          "test_ips": [...],
          "last_speed_test": {
            "download_mbps": 450.5,
            "upload_mbps": 42.3
          }
        }
      }
    },
    "connections": [
      {
        "source_id": "192.168.1.1",
        "target_id": "192.168.1.100",
        "connection_speed": "1GbE",
        "latency_ms": 0.5
      }
    ],
    "gateways": [...]
  }
}
```

## Subscribing to Events (Python Example)

```python
import redis
import json

r = redis.Redis(host='localhost', port=6379, decode_responses=True)
pubsub = r.pubsub()
pubsub.subscribe('metrics:topology', 'metrics:health')

for message in pubsub.listen():
    if message['type'] == 'message':
        event = json.loads(message['data'])
        print(f"Received {event['event_type']} at {event['timestamp']}")
        # Process event...
```

## WebSocket Client (JavaScript Example)

```javascript
const ws = new WebSocket('ws://localhost:8003/api/metrics/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'initial_snapshot') {
    // Initialize state with full topology
    initializeTopology(data.payload);
  } else if (data.type === 'full_snapshot') {
    // Update topology
    updateTopology(data.payload);
  } else if (data.type === 'health_update') {
    // Update node health
    updateNodeHealth(data.payload.node_id, data.payload.status);
  }
};

// Request fresh snapshot
ws.send(JSON.stringify({ action: 'request_snapshot' }));
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│  Health Service │     │     Backend     │
│   (Port 8001)   │     │   (Port 8000)   │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │   HTTP/JSON           │   HTTP/JSON
         │                       │
         └───────────┬───────────┘
                     │
              ┌──────▼──────┐
              │   Metrics   │
              │   Service   │
              │ (Port 8003) │
              └──────┬──────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
    ┌────▼────┐ ┌────▼────┐ ┌────▼────┐
    │  Redis  │ │WebSocket│ │ REST API│
    │ Pub/Sub │ │ Clients │ │ Clients │
    └─────────┘ └─────────┘ └─────────┘
```

## Integration with Other Services

Any service can subscribe to metrics events from Redis:

1. **Alerting Service**: Subscribe to `metrics:health` for status changes
2. **Dashboard Service**: Subscribe to `metrics:topology` for live updates
3. **Analytics Service**: Subscribe to `metrics:speedtest` for ISP tracking
4. **Logging Service**: Subscribe to all channels for audit trail
