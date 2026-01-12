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

# State persistence file
_STATE_FILE = Path(settings.health_data_dir) / "previous_states.json"


def _load_states() -> dict[str, str]:
    """Load previous states from disk"""
    try:
        if _STATE_FILE.exists():
            with open(_STATE_FILE, "r") as f:
                states = json.load(f)
                logger.info(f"Loaded {len(states)} previous device states from disk")
                return states
    except Exception as e:
        logger.warning(f"Failed to load previous states from disk: {e}")
    return {}


def _save_states():
    """Save previous states to disk"""
    try:
        _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_STATE_FILE, "w") as f:
            json.dump(_previous_states, f)
    except Exception as e:
        logger.warning(f"Failed to save previous states to disk: {e}")


# Track previous states for state change detection - loaded from disk
_previous_states: dict[str, str] = _load_states()


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

    Note: If network_id is None, the notification service will not send notifications
    but will still train the ML model.
    """
    global _previous_states

    # Get previous state for this device
    previous_state = _previous_states.get(device_ip)

    # Update tracked state
    current_state = "online" if success else "offline"
    state_changed = previous_state != current_state
    _previous_states[device_ip] = current_state

    # Persist state changes to disk (only on state change to reduce I/O)
    if state_changed or previous_state is None:
        _save_states()

    # Skip reporting if no network_id (device not part of a monitored network)
    if network_id is None:
        logger.debug(f"Skipping notification report for {device_ip} (no network_id)")
        return False

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
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

            response = await client.post(
                f"{settings.notification_service_url}/api/notifications/process-health-check",
                params=params,
            )

            if response.status_code == 200:
                return True
            else:
                logger.warning(
                    f"Notification service returned {response.status_code}: {response.text}"
                )
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


def clear_state_tracking():
    """Clear tracked device states (for testing/reset)"""
    global _previous_states
    _previous_states.clear()
    _save_states()  # Persist the cleared state


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
