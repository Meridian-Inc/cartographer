<template>
	<Teleport to="body">
		<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" @click.self="$emit('close')">
			<div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-2xl flex flex-col max-h-[90vh]">
				<!-- Header -->
				<div class="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 rounded-t-xl">
					<div class="flex items-center gap-3">
						<div class="w-9 h-9 rounded-lg bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center">
							<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-violet-600 dark:text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
							</svg>
						</div>
						<div>
							<h2 class="text-lg font-semibold text-slate-900 dark:text-white">Send Network Notification</h2>
							<p class="text-xs text-slate-500 dark:text-slate-400">Send a notification to all users in this network</p>
						</div>
					</div>
					<button
						@click="$emit('close')"
						class="p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
					>
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>

				<!-- Tabs -->
				<div class="flex border-b border-slate-200 dark:border-slate-700 px-6">
					<button
						@click="activeTab = 'compose'"
						:class="[
							'px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-colors',
							activeTab === 'compose'
								? 'border-violet-600 text-violet-600 dark:text-violet-400'
								: 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
						]"
					>
						Compose
					</button>
					<button
						@click="activeTab = 'scheduled'; loadScheduledBroadcasts()"
						:class="[
							'px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-colors flex items-center gap-2',
							activeTab === 'scheduled'
								? 'border-violet-600 text-violet-600 dark:text-violet-400'
								: 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
						]"
					>
						Scheduled
						<span v-if="scheduledBroadcasts.length > 0" class="px-1.5 py-0.5 text-xs rounded-full bg-violet-100 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400">
							{{ scheduledBroadcasts.length }}
						</span>
					</button>
				</div>

				<!-- Content -->
				<div class="flex-1 overflow-auto p-6">
					<!-- Compose Tab -->
					<div v-if="activeTab === 'compose'" class="space-y-5">
						<!-- Type -->
						<div>
							<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
								Notification Type
							</label>
							<select
								v-model="form.type"
								class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
							>
								<option value="scheduled_maintenance">Maintenance</option>
								<option value="system_status">System Status</option>
								<option value="security_alert">Security Alert</option>
								<option value="isp_issue">ISP Issue</option>
								<option value="device_offline">Device Offline</option>
								<option value="device_online">Device Online</option>
								<option value="device_degraded">Device Degraded</option>
								<option value="anomaly_detected">Anomaly Detected</option>
								<option value="high_latency">High Latency</option>
								<option value="packet_loss">Packet Loss</option>
							</select>
						</div>

						<!-- Priority -->
						<div>
							<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
								Priority
							</label>
							<select
								v-model="form.priority"
								class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
							>
								<option value="low">Low</option>
								<option value="medium">Medium</option>
								<option value="high">High</option>
								<option value="critical">Critical</option>
							</select>
						</div>

						<!-- Title -->
						<div>
							<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
								Title
							</label>
							<input
								v-model="form.title"
								type="text"
								placeholder="Notification title"
								class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
							/>
						</div>

						<!-- Message -->
						<div>
							<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
								Message
							</label>
							<textarea
								v-model="form.message"
								rows="3"
								placeholder="Notification message"
								class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white resize-none"
							></textarea>
						</div>

						<!-- Schedule -->
						<div class="space-y-3">
							<div class="flex items-center gap-3">
								<input
									type="radio"
									id="send-now"
									value="now"
									v-model="scheduleMode"
									class="w-4 h-4 text-violet-600"
								/>
								<label for="send-now" class="text-sm font-medium text-slate-700 dark:text-slate-300">
									Send immediately
								</label>
							</div>
							<div class="flex items-center gap-3">
								<input
									type="radio"
									id="schedule"
									value="schedule"
									v-model="scheduleMode"
									class="w-4 h-4 text-violet-600"
								/>
								<label for="schedule" class="text-sm font-medium text-slate-700 dark:text-slate-300">
									Schedule for later
								</label>
							</div>
							<div v-if="scheduleMode === 'schedule'" class="ml-7 space-y-2">
								<input
									v-model="scheduledDateTime"
									type="datetime-local"
									:min="minScheduleDateTime"
									class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
								/>
								<p class="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1">
									<svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
									</svg>
									Time is in your local timezone ({{ detectedTimezone }})
								</p>
							</div>
						</div>

						<!-- Error/Success Message -->
						<div v-if="error" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg">
							<p class="text-sm text-red-700 dark:text-red-400">{{ error }}</p>
						</div>
						<div v-if="successMessage" class="p-3 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-700 rounded-lg">
							<p class="text-sm text-emerald-700 dark:text-emerald-400">{{ successMessage }}</p>
						</div>
					</div>

					<!-- Scheduled Tab -->
					<div v-else-if="activeTab === 'scheduled'" class="space-y-4">
						<div v-if="loadingScheduled" class="flex items-center justify-center py-8">
							<svg class="animate-spin h-6 w-6 text-violet-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
							</svg>
						</div>

						<div v-else-if="scheduledBroadcasts.length === 0" class="text-center py-8">
							<svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto text-slate-300 dark:text-slate-600 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
								<path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
							<p class="text-slate-500 dark:text-slate-400">No scheduled broadcasts</p>
							<p class="text-sm text-slate-400 dark:text-slate-500 mt-1">Schedule a notification using the Compose tab</p>
						</div>

						<div v-else class="space-y-3">
							<div 
								v-for="broadcast in scheduledBroadcasts" 
								:key="broadcast.id"
								class="p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg border border-slate-200 dark:border-slate-600"
							>
								<div class="flex items-start justify-between gap-3">
									<div class="flex-1 min-w-0">
										<div class="flex items-center gap-2 mb-1">
											<span class="text-lg">{{ getTypeIcon(broadcast.event_type) }}</span>
											<p class="font-medium text-slate-900 dark:text-white truncate">{{ broadcast.title }}</p>
										</div>
										<p class="text-sm text-slate-500 dark:text-slate-400 line-clamp-2 mb-2">{{ broadcast.message }}</p>
										<div class="flex items-center gap-2 flex-wrap">
											<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-400">
												<svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
													<path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
												</svg>
												{{ formatScheduledTime(broadcast.scheduled_at) }}
											</span>
											<span 
												class="px-2 py-0.5 rounded text-xs font-medium"
												:class="getPriorityClass(broadcast.priority)"
											>
												{{ broadcast.priority }}
											</span>
											<span v-if="broadcast.timezone" class="px-2 py-0.5 rounded text-xs font-medium bg-slate-100 dark:bg-slate-600 text-slate-600 dark:text-slate-300">
												{{ broadcast.timezone }}
											</span>
										</div>
									</div>
									<div class="flex items-center gap-1 flex-shrink-0">
										<button
											@click="openEditModal(broadcast)"
											class="p-1.5 text-slate-400 hover:text-blue-500 dark:hover:text-blue-400 transition-colors rounded hover:bg-slate-200 dark:hover:bg-slate-600"
											title="Edit"
										>
											<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
												<path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
											</svg>
										</button>
										<button
											@click="cancelBroadcast(broadcast.id)"
											class="p-1.5 text-slate-400 hover:text-red-500 dark:hover:text-red-400 transition-colors rounded hover:bg-slate-200 dark:hover:bg-slate-600"
											title="Cancel"
										>
											<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
												<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
											</svg>
										</button>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- Footer -->
				<div v-if="activeTab === 'compose'" class="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 rounded-b-xl">
					<button
						@click="$emit('close')"
						class="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
					>
						Cancel
					</button>
					<button
						@click="handleSend"
						:disabled="!isValid || isSending"
						class="px-4 py-2 text-sm font-medium text-white bg-violet-600 hover:bg-violet-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
					>
						<svg v-if="isSending" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						{{ isSending ? 'Sending...' : scheduleMode === 'schedule' ? 'Schedule Notification' : 'Send Notification' }}
					</button>
				</div>
			</div>
		</div>

		<!-- Edit Modal -->
		<Transition
			enter-active-class="transition ease-out duration-200"
			enter-from-class="opacity-0"
			enter-to-class="opacity-100"
			leave-active-class="transition ease-in duration-150"
			leave-from-class="opacity-100"
			leave-to-class="opacity-0"
		>
			<div v-if="editingBroadcast" class="fixed inset-0 z-[60] flex items-center justify-center p-4">
				<div class="fixed inset-0 bg-black/50" @click="closeEditModal"></div>
				<div class="relative w-full max-w-md bg-white dark:bg-slate-800 rounded-xl shadow-xl">
					<div class="p-6">
						<div class="flex items-center justify-between mb-4">
							<h3 class="text-lg font-semibold text-slate-900 dark:text-white">Edit Scheduled Broadcast</h3>
							<button @click="closeEditModal" class="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
								<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
									<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
								</svg>
							</button>
						</div>

						<div class="space-y-4">
							<!-- Title -->
							<div>
								<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Title</label>
								<input
									v-model="editForm.title"
									type="text"
									class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-violet-500 focus:border-transparent"
								/>
							</div>

							<!-- Message -->
							<div>
								<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Message</label>
								<textarea
									v-model="editForm.message"
									rows="3"
									class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-violet-500 focus:border-transparent resize-none"
								></textarea>
							</div>

							<!-- Type & Priority -->
							<div class="grid grid-cols-2 gap-3">
								<div>
									<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Type</label>
									<select
										v-model="editForm.type"
										class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-violet-500 focus:border-transparent"
									>
										<option value="scheduled_maintenance">Maintenance</option>
										<option value="system_status">System Status</option>
										<option value="security_alert">Security Alert</option>
										<option value="isp_issue">ISP Issue</option>
										<option value="device_offline">Device Offline</option>
										<option value="device_online">Device Online</option>
										<option value="device_degraded">Device Degraded</option>
										<option value="anomaly_detected">Anomaly</option>
										<option value="high_latency">High Latency</option>
										<option value="packet_loss">Packet Loss</option>
									</select>
								</div>
								<div>
									<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Priority</label>
									<select
										v-model="editForm.priority"
										class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-violet-500 focus:border-transparent"
									>
										<option value="low">Low</option>
										<option value="medium">Medium</option>
										<option value="high">High</option>
										<option value="critical">Critical</option>
									</select>
								</div>
							</div>

							<!-- Scheduled Time -->
							<div>
								<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Scheduled Time</label>
								<input
									v-model="editForm.scheduledAt"
									type="datetime-local"
									:min="minScheduleDateTime"
									class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-violet-500 focus:border-transparent"
								/>
								<p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
									Time is in your local timezone ({{ detectedTimezone }})
								</p>
							</div>

							<!-- Edit Error -->
							<div v-if="editError" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg">
								<p class="text-sm text-red-700 dark:text-red-400">{{ editError }}</p>
							</div>

							<!-- Actions -->
							<div class="flex justify-end gap-3 pt-2">
								<button
									@click="closeEditModal"
									class="px-4 py-2 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
								>
									Cancel
								</button>
								<button
									@click="saveEdit"
									:disabled="savingEdit || !editForm.title.trim() || !editForm.message.trim() || !editForm.scheduledAt"
									class="px-4 py-2 bg-violet-600 text-white rounded-lg hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
								>
									<svg v-if="savingEdit" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
										<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
										<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
									</svg>
									{{ savingEdit ? 'Saving...' : 'Save Changes' }}
								</button>
							</div>
						</div>
					</div>
				</div>
			</div>
		</Transition>
	</Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

