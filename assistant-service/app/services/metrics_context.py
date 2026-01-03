"""
Service for fetching and formatting network context from the metrics service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


class MetricsContextService:
    """Service to fetch network context from metrics service"""

    def __init__(self):
        self.timeout = 10.0
        # Multi-tenant cache: network_id -> (context, summary, timestamp)
        self._context_cache: dict[str | None, tuple[str, dict[str, Any], datetime]] = {}
        self._cache_ttl_seconds = 30  # Cache for 30 seconds

        # Loading state tracking (per network_id)
        self._snapshot_available: dict[str | None, bool] = {}
        self._last_check_time: datetime | None = None
        self._check_interval_seconds = 5  # Recheck every 5 seconds when no snapshot
        self._max_wait_attempts = 6  # Max attempts when waiting for snapshot (30 seconds total)

    # Backwards compatibility properties
    @property
    def _cached_context(self) -> str | None:
        """Backwards compatibility: get legacy cached context."""
        if None in self._context_cache:
            return self._context_cache[None][0]
        return None

    @property
    def _cached_summary(self) -> dict[str, Any] | None:
        """Backwards compatibility: get legacy cached summary."""
        if None in self._context_cache:
            return self._context_cache[None][1]
        return None

    @property
    def _cache_timestamp(self) -> datetime | None:
        """Backwards compatibility: get legacy cache timestamp."""
        if None in self._context_cache:
            return self._context_cache[None][2]
        return None

    async def fetch_network_snapshot(
        self, force_refresh: bool = False, network_id: str | None = None
    ) -> dict[str, Any] | None:
        """Fetch the current network topology snapshot

        Args:
            force_refresh: If True, ask the metrics service to generate a fresh snapshot
                          instead of returning the cached one. Use this after data changes
                          (like a speed test) to get the latest data.
            network_id: The network ID to fetch snapshot for (multi-tenant support).
                       If None, uses legacy single-network mode for backwards compatibility.
        """
        self._last_check_time = datetime.utcnow()

        # Build query params for network_id
        params = {}
        if network_id is not None:
            params["network_id"] = network_id

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if force_refresh:
                    # Ask metrics service to generate a fresh snapshot with latest data
                    response = await client.post(
                        f"{settings.metrics_service_url}/api/metrics/snapshot/generate",
                        params=params,
                    )
                else:
                    response = await client.get(
                        f"{settings.metrics_service_url}/api/metrics/snapshot", params=params
                    )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("snapshot"):
                        self._snapshot_available[network_id] = True
                        logger.debug(f"Successfully fetched snapshot for network_id={network_id}")
                        return data["snapshot"]
                    else:
                        # Log why we didn't get a snapshot
                        logger.warning(
                            f"Metrics service returned 200 but no valid snapshot for network_id={network_id}: "
                            f"success={data.get('success')}, has_snapshot={data.get('snapshot') is not None}, "
                            f"message={data.get('message', 'no message')}"
                        )

                # Snapshot not yet available (service may be starting up)
                self._snapshot_available[network_id] = False
                logger.info(
                    f"Snapshot not yet available for network_id={network_id}: status={response.status_code}"
                )
                return None

        except httpx.ConnectError:
            self._snapshot_available[network_id] = False
            logger.warning(f"Cannot connect to metrics service at {settings.metrics_service_url}")
            return None
        except Exception as e:
            self._snapshot_available[network_id] = False
            logger.error(f"Error fetching network snapshot: {e}")
            return None

    async def wait_for_snapshot(
        self, max_attempts: int | None = None, network_id: str | None = None
    ) -> dict[str, Any] | None:
        """
        Wait for a snapshot to become available, retrying periodically.

        Args:
            max_attempts: Maximum number of attempts (defaults to self._max_wait_attempts)
            network_id: The network ID to wait for snapshot (multi-tenant support).

        Returns:
            The snapshot if available, None if max attempts exceeded
        """
        attempts = max_attempts or self._max_wait_attempts

        for attempt in range(attempts):
            snapshot = await self.fetch_network_snapshot(network_id=network_id)
            if snapshot:
                logger.info(
                    f"Snapshot for network_id={network_id} available after {attempt + 1} attempt(s)"
                )
                return snapshot

            if attempt < attempts - 1:
                logger.debug(
                    f"Waiting for snapshot network_id={network_id} (attempt {attempt + 1}/{attempts})..."
                )
                await asyncio.sleep(self._check_interval_seconds)

        logger.warning(
            f"Snapshot for network_id={network_id} not available after {attempts} attempts"
        )
        return None

    def is_snapshot_available(self, network_id: str | None = None) -> bool:
        """Check if a snapshot has ever been successfully fetched for a network"""
        return self._snapshot_available.get(network_id, False)

    def should_recheck(self) -> bool:
        """Check if we should try fetching the snapshot again"""
        if self._snapshot_available:
            return False

        if not self._last_check_time:
            return True

        elapsed = (datetime.utcnow() - self._last_check_time).total_seconds()
        return elapsed >= self._check_interval_seconds

    async def fetch_network_summary(self, network_id: str | None = None) -> dict[str, Any] | None:
        """Fetch network summary (lighter weight than full snapshot)

        Args:
            network_id: The network ID to fetch summary for (multi-tenant support).
        """
        try:
            params = {}
            if network_id is not None:
                params["network_id"] = network_id

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{settings.metrics_service_url}/api/metrics/summary", params=params
                )

                if response.status_code == 200:
                    return response.json()

                return None

        except Exception as e:
            logger.error(f"Error fetching network summary: {e}")
            return None

    def _format_node_info(self, node: dict[str, Any]) -> str:
        """Format a single node's information"""
        lines = []

        name = node.get("name", "Unknown")
        ip = node.get("ip", "N/A")
        role = node.get("role", "unknown")
        status = node.get("status", "unknown")
        hostname = node.get("hostname", "")

        lines.append(f"  - {name}")
        lines.append(f"    IP: {ip}")
        lines.append(f"    Role: {role}")
        lines.append(f"    Status: {status}")

        if hostname and hostname != name:
            lines.append(f"    Hostname: {hostname}")

        # Connection info
        if node.get("connection_speed"):
            lines.append(f"    Connection: {node['connection_speed']}")

        # Ping metrics
        ping = node.get("ping")
        if ping and ping.get("success"):
            latency = ping.get("avg_latency_ms") or ping.get("latency_ms")
            if latency:
                lines.append(f"    Latency: {latency:.1f}ms")

        # Uptime info
        uptime = node.get("uptime")
        if uptime and uptime.get("uptime_percent_24h") is not None:
            lines.append(f"    Uptime (24h): {uptime['uptime_percent_24h']:.1f}%")

        # Open ports
        open_ports = node.get("open_ports", [])
        if open_ports:
            ports_str = ", ".join(
                f"{p['port']}" + (f" ({p['service']})" if p.get("service") else "")
                for p in open_ports[:5]  # Limit to first 5
            )
            lines.append(f"    Open Ports: {ports_str}")

        # LAN Ports configuration
        lan_ports = node.get("lan_ports")
        if lan_ports:
            lines.append(self._format_lan_ports(lan_ports))

        # Notes
        if node.get("notes"):
            lines.append(f"    Notes: {node['notes']}")

        return "\n".join(lines)

    def _format_lan_ports(self, lan_ports: dict[str, Any]) -> str:
        """Format LAN ports configuration for a device"""
        lines = []

        rows = lan_ports.get("rows", 0)
        cols = lan_ports.get("cols", 0)
        ports = lan_ports.get("ports", [])

        if not ports:
            return ""

        total_ports = len(ports)
        active_ports = [p for p in ports if p.get("status") == "active"]
        unused_ports = [p for p in ports if p.get("status") == "unused"]
        blocked_ports = [p for p in ports if p.get("status") == "blocked"]

        # Count port types
        rj45_count = len(
            [p for p in ports if p.get("type") == "rj45" and p.get("status") != "blocked"]
        )
        sfp_count = len(
            [p for p in ports if p.get("type") in ["sfp", "sfp+"] and p.get("status") != "blocked"]
        )
        poe_count = len([p for p in ports if p.get("poe") and p.get("poe") != "off"])

        lines.append(f"    LAN Ports: {total_ports} total ({rows}x{cols} grid)")
        lines.append(f"      Port Types: {rj45_count} RJ45, {sfp_count} SFP/SFP+")
        lines.append(
            f"      Status: {len(active_ports)} active, {len(unused_ports)} unused, {len(blocked_ports)} blocked"
        )

        if poe_count > 0:
            lines.append(f"      PoE Enabled: {poe_count} ports")

        # List active connections
        connected_ports = [
            p
            for p in active_ports
            if p.get("connected_device_id") or p.get("connected_device_name")
        ]
        if connected_ports:
            lines.append(f"      Active Connections ({len(connected_ports)}):")
            for port in connected_ports[:10]:  # Limit to first 10 connections
                port_num = self._get_port_label(port, lan_ports)
                port_type = port.get("type", "rj45").upper()
                speed = port.get("negotiated_speed") or port.get("speed") or "auto"
                connected_to = (
                    port.get("connected_device_name")
                    or port.get("connection_label")
                    or "Unknown device"
                )
                poe_info = ""
                if port.get("poe") and port.get("poe") != "off":
                    poe_info = f" [PoE: {port.get('poe').upper()}]"

                lines.append(
                    f"        Port {port_num} ({port_type}, {speed}) → {connected_to}{poe_info}"
                )

        return "\n".join(lines)

    def _get_port_label(self, port: dict[str, Any], lan_ports: dict[str, Any]) -> str:
        """Get the display label for a port"""
        if port.get("port_number"):
            return str(port.get("port_number"))

        # Calculate port number from position
        row = port.get("row", 1)
        col = port.get("col", 1)
        cols = lan_ports.get("cols", 1)
        start_num = lan_ports.get("start_number", 1)

        return str((row - 1) * cols + col + start_num - 1)

    def _find_gateway_node(self, gw_ip: str, nodes: dict[str, Any]) -> dict[str, Any] | None:
        """Find the gateway node by IP address."""
        for node_id, node in nodes.items():
            if node.get("ip") == gw_ip:
                logger.debug(f"Found gateway node for {gw_ip}: {node.get('name')}")
                return node
        logger.warning(f"Could not find gateway node for IP {gw_ip}")
        return None

    def _normalize_status(self, status: Any) -> str:
        """Normalize status to lowercase string."""
        if isinstance(status, str):
            return status.lower()
        if isinstance(status, dict):
            return status.get("value", "unknown").lower()
        return "unknown"

    def _format_test_ips(self, test_ips: list[dict[str, Any]]) -> list[str]:
        """Format test IP connectivity information."""
        lines = []
        healthy = sum(1 for t in test_ips if self._normalize_status(t.get("status")) == "healthy")
        lines.append(f"    External Connectivity: {healthy}/{len(test_ips)} test IPs healthy")

        for t in test_ips:
            tip_display = t.get("ip", "Unknown")
            if t.get("label"):
                tip_display += f" ({t['label']})"
            lines.append(f"      - {tip_display}: {self._normalize_status(t.get('status'))}")

        return lines

    def _format_speed_test(self, speed_test: dict[str, Any]) -> list[str]:
        """Format speed test results."""
        lines = []
        if not speed_test.get("success"):
            lines.append(
                f"    Speed Test: Failed - {speed_test.get('error_message', 'Unknown error')}"
            )
            return lines

        download = speed_test.get("download_mbps")
        upload = speed_test.get("upload_mbps")
        if download is not None or upload is not None:
            download_str = f"{download:.1f}" if download is not None else "N/A"
            upload_str = f"{upload:.1f}" if upload is not None else "N/A"
            lines.append(f"    Speed Test: ↓{download_str} Mbps / ↑{upload_str} Mbps")

        if speed_test.get("ping_ms") is not None:
            lines.append(f"    ISP Latency: {speed_test['ping_ms']:.1f}ms")

        if speed_test.get("client_isp"):
            lines.append(f"    ISP: {speed_test['client_isp']}")

        server_sponsor = speed_test.get("server_sponsor")
        server_location = speed_test.get("server_location")
        if server_sponsor or server_location:
            server_info = server_sponsor or ""
            if server_location:
                server_info += f" ({server_location})" if server_info else server_location
            lines.append(f"    Test Server: {server_info}")

        timestamp = speed_test.get("timestamp")
        if timestamp:
            ts_str = (
                timestamp
                if isinstance(timestamp, str)
                else (timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp))
            )
            lines.append(f"    Tested: {ts_str}")

        return lines

    def _format_gateway_info(self, gateway: dict[str, Any], nodes: dict[str, Any]) -> str:
        """Format gateway/ISP information, including notes from the gateway node"""
        lines = []
        gw_ip = gateway.get("gateway_ip", "Unknown")
        lines.append(f"\n  Gateway: {gw_ip}")

        gateway_node = self._find_gateway_node(gw_ip, nodes)
        if gateway_node:
            gw_name = gateway_node.get("name")
            if gw_name and gw_name != gw_ip:
                lines.append(f"    Name: {gw_name}")

        test_ips = gateway.get("test_ips", [])
        if test_ips:
            lines.extend(self._format_test_ips(test_ips))

        speed_test = gateway.get("last_speed_test")
        if speed_test:
            lines.extend(self._format_speed_test(speed_test))

        if gateway_node and gateway_node.get("notes"):
            lines.append(f"    Notes: {gateway_node['notes']}")

        return "\n".join(lines)

    def _normalize_node_role(self, role: Any) -> str:
        """Normalize a node role to a standard string."""
        if not isinstance(role, str):
            return "unknown"
        role = role.lower()
        if "gateway" in role or "router" in role:
            return "gateway/router"
        if "switch" in role or "ap" in role or "access" in role:
            return "switch/ap"
        return role

    def _group_nodes_by_role(self, nodes: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        """Group nodes by their role, excluding group nodes."""
        nodes_by_role: dict[str, list[dict[str, Any]]] = {}
        for node_id, node in nodes.items():
            role = self._normalize_node_role(node.get("role", "unknown"))
            if role == "group":
                continue
            if role not in nodes_by_role:
                nodes_by_role[role] = []
            nodes_by_role[role].append(node)
        return nodes_by_role

    def _format_health_summary(self, snapshot: dict[str, Any]) -> list[str]:
        """Format the network health summary section."""
        lines = ["\n📊 NETWORK SUMMARY"]
        lines.append(f"Total Devices: {snapshot.get('total_nodes', 0)}")
        lines.append("Health Status:")
        lines.append(f"  ✅ Healthy: {snapshot.get('healthy_nodes', 0)}")
        if snapshot.get("degraded_nodes", 0) > 0:
            lines.append(f"  ⚠️  Degraded: {snapshot['degraded_nodes']}")
        if snapshot.get("unhealthy_nodes", 0) > 0:
            lines.append(f"  ❌ Unhealthy: {snapshot['unhealthy_nodes']}")
        if snapshot.get("unknown_nodes", 0) > 0:
            lines.append(f"  ❓ Unknown: {snapshot['unknown_nodes']}")
        return lines

    def _format_nodes_by_role(self, nodes_by_role: dict[str, list[dict[str, Any]]]) -> list[str]:
        """Format nodes organized by role."""
        role_order = [
            "gateway/router",
            "firewall",
            "switch/ap",
            "server",
            "service",
            "nas",
            "client",
            "unknown",
        ]
        role_labels = {
            "gateway/router": "🌐 GATEWAYS & ROUTERS",
            "firewall": "🛡️  FIREWALLS",
            "switch/ap": "📡 SWITCHES & ACCESS POINTS",
            "server": "🖥️  SERVERS",
            "service": "⚙️  SERVICES",
            "nas": "💾 NAS DEVICES",
            "client": "💻 CLIENT DEVICES",
            "unknown": "❓ UNKNOWN DEVICES",
        }
        lines = []
        for role in role_order:
            if role in nodes_by_role and nodes_by_role[role]:
                lines.append(f"\n{role_labels.get(role, role.upper())}")
                lines.append("-" * 40)
                for node in nodes_by_role[role]:
                    lines.append(self._format_node_info(node))
        return lines

    def _format_gateways_section(
        self, gateways: list[dict[str, Any]], nodes: dict[str, Any]
    ) -> list[str]:
        """Format the gateway/ISP connectivity section."""
        if not gateways:
            return []
        lines = ["\n🌍 ISP & INTERNET CONNECTIVITY", "-" * 40]
        for gw in gateways:
            lines.append(self._format_gateway_info(gw, nodes))
        return lines

    def _collect_lan_devices(self, nodes: dict[str, Any]) -> list[dict[str, Any]]:
        """Collect devices with LAN port configurations."""
        lan_devices = []
        for node_id, node in nodes.items():
            lan_ports = node.get("lan_ports")
            if not lan_ports or not lan_ports.get("ports"):
                continue
            ports = lan_ports.get("ports", [])
            active_ports = [p for p in ports if p.get("status") == "active"]
            connected_ports = [
                p
                for p in active_ports
                if p.get("connected_device_id") or p.get("connected_device_name")
            ]
            lan_devices.append(
                {
                    "name": node.get("name", node_id),
                    "ip": node.get("ip", "N/A"),
                    "total_ports": len(ports),
                    "active_ports": len(active_ports),
                    "connected_ports": len(connected_ports),
                }
            )
        return lan_devices

    def _format_lan_infrastructure(self, lan_devices: list[dict[str, Any]]) -> list[str]:
        """Format the LAN infrastructure summary."""
        if not lan_devices:
            return []
        lines = ["\n🔌 LAN INFRASTRUCTURE", "-" * 40]
        lines.append(f"  Devices with LAN ports: {len(lan_devices)}")
        lines.append(f"  Total ports: {sum(d['total_ports'] for d in lan_devices)}")
        lines.append(f"  Active ports: {sum(d['active_ports'] for d in lan_devices)}")
        lines.append(f"  Connected ports: {sum(d['connected_ports'] for d in lan_devices)}")
        lines.append("\n  Port details are listed under each device above.")
        return lines

    def _collect_nodes_with_notes(self, nodes: dict[str, Any]) -> list[dict[str, Any]]:
        """Collect nodes that have user notes, excluding groups."""
        nodes_with_notes = []
        for node_id, node in nodes.items():
            node_role = node.get("role", "")
            if isinstance(node_role, str) and node_role.lower() == "group":
                continue
            if node.get("notes"):
                nodes_with_notes.append(
                    {
                        "name": node.get("name", node_id),
                        "ip": node.get("ip", "N/A"),
                        "notes": node.get("notes"),
                    }
                )
        return nodes_with_notes

    def _format_user_notes(self, nodes_with_notes: list[dict[str, Any]]) -> list[str]:
        """Format the user notes section."""
        if not nodes_with_notes:
            return []
        lines = ["\n📝 USER NOTES", "-" * 40]
        for node_info in nodes_with_notes:
            lines.append(f"  {node_info['name']} ({node_info['ip']}):")
            for note_line in node_info["notes"].strip().split("\n"):
                lines.append(f"    {note_line}")
        return lines

    def _build_context_from_snapshot(self, snapshot: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """Build context string and summary from a snapshot."""
        lines = ["=" * 60, "NETWORK TOPOLOGY INFORMATION", "=" * 60]

        timestamp = snapshot.get("timestamp", "")
        if timestamp:
            lines.append(f"\nSnapshot Time: {timestamp}")

        lines.extend(self._format_health_summary(snapshot))

        nodes = snapshot.get("nodes", {})
        nodes_by_role = self._group_nodes_by_role(nodes)
        lines.extend(self._format_nodes_by_role(nodes_by_role))

        gateways = snapshot.get("gateways", [])
        lines.extend(self._format_gateways_section(gateways, nodes))

        connections = snapshot.get("connections", [])
        if connections:
            lines.append(f"\n🔗 NETWORK CONNECTIONS: {len(connections)} total")

        lan_devices = self._collect_lan_devices(nodes)
        lines.extend(self._format_lan_infrastructure(lan_devices))

        nodes_with_notes = self._collect_nodes_with_notes(nodes)
        lines.extend(self._format_user_notes(nodes_with_notes))

        lines.append("\n" + "=" * 60)
        context = "\n".join(lines)

        summary = {
            "total_nodes": snapshot.get("total_nodes", 0),
            "healthy_nodes": snapshot.get("healthy_nodes", 0),
            "unhealthy_nodes": snapshot.get("unhealthy_nodes", 0),
            "gateway_count": len(gateways),
            "snapshot_timestamp": timestamp,
            "context_tokens_estimate": len(context) // 4,
        }
        return context, summary

    async def build_context_string(
        self, wait_for_data: bool = True, force_refresh: bool = False, network_id: str | None = None
    ) -> tuple[str, dict[str, Any]]:
        """
        Build a context string for the AI assistant with network information.
        Returns (context_string, summary_dict)

        Args:
            wait_for_data: If True and no snapshot available, wait and retry
            force_refresh: If True, bypass cache and fetch fresh data from the metrics service.
                          This also triggers the metrics service to regenerate its snapshot.
            network_id: The network ID to build context for (multi-tenant support).
                       If None, uses legacy single-network mode for backwards compatibility.
        """
        now = datetime.utcnow()

        # Check per-network cache (skip if force_refresh)
        if network_id in self._context_cache and not force_refresh:
            cached_context, cached_summary, cache_timestamp = self._context_cache[network_id]
            if (now - cache_timestamp).total_seconds() < self._cache_ttl_seconds:
                return cached_context, cached_summary

        # Try to fetch snapshot (force regeneration if force_refresh)
        snapshot = await self.fetch_network_snapshot(
            force_refresh=force_refresh, network_id=network_id
        )

        # If no snapshot and we should wait, try waiting for it
        if not snapshot and wait_for_data and not self.is_snapshot_available(network_id):
            logger.info(
                f"No snapshot available yet for network_id={network_id}, waiting for metrics service..."
            )
            snapshot = await self.wait_for_snapshot(max_attempts=3, network_id=network_id)

        if not snapshot:
            return (
                self._build_loading_context()
                if not self.is_snapshot_available(network_id)
                else self._build_fallback_context()
            )

        context, summary = self._build_context_from_snapshot(snapshot)
        self._context_cache[network_id] = (context, summary, now)
        return context, summary

    def _build_loading_context(self) -> tuple[str, dict[str, Any]]:
        """Build context when waiting for initial snapshot"""
        context = """
========================================
NETWORK TOPOLOGY INFORMATION
========================================

⏳ Network data is loading...

The network monitoring system is starting up and collecting initial data.
This typically takes 30-60 seconds after first launch.

I can still help answer general networking questions while we wait.
Once the network scan completes, I'll have full visibility into your topology.
========================================
"""
        summary = {
            "total_nodes": 0,
            "healthy_nodes": 0,
            "unhealthy_nodes": 0,
            "gateway_count": 0,
            "snapshot_timestamp": None,
            "context_tokens_estimate": len(context) // 4,
            "loading": True,
        }
        return context.strip(), summary

    def _build_fallback_context(self) -> tuple[str, dict[str, Any]]:
        """Build fallback context when metrics service is unavailable"""
        context = """
========================================
NETWORK TOPOLOGY INFORMATION
========================================

⚠️ Network data is temporarily unavailable.

The metrics service may be restarting or experiencing issues.
Previous network data should be restored shortly.

I can still help answer general networking questions or provide guidance
based on the information you provide directly.
========================================
"""
        summary = {
            "total_nodes": 0,
            "healthy_nodes": 0,
            "unhealthy_nodes": 0,
            "gateway_count": 0,
            "snapshot_timestamp": None,
            "context_tokens_estimate": len(context) // 4,
            "unavailable": True,
        }
        return context.strip(), summary

    def clear_cache(self, network_id: str | None = None):
        """Clear the cached context for a specific network or all networks.

        Args:
            network_id: If provided, only clear cache for this network.
                       If None, clears all cached contexts.
        """
        if network_id is not None:
            self._context_cache.pop(network_id, None)
        else:
            self._context_cache.clear()

    def reset_state(self, network_id: str | None = None):
        """Reset all state including snapshot availability.

        Args:
            network_id: If provided, only reset state for this network.
                       If None, resets all state.
        """
        self.clear_cache(network_id)
        if network_id is not None:
            self._snapshot_available.pop(network_id, None)
        else:
            self._snapshot_available.clear()
        self._last_check_time = None

    def get_status(self, network_id: str | None = None) -> dict[str, Any]:
        """Get current service status.

        Args:
            network_id: If provided, get status for specific network.
                       If None, returns overall status.
        """
        if network_id is not None:
            # Status for specific network
            cache_entry = self._context_cache.get(network_id)
            return {
                "network_id": network_id,
                "snapshot_available": self._snapshot_available.get(network_id, False),
                "cached": cache_entry is not None,
                "last_check": self._last_check_time.isoformat() if self._last_check_time else None,
                "cache_age_seconds": (
                    (datetime.utcnow() - cache_entry[2]).total_seconds() if cache_entry else None
                ),
            }
        else:
            # Overall status (backwards compatible)
            any_snapshot_available = (
                any(self._snapshot_available.values()) if self._snapshot_available else False
            )
            any_cached = len(self._context_cache) > 0
            return {
                "snapshot_available": any_snapshot_available,
                "cached": any_cached,
                "cached_networks": list(self._context_cache.keys()),
                "available_networks": [k for k, v in self._snapshot_available.items() if v],
                "last_check": self._last_check_time.isoformat() if self._last_check_time else None,
            }


# Singleton instance
metrics_context_service = MetricsContextService()
