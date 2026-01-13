"""
Notification reporter service.

Reports health check results to the notification service for
anomaly detection and alerting.
"""

import asyncio
import json
import logging
from pathlib import Path

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

# State persistence directory (per-network state files)
_STATE_DIR = Path(settings.health_data_dir) / "network_states"


def _get_state_file(network_id: str) -> Path:
    """Get state file path for a specific network"""
    return _STATE_DIR / f"{network_id}.json"


def _load_network_states(network_id: str) -> dict[str, str]:
    """Load previous states for a specific network from disk"""
    try:
        state_file = _get_state_file(network_id)
        if state_file.exists():
            with open(state_file, "r") as f:
                states = json.load(f)
                logger.info(f"Loaded {len(states)} device states for network {network_id}")
                return states
    except Exception as e:
        logger.warning(f"Failed to load states for network {network_id}: {e}")
    return {}


def _save_network_states(network_id: str):
    """Save states for a specific network to disk"""
    try:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        states = _previous_states.get(network_id, {})
        with open(_get_state_file(network_id), "w") as f:
            json.dump(states, f)
    except Exception as e:
        logger.warning(f"Failed to save states for network {network_id}: {e}")


# Track previous states per-network: {network_id: {device_ip: state}}
_previous_states: dict[str, dict[str, str]] = {}


def _build_health_check_params(
    device_ip: str,
    success: bool,
    network_id: str,
    latency_ms: float | None,
    packet_loss: float | None,
    device_name: str | None,
    previous_state: str | None,
) -> dict:
    """Build request params for health check report."""
    params = {
        "device_ip": device_ip,
        "success": success,
        "network_id": network_id,
    }
    if latency_ms is not None:
        params["latency_ms"] = latency_ms
    if packet_loss is not None:
        params["packet_loss"] = packet_loss
    if device_name is not None:
        params["device_name"] = device_name
    if previous_state is not None:
        params["previous_state"] = previous_state
    return params


def _update_device_state(network_id: str, device_ip: str, success: bool) -> tuple[str | None, bool]:
    """Update tracked device state for a network and return (previous_state, state_changed)."""
    global _previous_states

    # Ensure network state dict exists, load from disk if first access
    if network_id not in _previous_states:
        _previous_states[network_id] = _load_network_states(network_id)

    network_states = _previous_states[network_id]
    previous_state = network_states.get(device_ip)
    current_state = "online" if success else "offline"
    state_changed = previous_state != current_state
    network_states[device_ip] = current_state

    if state_changed or previous_state is None:
        _save_network_states(network_id)

    return previous_state, state_changed


async def report_health_check(
    device_ip: str,
    success: bool,
    network_id: str | None = None,
    latency_ms: float | None = None,
    packet_loss: float | None = None,
    device_name: str | None = None,
) -> bool:
    """
    Report a health check result to the notification service.

    This enables:
    - ML-based anomaly detection
    - Automatic notification dispatch

    Args:
        device_ip: IP address of the device
        success: Whether the health check succeeded
        network_id: The network this device belongs to (required for notifications)
        latency_ms: Optional latency measurement
        packet_loss: Optional packet loss percentage
        device_name: Optional device name

    Returns True if successfully reported, False otherwise.

    Note: If network_id is None, nothing is tracked or reported. This prevents
    cross-network state pollution from unregistered device checks.
    """
    # CRITICAL: Check network_id FIRST before any state tracking
    # This prevents state pollution from devices checked without a network context
    if network_id is None:
        logger.debug(f"Skipping notification report for {device_ip} (no network_id)")
        return False

    # Only track state for devices with a valid network_id
    previous_state, _ = _update_device_state(network_id, device_ip, success)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            params = _build_health_check_params(
                device_ip, success, network_id, latency_ms, packet_loss, device_name, previous_state
            )
            response = await client.post(
                f"{settings.notification_service_url}/api/notifications/process-health-check",
                params=params,
            )
            if response.status_code == 200:
                return True
            logger.warning(f"Notification service returned {response.status_code}: {response.text}")
            return False
    except httpx.ConnectError:
        logger.debug("Notification service not available")
        return False
    except Exception as e:
        logger.warning(f"Failed to report health check to notification service: {e}")
        return False


async def report_health_checks_batch(
    results: dict[str, tuple],  # ip -> (success, latency_ms, packet_loss, device_name)
) -> int:
    """
    Report multiple health check results in parallel.

    Returns the number of successfully reported checks.
    """
    tasks = []
    for device_ip, (success, latency_ms, packet_loss, device_name) in results.items():
        tasks.append(
            report_health_check(
                device_ip=device_ip,
                success=success,
                latency_ms=latency_ms,
                packet_loss=packet_loss,
                device_name=device_name,
            )
        )

    batch_results = await asyncio.gather(*tasks)
    return sum(1 for r in batch_results if r)


def clear_state_tracking(network_id: str | None = None):
    """Clear tracked device states (for testing/reset).

    Args:
        network_id: If provided, only clear state for that network.
                   If None, clear all network states.
    """
    global _previous_states
    if network_id is not None:
        _previous_states.pop(network_id, None)
        state_file = _get_state_file(network_id)
        if state_file.exists():
            state_file.unlink()
    else:
        _previous_states.clear()
        # Clear all state files
        if _STATE_DIR.exists():
            for state_file in _STATE_DIR.glob("*.json"):
                state_file.unlink()


async def sync_devices_with_notification_service(
    device_ips: list, network_id: str | None = None
) -> bool:
    """
    Sync the current list of monitored devices with the notification service.

    This ensures the ML anomaly detector only tracks devices that are
    currently in the network, preventing stale device counts.

    Args:
        device_ips: List of device IP addresses
        network_id: The network ID these devices belong to (required for per-network tracking)

    Returns True if successfully synced, False otherwise.
    """
    if network_id is None:
        logger.debug("Skipping device sync (no network_id provided)")
        return False

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{settings.notification_service_url}/api/notifications/ml/sync-devices",
                params={"network_id": network_id},
                json=device_ips,
            )

            if response.status_code == 200:
                logger.info(
                    f"Synced {len(device_ips)} devices with notification service for network {network_id}"
                )
                return True
            else:
                logger.warning(
                    f"Notification service returned {response.status_code}: {response.text}"
                )
                return False

    except httpx.ConnectError:
        logger.debug("Notification service not available for device sync")
        return False
    except Exception as e:
        logger.warning(f"Failed to sync devices with notification service: {e}")
        return False