interface ScheduledBroadcast {
	id: string;
	title: string;
	message: string;
	event_type: string;
	priority: string;
	network_id: number;
	scheduled_at: string;
	timezone?: string;
	status: string;
}

const props = defineProps<{
	networkId: number;
}>();

const emit = defineEmits<{
	close: [];
	sent: [];
}>();

// Tab state
const activeTab = ref<'compose' | 'scheduled'>('compose');

// Compose form
const form = ref({
	type: 'scheduled_maintenance',
	priority: 'medium',
	title: '',
	message: '',
});

const scheduleMode = ref<'now' | 'schedule'>('now');
const scheduledDateTime = ref('');
const error = ref<string | null>(null);
const successMessage = ref<string | null>(null);
const isSending = ref(false);

// Scheduled broadcasts
const scheduledBroadcasts = ref<ScheduledBroadcast[]>([]);
const loadingScheduled = ref(false);

// Edit modal
const editingBroadcast = ref<ScheduledBroadcast | null>(null);
const editForm = ref({
	title: '',
	message: '',
	type: 'scheduled_maintenance',
	priority: 'medium',
	scheduledAt: '',
});
const savingEdit = ref(false);
const editError = ref<string | null>(null);

// Detected timezone
const detectedTimezone = computed(() => {
	try {
		return Intl.DateTimeFormat().resolvedOptions().timeZone;
	} catch {
		return 'UTC';
	}
});

