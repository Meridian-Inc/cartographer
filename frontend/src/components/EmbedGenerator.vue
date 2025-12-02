<template>
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="$emit('close')">
		<div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-2xl mx-4 overflow-hidden max-h-[90vh] flex flex-col">
			<!-- Header -->
			<div class="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-indigo-500 to-purple-600">
				<div class="flex items-center gap-3">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
					</svg>
					<h2 class="text-lg font-semibold text-white">Manage Embeds</h2>
				</div>
				<button 
					@click="$emit('close')" 
					class="p-1 rounded hover:bg-white/20 text-white/80 hover:text-white transition-colors"
				>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>

			<!-- Content -->
			<div class="p-6 overflow-auto flex-1">
				<!-- Loading state -->
				<div v-if="loading" class="flex items-center justify-center py-8">
					<svg class="animate-spin h-8 w-8 text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
						<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
					</svg>
				</div>

				<template v-else>
					<!-- Create New Embed Section -->
					<div v-if="!selectedEmbed" class="mb-6">
						<button 
							@click="showCreateForm = !showCreateForm"
							class="w-full px-4 py-3 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-500 transition-colors flex items-center justify-center gap-2"
						>
							<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
							</svg>
							Create New Embed
						</button>

						<!-- Create Form -->
						<div v-if="showCreateForm" class="mt-4 p-4 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700">
							<div class="mb-4">
								<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Embed Name</label>
								<input 
									v-model="newEmbedName"
									type="text"
									placeholder="e.g., Public Dashboard, Client View..."
									class="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
								/>
							</div>

							<!-- Sensitive Mode -->
							<div class="flex items-center justify-between mb-4">
								<div class="flex items-center gap-2">
									<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
									</svg>
									<span class="text-sm text-slate-700 dark:text-slate-300">Sensitive Mode</span>
									<span class="text-xs text-slate-500">(Hide IPs)</span>
								</div>
								<button 
									@click="newEmbedSensitive = !newEmbedSensitive"
									class="relative w-10 h-6 rounded-full transition-colors"
									:class="newEmbedSensitive ? 'bg-amber-500' : 'bg-slate-300 dark:bg-slate-600'"
								>
									<span class="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform" :class="newEmbedSensitive ? 'translate-x-4' : ''"></span>
								</button>
							</div>

							<!-- Show Owner -->
							<div class="flex items-center justify-between mb-4">
								<div class="flex items-center gap-2">
									<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
									</svg>
									<span class="text-sm text-slate-700 dark:text-slate-300">Show Owner</span>
								</div>
								<button 
									@click="newEmbedShowOwner = !newEmbedShowOwner"
									class="relative w-10 h-6 rounded-full transition-colors"
									:class="newEmbedShowOwner ? 'bg-indigo-500' : 'bg-slate-300 dark:bg-slate-600'"
								>
									<span class="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform" :class="newEmbedShowOwner ? 'translate-x-4' : ''"></span>
								</button>
							</div>

							<!-- Owner Display Type -->
							<div v-if="newEmbedShowOwner" class="mb-4 pl-6">
								<label class="flex items-center gap-2 cursor-pointer mb-1">
									<input type="radio" v-model="newEmbedOwnerType" value="fullName" class="text-indigo-600" />
									<span class="text-sm text-slate-600 dark:text-slate-400">Full Name ({{ currentUser?.first_name }} {{ currentUser?.last_name }})</span>
								</label>
								<label class="flex items-center gap-2 cursor-pointer">
									<input type="radio" v-model="newEmbedOwnerType" value="username" class="text-indigo-600" />
									<span class="text-sm text-slate-600 dark:text-slate-400">Username ({{ currentUser?.username }})</span>
								</label>
							</div>

							<div class="flex justify-end gap-2">
								<button 
									@click="showCreateForm = false"
									class="px-3 py-1.5 text-sm text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200"
								>
									Cancel
								</button>
								<button 
									@click="createEmbed"
									:disabled="creating || !newEmbedName.trim()"
									class="px-4 py-1.5 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-500 disabled:opacity-50 flex items-center gap-1"
								>
									<svg v-if="creating" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
										<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
										<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
									</svg>
									Create
								</button>
							</div>
						</div>
					</div>

					<!-- Existing Embeds List -->
					<div v-if="!selectedEmbed">
						<h3 class="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">Your Embeds</h3>
						
						<div v-if="embeds.length === 0" class="text-center py-8 text-slate-500 dark:text-slate-400">
							<svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-2 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
							</svg>
							<p class="text-sm">No embeds created yet</p>
							<p class="text-xs mt-1">Click "Create New Embed" to get started</p>
						</div>

						<div v-else class="space-y-2">
							<div 
								v-for="embed in embeds" 
								:key="embed.id"
								class="p-3 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-indigo-300 dark:hover:border-indigo-600 cursor-pointer transition-colors bg-white dark:bg-slate-800/50"
								@click="selectEmbed(embed)"
							>
								<div class="flex items-center justify-between">
									<div>
										<div class="font-medium text-slate-800 dark:text-slate-200">{{ embed.name }}</div>
										<div class="text-xs text-slate-500 dark:text-slate-400 mt-0.5 flex items-center gap-2">
											<span v-if="embed.sensitiveMode" class="inline-flex items-center gap-1 text-amber-600 dark:text-amber-400">
												<svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
												Sensitive
											</span>
											<span v-if="embed.showOwner" class="inline-flex items-center gap-1">
												<svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
												{{ embed.ownerDisplayName }}
											</span>
											<span>Created {{ formatDate(embed.createdAt) }}</span>
										</div>
									</div>
									<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
									</svg>
								</div>
							</div>
						</div>
					</div>

					<!-- Selected Embed Details -->
					<div v-else>
						<button 
							@click="selectedEmbed = null"
							class="flex items-center gap-1 text-sm text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 mb-4"
						>
							<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
							</svg>
							Back to list
						</button>

						<div class="mb-4">
							<h3 class="text-lg font-medium text-slate-800 dark:text-slate-200">{{ selectedEmbed.name }}</h3>
							<div class="text-xs text-slate-500 dark:text-slate-400 mt-1">
								Created {{ formatDate(selectedEmbed.createdAt) }}
								<span v-if="selectedEmbed.updatedAt !== selectedEmbed.createdAt"> • Updated {{ formatDate(selectedEmbed.updatedAt) }}</span>
							</div>
						</div>

						<!-- Embed URL -->
						<div class="mb-4">
							<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Embed URL</label>
							<div class="flex gap-2">
								<input 
									type="text" 
									:value="getEmbedUrl(selectedEmbed.id)" 
									readonly
									class="flex-1 px-3 py-2 text-sm bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-800 dark:text-slate-200 font-mono text-xs"
								/>
								<button 
									@click="copyUrl(selectedEmbed.id)"
									class="px-3 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-500 transition-colors"
								>
									{{ copiedId === selectedEmbed.id ? '✓' : 'Copy' }}
								</button>
							</div>
						</div>

						<!-- iframe Code -->
						<div class="mb-4">
							<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">iframe Code</label>
							<div class="relative">
								<textarea 
									:value="getIframeCode(selectedEmbed.id)" 
									readonly
									rows="2"
									class="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-emerald-400 font-mono resize-none"
								></textarea>
								<button 
									@click="copyIframe(selectedEmbed.id)"
									class="absolute top-1.5 right-1.5 px-2 py-0.5 bg-slate-700 text-slate-300 text-xs rounded hover:bg-slate-600"
								>
									{{ copiedIframeId === selectedEmbed.id ? '✓' : 'Copy' }}
								</button>
							</div>
						</div>

						<!-- Settings -->
						<div class="mb-4 p-3 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700">
							<div class="text-xs font-medium text-slate-600 dark:text-slate-400 uppercase tracking-wide mb-2">Settings</div>
							<div class="space-y-2 text-sm">
								<div class="flex items-center justify-between">
									<span class="text-slate-600 dark:text-slate-400">Sensitive Mode</span>
									<span :class="selectedEmbed.sensitiveMode ? 'text-amber-600' : 'text-slate-500'">
										{{ selectedEmbed.sensitiveMode ? 'Enabled' : 'Disabled' }}
									</span>
								</div>
								<div class="flex items-center justify-between">
									<span class="text-slate-600 dark:text-slate-400">Show Owner</span>
									<span :class="selectedEmbed.showOwner ? 'text-indigo-600' : 'text-slate-500'">
										{{ selectedEmbed.showOwner ? selectedEmbed.ownerDisplayName : 'Disabled' }}
									</span>
								</div>
							</div>
						</div>

						<!-- Actions -->
						<div class="flex items-center justify-between">
							<button 
								@click="confirmDelete = true"
								class="px-3 py-1.5 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
							>
								Delete Embed
							</button>
							<a 
								:href="getEmbedUrl(selectedEmbed.id)"
								target="_blank"
								rel="noopener noreferrer"
								class="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-500 transition-colors flex items-center gap-2"
							>
								<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
								</svg>
								Open Preview
							</a>
						</div>

						<!-- Delete Confirmation -->
						<div v-if="confirmDelete" class="mt-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
							<p class="text-sm text-red-800 dark:text-red-200 mb-3">Are you sure you want to delete this embed? This action cannot be undone.</p>
							<div class="flex justify-end gap-2">
								<button 
									@click="confirmDelete = false"
									class="px-3 py-1.5 text-sm text-slate-600 dark:text-slate-400"
								>
									Cancel
								</button>
								<button 
									@click="deleteEmbed"
									:disabled="deleting"
									class="px-3 py-1.5 bg-red-600 text-white text-sm rounded-lg hover:bg-red-500 disabled:opacity-50"
								>
									{{ deleting ? 'Deleting...' : 'Delete' }}
								</button>
							</div>
						</div>
					</div>
				</template>
			</div>
		</div>
	</div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { useAuth } from '../composables/useAuth';

