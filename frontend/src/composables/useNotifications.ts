/**
 * Composable for notification settings API
 */

import { ref } from 'vue';
import axios from 'axios';

// Types
export interface EmailConfig {
  enabled: boolean;
  email_address: string;
}

export interface DiscordChannelConfig {
  guild_id: string;
  channel_id: string;
  guild_name?: string;
  channel_name?: string;
}

export interface DiscordConfig {
  enabled: boolean;
  delivery_method: 'channel' | 'dm';
  discord_user_id?: string;
  channel_config?: DiscordChannelConfig;
}

export type NotificationType = 
  | 'device_offline'
  | 'device_online'
  | 'device_degraded'
  | 'anomaly_detected'
  | 'high_latency'
  | 'packet_loss'
  | 'isp_issue'
  | 'security_alert'
  | 'scheduled_maintenance'
  | 'system_status'
  | 'cartographer_down'
  | 'cartographer_up';

export type NotificationPriority = 'low' | 'medium' | 'high' | 'critical';

// Priority overrides for specific notification types (user customization)
export type NotificationTypePriorityOverrides = Partial<Record<NotificationType, NotificationPriority>>;

export interface NotificationPreferences {
  network_id: number;
  network_name?: string;
  owner_user_id?: string;
  enabled: boolean;
  email: EmailConfig;
  discord: DiscordConfig;
  enabled_notification_types: NotificationType[];
  minimum_priority: NotificationPriority;
  notification_type_priorities?: NotificationTypePriorityOverrides; // User-defined priority overrides
  quiet_hours_enabled: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  quiet_hours_bypass_priority?: NotificationPriority | null; // Alerts at or above this priority bypass quiet hours
  timezone?: string; // IANA timezone name (e.g., "America/New_York") for quiet hours
  max_notifications_per_hour: number;
  created_at: string;
  updated_at: string;
}

export interface NotificationServiceStatus {
  email_configured: boolean;
  discord_configured: boolean;
  discord_bot_connected: boolean;
  ml_model_status: {
    model_version: string;
    is_trained: boolean;
    devices_tracked: number;
    anomalies_detected_total: number;
    anomalies_detected_24h: number;
  };
}

export interface DiscordBotInfo {
  bot_name: string;
  bot_id?: string;
  invite_url?: string;
  is_connected: boolean;
  connected_guilds: number;
}

export interface DiscordGuild {
  id: string;
  name: string;
  icon_url?: string;
  member_count?: number;
}

export interface DiscordChannel {
  id: string;
  name: string;
  type: string;
}

export interface NotificationStats {
  total_sent_24h: number;
  total_sent_7d: number;
  by_channel: Record<string, number>;
  by_type: Record<string, number>;
  success_rate: number;
  anomalies_detected_24h: number;
}

export interface TestNotificationResult {
  success: boolean;
  channel: string;
  message: string;
  error?: string;
}

export type ScheduledBroadcastStatus = 'pending' | 'sent' | 'cancelled' | 'failed';

export interface ScheduledBroadcast {
  id: string;
  title: string;
  message: string;
  event_type: NotificationType;
  priority: NotificationPriority;
  network_id: number;
  scheduled_at: string;
  timezone?: string;  // IANA timezone name for display
  created_at: string;
  created_by: string;
  status: ScheduledBroadcastStatus;
  sent_at?: string;
  users_notified: number;
  error_message?: string;
}

export interface ScheduledBroadcastUpdate {
  title?: string;
  message?: string;
  event_type?: NotificationType;
  priority?: NotificationPriority;
  scheduled_at?: string;
  timezone?: string;
}

export interface ScheduledBroadcastResponse {
  broadcasts: ScheduledBroadcast[];
  total_count: number;
}

// ==================== Global Preferences (Cartographer Up/Down) ====================