// Minimum schedule datetime (5 minutes from now)
const minScheduleDateTime = computed(() => {
	const now = new Date();
	now.setMinutes(now.getMinutes() + 5);
	return now.toISOString().slice(0, 16);
});

const isValid = computed(() => {
	if (scheduleMode.value === 'schedule' && !scheduledDateTime.value) {
		return false;
	}
	return form.value.title.trim().length > 0 && form.value.message.trim().length > 0;
});

// Load scheduled broadcasts
async function loadScheduledBroadcasts() {
	loadingScheduled.value = true;
	try {
		const response = await axios.get(`/api/notifications/scheduled`, {
			params: { include_completed: false }
		});
		scheduledBroadcasts.value = response.data.broadcasts.filter(
			(b: ScheduledBroadcast) => b.network_id === props.networkId
		);
	} catch (e) {
		console.error('Failed to load scheduled broadcasts:', e);
	} finally {
		loadingScheduled.value = false;
	}
}

// Send or schedule notification
async function handleSend() {
	if (!isValid.value) return;
	
	error.value = null;
	successMessage.value = null;
	isSending.value = true;
	
	try {
		if (scheduleMode.value === 'schedule' && scheduledDateTime.value) {
			// Schedule for later
			const date = new Date(scheduledDateTime.value);
			await axios.post(`/api/notifications/scheduled`, {
				network_id: props.networkId,
				title: form.value.title,
				message: form.value.message,
				event_type: form.value.type,
				priority: form.value.priority,
				scheduled_at: date.toISOString(),
				timezone: detectedTimezone.value,
			});
			
			successMessage.value = `Notification scheduled for ${date.toLocaleString()}`;
			
			// Reset form
			form.value = { type: 'scheduled_maintenance', priority: 'medium', title: '', message: '' };
			scheduledDateTime.value = '';
			scheduleMode.value = 'now';
			
			// Refresh scheduled list
			await loadScheduledBroadcasts();
			
			setTimeout(() => { successMessage.value = null; }, 5000);
		} else {
			// Send immediately
			const payload = {
				type: form.value.type,
				priority: form.value.priority,
				title: form.value.title,
				message: form.value.message,
			};
			
			await axios.post(`/api/notifications/networks/${props.networkId}/send`, payload);
			
			emit('sent');
			emit('close');
		}
	} catch (e: any) {
		error.value = e.response?.data?.detail || e.message || 'Failed to send notification';
		setTimeout(() => { error.value = null; }, 5000);
	} finally {
		isSending.value = false;
	}
}