interface EmbedConfig {
	id: string;
	name: string;
	sensitiveMode: boolean;
	showOwner: boolean;
	ownerDisplayName: string | null;
	createdAt: string;
	updatedAt: string;
}

const emit = defineEmits<{
	(e: 'close'): void;
}>();

const { user } = useAuth();
const currentUser = computed(() => user.value);

const loading = ref(true);
const creating = ref(false);
const deleting = ref(false);
const embeds = ref<EmbedConfig[]>([]);
const selectedEmbed = ref<EmbedConfig | null>(null);
const showCreateForm = ref(false);
const confirmDelete = ref(false);

// New embed form
const newEmbedName = ref('');
const newEmbedSensitive = ref(false);
const newEmbedShowOwner = ref(false);
const newEmbedOwnerType = ref<'fullName' | 'username'>('fullName');

// Copy states
const copiedId = ref<string | null>(null);
const copiedIframeId = ref<string | null>(null);

function getEmbedUrl(embedId: string): string {
	return `${window.location.origin}/embed/${embedId}`;
}

function getIframeCode(embedId: string): string {
	return `<iframe src="${getEmbedUrl(embedId)}" width="100%" height="600" frameborder="0" style="border-radius: 8px;"></iframe>`;
}

function getOwnerDisplayName(): string {
	if (!currentUser.value) return '';
	if (newEmbedOwnerType.value === 'username') {
		return currentUser.value.username;
	}
	return `${currentUser.value.first_name} ${currentUser.value.last_name}`.trim();
}