export interface GlobalUserPreferences {
  user_id: string;
  email_address?: string;
  cartographer_up_enabled: boolean;
  cartographer_down_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface GlobalUserPreferencesUpdate {
  email_address?: string;
  cartographer_up_enabled?: boolean;
  cartographer_down_enabled?: boolean;
}

const API_BASE = '/api/notifications';

export function useNotifications(networkId?: number) {
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const currentNetworkId = ref<number | undefined>(networkId);

  // Set the network ID for subsequent calls
  function setNetworkId(id: number) {
    currentNetworkId.value = id;
  }

  // Get network-specific API path
  function getNetworkPath(): string {
    if (!currentNetworkId.value) {
      throw new Error('Network ID is required for notification operations');
    }
    return `${API_BASE}/networks/${currentNetworkId.value}`;
  }

  // Get notification preferences for a network
  async function getPreferences(netId?: number): Promise<NotificationPreferences> {
    const id = netId ?? currentNetworkId.value;
    if (!id) throw new Error('Network ID is required');
    
    isLoading.value = true;
    error.value = null;
    try {
      const response = await axios.get<NotificationPreferences>(`${API_BASE}/networks/${id}/preferences`);
      return response.data;
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message;
      throw new Error(error.value || 'Failed to get preferences');
    } finally {
      isLoading.value = false;
    }
  }

  // Update notification preferences for a network
  // Note: Does not set isLoading to avoid UI flicker/scroll reset during background saves
  async function updatePreferences(
    update: Partial<NotificationPreferences>,
    netId?: number
  ): Promise<NotificationPreferences> {
    const id = netId ?? currentNetworkId.value;
    if (!id) throw new Error('Network ID is required');
    
    error.value = null;
    try {
      const response = await axios.put<NotificationPreferences>(`${API_BASE}/networks/${id}/preferences`, update);
      return response.data;
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message;
      throw new Error(error.value || 'Failed to update preferences');
    }
  }

  // Get service status
  async function getServiceStatus(): Promise<NotificationServiceStatus> {
    const response = await axios.get<NotificationServiceStatus>(`${API_BASE}/status`);
    return response.data;
  }

  // Get Discord bot info
  async function getDiscordBotInfo(): Promise<DiscordBotInfo> {
    const response = await axios.get<DiscordBotInfo>(`${API_BASE}/discord/info`);
    return response.data;
  }

  // Get Discord guilds
  async function getDiscordGuilds(): Promise<DiscordGuild[]> {
    const response = await axios.get<{ guilds: DiscordGuild[] }>(`${API_BASE}/discord/guilds`);
    return response.data.guilds;
  }

  // Get Discord channels for a guild
  async function getDiscordChannels(guildId: string): Promise<DiscordChannel[]> {
    const response = await axios.get<{ channels: DiscordChannel[] }>(
      `${API_BASE}/discord/guilds/${guildId}/channels`
    );
    return response.data.channels;
  }

  // Get Discord invite URL
  async function getDiscordInviteUrl(): Promise<string> {
    const response = await axios.get<{ invite_url: string }>(`${API_BASE}/discord/invite-url`);
    return response.data.invite_url;
  }

  // Send test notification for a network
  async function sendTestNotification(
    channel: 'email' | 'discord',
    message?: string,
    netId?: number
  ): Promise<TestNotificationResult> {
    const id = netId ?? currentNetworkId.value;
    if (!id) throw new Error('Network ID is required');
    
    const response = await axios.post<TestNotificationResult>(`${API_BASE}/networks/${id}/test`, { channel, message });
    return response.data;
  }

  // Get notification stats for a network
  async function getStats(netId?: number): Promise<NotificationStats> {
    const id = netId ?? currentNetworkId.value;
    if (!id) throw new Error('Network ID is required');
    
    const response = await axios.get<NotificationStats>(`${API_BASE}/networks/${id}/stats`);
    return response.data;
  }

  // Send broadcast notification (owner only, network-scoped)
  async function sendBroadcastNotification(
    networkId: number,
    title: string,
    message: string,
    eventType: NotificationType = 'scheduled_maintenance',
    priority: NotificationPriority = 'medium'
  ): Promise<{ success: boolean; users_notified: number }> {
    const response = await axios.post<{ success: boolean; users_notified: number }>(
      `${API_BASE}/broadcast`,
      {
        network_id: networkId,
        title,
        message,
        event_type: eventType,
        priority,
      }
    );
    return response.data;
  }

  // Get scheduled broadcasts (owner only)
  async function getScheduledBroadcasts(includeCompleted: boolean = false): Promise<ScheduledBroadcastResponse> {
    const response = await axios.get<ScheduledBroadcastResponse>(
      `${API_BASE}/scheduled`,
      { params: { include_completed: includeCompleted } }
    );
    return response.data;
  }

  // Schedule a broadcast (owner only, network-scoped)
  async function scheduleBroadcast(
    networkId: number,
    title: string,
    message: string,
    scheduledAt: Date,
    eventType: NotificationType = 'scheduled_maintenance',
    priority: NotificationPriority = 'medium',
    timezone?: string
  ): Promise<ScheduledBroadcast> {
    const response = await axios.post<ScheduledBroadcast>(
      `${API_BASE}/scheduled`,
      {
        network_id: networkId,
        title,
        message,
        event_type: eventType,
        priority,
        scheduled_at: scheduledAt.toISOString(),
        timezone: timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
      }
    );
    return response.data;
  }

  // Update a scheduled broadcast (owner only, only pending broadcasts)
  async function updateScheduledBroadcast(
    broadcastId: string,
    update: ScheduledBroadcastUpdate
  ): Promise<ScheduledBroadcast> {
    // Convert scheduled_at to ISO string if it's provided
    const body: Record<string, unknown> = { ...update };
    if (update.scheduled_at) {
      body.scheduled_at = update.scheduled_at;
    }
    
    const response = await axios.patch<ScheduledBroadcast>(
      `${API_BASE}/scheduled/${broadcastId}`,
      body
    );
    return response.data;
  }

  // Cancel a scheduled broadcast (owner only)
  async function cancelScheduledBroadcast(broadcastId: string): Promise<void> {
    await axios.post(`${API_BASE}/scheduled/${broadcastId}/cancel`);
  }

  // Delete a scheduled broadcast (owner only)
  async function deleteScheduledBroadcast(broadcastId: string): Promise<void> {
    await axios.delete(`${API_BASE}/scheduled/${broadcastId}`);
  }

  // ==================== Silenced Devices (Monitoring Disabled) ====================

  // Get list of silenced devices
  async function getSilencedDevices(): Promise<string[]> {
    const response = await axios.get<{ devices: string[] }>(`${API_BASE}/silenced-devices`);
    return response.data.devices;
  }

  // Set full list of silenced devices
  async function setSilencedDevices(deviceIps: string[]): Promise<void> {
    await axios.post(`${API_BASE}/silenced-devices`, deviceIps);
  }

  // Silence a specific device (disable monitoring notifications)
  async function silenceDevice(deviceIp: string): Promise<void> {
    await axios.post(`${API_BASE}/silenced-devices/${encodeURIComponent(deviceIp)}`);
  }

  // Unsilence a device (enable monitoring notifications)
  async function unsilenceDevice(deviceIp: string): Promise<void> {
    await axios.delete(`${API_BASE}/silenced-devices/${encodeURIComponent(deviceIp)}`);
  }

  // Check if a device is silenced
  async function isDeviceSilenced(deviceIp: string): Promise<boolean> {
    const response = await axios.get<{ silenced: boolean }>(
      `${API_BASE}/silenced-devices/${encodeURIComponent(deviceIp)}`
    );
    return response.data.silenced;
  }

  // Get global notification preferences (Cartographer Up/Down)
  async function getGlobalPreferences(): Promise<GlobalUserPreferences> {
    const response = await axios.get<GlobalUserPreferences>(`${API_BASE}/global/preferences`);
    return response.data;
  }

  // Update global notification preferences (Cartographer Up/Down)
  async function updateGlobalPreferences(
    update: GlobalUserPreferencesUpdate
  ): Promise<GlobalUserPreferences> {
    const response = await axios.put<GlobalUserPreferences>(
      `${API_BASE}/global/preferences`,
      update
    );
    return response.data;
  }

  return {
    isLoading,
    error,
    currentNetworkId,
    setNetworkId,
    getPreferences,
    updatePreferences,
    getServiceStatus,
    getDiscordBotInfo,
    getDiscordGuilds,
    getDiscordChannels,
    getDiscordInviteUrl,
    sendTestNotification,
    getStats,
    sendBroadcastNotification,
    getScheduledBroadcasts,
    scheduleBroadcast,
    updateScheduledBroadcast,
    cancelScheduledBroadcast,
    deleteScheduledBroadcast,
    getSilencedDevices,
    setSilencedDevices,
    silenceDevice,
    unsilenceDevice,
    isDeviceSilenced,
    getGlobalPreferences,
    updateGlobalPreferences,
  };
}

// Notification type labels, icons, and default priorities
export const NOTIFICATION_TYPE_INFO: Record<NotificationType, { label: string; icon: string; description: string; defaultPriority: NotificationPriority }> = {
  device_offline: { 
    label: 'Device Offline', 
    icon: '🔴', 
    description: 'When a device stops responding',
    defaultPriority: 'high'
  },
  device_online: { 
    label: 'Device Online', 
    icon: '🟢', 
    description: 'When a device comes back online',
    defaultPriority: 'low'
  },
  device_degraded: { 
    label: 'Device Degraded', 
    icon: '🟡', 
    description: 'When a device has degraded performance',
    defaultPriority: 'medium'
  },
  anomaly_detected: { 
    label: 'Anomaly Detected', 
    icon: '⚠️', 
    description: 'ML-detected unusual behavior',
    defaultPriority: 'high'
  },
  high_latency: { 
    label: 'High Latency', 
    icon: '🐌', 
    description: 'Unusual latency spikes',
    defaultPriority: 'medium'
  },
  packet_loss: { 
    label: 'Packet Loss', 
    icon: '📉', 
    description: 'Significant packet loss',
    defaultPriority: 'medium'
  },
  isp_issue: { 
    label: 'ISP Issue', 
    icon: '🌐', 
    description: 'Internet connectivity problems',
    defaultPriority: 'high'
  },
  security_alert: { 
    label: 'Security Alert', 
    icon: '🔒', 
    description: 'Security-related notifications',
    defaultPriority: 'critical'
  },
  scheduled_maintenance: { 
    label: 'Maintenance', 
    icon: '🔧', 
    description: 'Planned maintenance notices',
    defaultPriority: 'low'
  },
  system_status: { 
    label: 'System Status', 
    icon: 'ℹ️', 
    description: 'General system updates',
    defaultPriority: 'low'
  },
  cartographer_down: { 
    label: 'Cartographer Down', 
    icon: '🚨', 
    description: 'When Cartographer service goes offline',
    defaultPriority: 'critical'
  },
  cartographer_up: { 
    label: 'Cartographer Up', 
    icon: '✅', 
    description: 'When Cartographer service comes back online',
    defaultPriority: 'medium'
  },
};

export const PRIORITY_INFO: Record<NotificationPriority, { label: string; color: string }> = {
  low: { label: 'Low', color: 'emerald' },
  medium: { label: 'Medium', color: 'amber' },
  high: { label: 'High', color: 'orange' },
  critical: { label: 'Critical', color: 'red' },
};