// Cancel a scheduled broadcast
async function cancelBroadcast(broadcastId: string) {
	try {
		await axios.post(`/api/notifications/scheduled/${broadcastId}/cancel`);
		await loadScheduledBroadcasts();
	} catch (e: any) {
		console.error('Failed to cancel broadcast:', e);
	}
}

// Open edit modal
function openEditModal(broadcast: ScheduledBroadcast) {
	editingBroadcast.value = broadcast;
	editForm.value.title = broadcast.title;
	editForm.value.message = broadcast.message;
	editForm.value.type = broadcast.event_type;
	editForm.value.priority = broadcast.priority;
	
	// Convert UTC to local datetime-local format
	const date = new Date(broadcast.scheduled_at);
	editForm.value.scheduledAt = new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
	
	editError.value = null;
}

// Close edit modal
function closeEditModal() {
	editingBroadcast.value = null;
	editError.value = null;
}

// Save edited broadcast
async function saveEdit() {
	if (!editingBroadcast.value) return;
	
	savingEdit.value = true;
	editError.value = null;
	
	try {
		const update: Record<string, any> = {};
		
		if (editForm.value.title !== editingBroadcast.value.title) {
			update.title = editForm.value.title;
		}
		if (editForm.value.message !== editingBroadcast.value.message) {
			update.message = editForm.value.message;
		}
		if (editForm.value.type !== editingBroadcast.value.event_type) {
			update.event_type = editForm.value.type;
		}
		if (editForm.value.priority !== editingBroadcast.value.priority) {
			update.priority = editForm.value.priority;
		}
		
		// Check if scheduled time changed
		const newDate = new Date(editForm.value.scheduledAt);
		const originalDate = new Date(editingBroadcast.value.scheduled_at);
		if (newDate.getTime() !== originalDate.getTime()) {
			update.scheduled_at = newDate.toISOString();
			update.timezone = detectedTimezone.value;
		}
		
		await axios.patch(`/api/notifications/scheduled/${editingBroadcast.value.id}`, update);
		
		await loadScheduledBroadcasts();
		closeEditModal();
	} catch (e: any) {
		editError.value = e.response?.data?.detail || e.message || 'Failed to update broadcast';
	} finally {
		savingEdit.value = false;
	}
}

// Format scheduled time for display
function formatScheduledTime(isoString: string): string {
	const date = new Date(isoString);
	return date.toLocaleString();
}

// Get notification type icon
function getTypeIcon(type: string): string {
	const icons: Record<string, string> = {
		scheduled_maintenance: '🔧',
		system_status: '📊',
		security_alert: '🔒',
		isp_issue: '🌐',
		device_offline: '🔴',
		device_online: '🟢',
		device_degraded: '🟡',
		anomaly_detected: '⚠️',
		high_latency: '🐢',
		packet_loss: '📉',
	};
	return icons[type] || '📢';
}

// Get priority CSS class
function getPriorityClass(priority: string): string {
	const classes: Record<string, string> = {
		low: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400',
		medium: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400',
		high: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400',
		critical: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
	};
	return classes[priority] || classes.medium;
}

// Load scheduled broadcasts on mount
onMounted(() => {
	loadScheduledBroadcasts();
});
</script>
