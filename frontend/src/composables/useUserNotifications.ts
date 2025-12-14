/**
 * Composable for user-specific notification preferences API
 */

import { ref } from 'vue';
import axios from 'axios';

export type NotificationPriority = 'low' | 'medium' | 'high' | 'critical';

export type NetworkNotificationType = 
  | 'device_offline'
  | 'device_online'
  | 'device_degraded'
  | 'anomaly_detected'
  | 'high_latency'
  | 'packet_loss'
  | 'isp_issue'
  | 'security_alert'
  | 'scheduled_maintenance'
  | 'system_status';

export type GlobalNotificationType = 'cartographer_up' | 'cartographer_down';

export interface NetworkPreferences {
  user_id: string;
  network_id: number;
  email_enabled: boolean;
  discord_enabled: boolean;
  discord_user_id?: string;
  enabled_types: string[];
  type_priorities: Record<string, string>;
  minimum_priority: string;
  quiet_hours_enabled: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  quiet_hours_timezone?: string;
  quiet_hours_bypass_priority?: string;
  created_at: string;
  updated_at: string;
}

export interface GlobalPreferences {
  user_id: string;
  email_enabled: boolean;
  discord_enabled: boolean;
  discord_user_id?: string;
  cartographer_up_enabled: boolean;
  cartographer_down_enabled: boolean;
  minimum_priority: string;
  quiet_hours_enabled: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  quiet_hours_timezone?: string;
  quiet_hours_bypass_priority?: string;
  created_at: string;
  updated_at: string;
}

export interface DiscordLinkInfo {
  linked: boolean;
  discord_id?: string;
  discord_username?: string;
  discord_avatar?: string;
}

const API_BASE = '/api/notifications';

export function useUserNotifications() {
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Network preferences
  async function getNetworkPreferences(networkId: number): Promise<NetworkPreferences> {
    isLoading.value = true;
    error.value = null;
    try {
      const response = await axios.get<NetworkPreferences>(
        `${API_BASE}/users/me/networks/${networkId}/preferences`
      );
      return response.data;
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message;
      throw e;
    } finally {
      isLoading.value = false;
    }
  }

  async function updateNetworkPreferences(
    networkId: number,
    update: Partial<NetworkPreferences>
  ): Promise<NetworkPreferences> {
    error.value = null;
    try {
      const response = await axios.put<NetworkPreferences>(
        `${API_BASE}/users/me/networks/${networkId}/preferences`,
        update
      );
      return response.data;
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message;
      throw e;
    }
  }

  async function deleteNetworkPreferences(networkId: number): Promise<void> {
    error.value = null;
    try {
      await axios.delete(`${API_BASE}/users/me/networks/${networkId}/preferences`);
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message;
      throw e;
    }
  }

  // Global preferences
  async function getGlobalPreferences(): Promise<GlobalPreferences> {
    isLoading.value = true;
    error.value = null;
    try {
      const response = await axios.get<GlobalPreferences>(
        `${API_BASE}/users/me/global/preferences`
      );
      return response.data;
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message;
      throw e;
    } finally {
      isLoading.value = false;
    }
  }

  async function updateGlobalPreferences(
    update: Partial<GlobalPreferences>
  ): Promise<GlobalPreferences> {
    error.value = null;
    try {
      const response = await axios.put<GlobalPreferences>(
        `${API_BASE}/users/me/global/preferences`,
        update
      );
      return response.data;
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message;
      throw e;
    }
  }

  // Test notifications
  async function testNetworkNotification(
    networkId: number,
    channel: 'email' | 'discord'
  ): Promise<{ success: boolean; message: string; error?: string }> {
    error.value = null;
    try {
      const response = await axios.post(
        `${API_BASE}/users/me/networks/${networkId}/test`,
        { channel }
      );
      return response.data;
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message;
      throw e;
    }
  }

  async function testGlobalNotification(
    channel: 'email' | 'discord'
  ): Promise<{ success: boolean; message: string; error?: string }> {
    error.value = null;
    try {
      const response = await axios.post(
        `${API_BASE}/users/me/global/test`,
        { channel }
      );
      return response.data;
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message;
      throw e;
    }
  }

  // Discord OAuth - Context-aware (per-network or global)
  async function initiateDiscordOAuth(
    contextType: 'network' | 'global' = 'global',
    networkId?: number
  ): Promise<{ authorization_url: string }> {
    error.value = null;
    try {
      const params: Record<string, string | number> = { context_type: contextType };
      if (contextType === 'network' && networkId !== undefined) {
        params.network_id = networkId;
      }
      const response = await axios.get<{ authorization_url: string }>(
        `${API_BASE}/auth/discord/link`,
        { params }
      );
      return response.data;
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message;
      throw e;
    }
  }

  async function getDiscordLink(
    contextType: 'network' | 'global' = 'global',
    networkId?: number
  ): Promise<DiscordLinkInfo> {
    error.value = null;
    try {
      const params: Record<string, string | number> = { context_type: contextType };
      if (contextType === 'network' && networkId !== undefined) {
        params.network_id = networkId;
      }
      const response = await axios.get<DiscordLinkInfo>(
        `${API_BASE}/users/me/discord`,
        { params }
      );
      return response.data;
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message;
      throw e;
    }
  }

  async function unlinkDiscord(
    contextType: 'network' | 'global' = 'global',
    networkId?: number
  ): Promise<void> {
    error.value = null;
    try {
      const params: Record<string, string | number> = { context_type: contextType };
      if (contextType === 'network' && networkId !== undefined) {
        params.network_id = networkId;
      }
      await axios.delete(`${API_BASE}/users/me/discord/link`, { params });
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message;
      throw e;
    }
  }

  // Service status
  async function getServiceStatus(): Promise<{
    email_configured: boolean;
    discord_configured: boolean;
    discord_bot_connected: boolean;
  }> {
    try {
      const response = await axios.get(`${API_BASE}/status`);
      return response.data;
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message;
      throw e;
    }
  }

  // Anomaly stats (network only)
  async function getAnomalyStats(networkId: number): Promise<{
    devices_tracked: number;
    anomalies_detected_24h: number;
    is_trained: boolean;
  }> {
    try {
      // Use the notifications API which proxies to notification service
      const response = await axios.get(`${API_BASE}/ml/status`, {
        params: { network_id: networkId }
      });
      return {
        devices_tracked: response.data.devices_tracked || 0,
        anomalies_detected_24h: response.data.anomalies_detected_24h || 0,
        is_trained: response.data.is_trained || false,
      };
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message;
      throw e;
    }
  }

  return {
    isLoading,
    error,
    getNetworkPreferences,
    updateNetworkPreferences,
    deleteNetworkPreferences,
    getGlobalPreferences,
    updateGlobalPreferences,
    testNetworkNotification,
    testGlobalNotification,
    initiateDiscordOAuth,
    getDiscordLink,
    unlinkDiscord,
    getServiceStatus,
    getAnomalyStats,
  };
}