function formatDate(isoString: string): string {
	if (!isoString) return '';
	const date = new Date(isoString);
	const now = new Date();
	const diffMs = now.getTime() - date.getTime();
	const diffDays = Math.floor(diffMs / 86400000);
	
	if (diffDays === 0) return 'today';
	if (diffDays === 1) return 'yesterday';
	if (diffDays < 7) return `${diffDays} days ago`;
	
	return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

async function loadEmbeds() {
	loading.value = true;
	try {
		const response = await axios.get('/api/embeds');
		embeds.value = response.data.embeds || [];
	} catch (err) {
		console.error('Failed to load embeds:', err);
	} finally {
		loading.value = false;
	}
}

async function createEmbed() {
	if (!newEmbedName.value.trim()) return;
	
	creating.value = true;
	try {
		const response = await axios.post('/api/embeds', {
			name: newEmbedName.value.trim(),
			sensitiveMode: newEmbedSensitive.value,
			showOwner: newEmbedShowOwner.value,
			ownerDisplayType: newEmbedOwnerType.value,
			ownerDisplayName: newEmbedShowOwner.value ? getOwnerDisplayName() : null
		});
		
		// Add new embed to list and select it
		const newEmbed: EmbedConfig = {
			id: response.data.id,
			...response.data.embed
		};
		embeds.value.unshift(newEmbed);
		selectedEmbed.value = newEmbed;
		
		// Reset form
		showCreateForm.value = false;
		newEmbedName.value = '';
		newEmbedSensitive.value = false;
		newEmbedShowOwner.value = false;
		newEmbedOwnerType.value = 'fullName';
	} catch (err) {
		console.error('Failed to create embed:', err);
	} finally {
		creating.value = false;
	}
}

function selectEmbed(embed: EmbedConfig) {
	selectedEmbed.value = embed;
	confirmDelete.value = false;
}

async function deleteEmbed() {
	if (!selectedEmbed.value) return;
	
	deleting.value = true;
	try {
		await axios.delete(`/api/embeds/${selectedEmbed.value.id}`);
		embeds.value = embeds.value.filter(e => e.id !== selectedEmbed.value!.id);
		selectedEmbed.value = null;
		confirmDelete.value = false;
	} catch (err) {
		console.error('Failed to delete embed:', err);
	} finally {
		deleting.value = false;
	}
}

function copyUrl(embedId: string) {
	navigator.clipboard.writeText(getEmbedUrl(embedId));
	copiedId.value = embedId;
	setTimeout(() => { copiedId.value = null; }, 2000);
}

function copyIframe(embedId: string) {
	navigator.clipboard.writeText(getIframeCode(embedId));
	copiedIframeId.value = embedId;
	setTimeout(() => { copiedIframeId.value = null; }, 2000);
}

onMounted(() => {
	loadEmbeds();
});
</script>
