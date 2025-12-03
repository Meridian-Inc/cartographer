<template>
	<div class="flex flex-col h-full bg-white dark:bg-slate-800 border-l border-slate-200 dark:border-slate-700 overflow-hidden">
		<!-- Header -->
		<div class="flex flex-col border-b border-slate-200 dark:border-slate-700">
			<!-- Title row -->
			<div class="flex items-center justify-between px-4 py-3 bg-slate-50 dark:bg-slate-900">
				<div class="flex items-center gap-3">
					<div class="p-1.5 bg-gradient-to-br from-violet-500 to-fuchsia-500 rounded-lg shadow-sm">
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z" />
						</svg>
					</div>
					<div>
						<h2 class="font-semibold text-slate-800 dark:text-slate-100">Network Assistant</h2>
					</div>
				</div>
				<!-- Close button -->
				<button 
					@click="$emit('close')"
					class="p-1 rounded hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 transition-colors"
					title="Close assistant"
				>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>
			<!-- Model selection row -->
			<div class="flex items-center gap-2 px-4 py-2 bg-slate-100/50 dark:bg-slate-800/50">
				<!-- Provider selector -->
				<select 
					v-model="selectedProvider" 
					@change="onProviderChange"
					class="text-xs bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md px-2 py-1.5 text-slate-700 dark:text-slate-200 focus:border-violet-500 focus:ring-1 focus:ring-violet-500 outline-none"
					:disabled="isStreaming"
				>
					<option v-for="p in availableProviders" :key="p.provider" :value="p.provider">
						{{ providerLabels[p.provider] || p.provider }}
					</option>
				</select>
				<!-- Model selector -->
				<select 
					v-model="selectedModel" 
					class="text-xs bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md px-2 py-1.5 text-slate-700 dark:text-slate-200 focus:border-violet-500 focus:ring-1 focus:ring-violet-500 outline-none flex-1 min-w-0"
					:disabled="isStreaming || !currentProviderModels.length"
					:title="selectedModel"
				>
					<option v-for="model in currentProviderModels" :key="model" :value="model">
						{{ formatModelName(model) }}
					</option>
				</select>
			</div>
		</div>

		<!-- Messages Area -->
		<div 
			ref="messagesContainer"
			class="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50 dark:bg-slate-900"
		>
			<!-- Welcome message -->
			<div v-if="messages.length === 0" class="text-center py-8">
				<div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-500 shadow-lg mb-4">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z" />
					</svg>
				</div>
				<h3 class="text-lg font-medium text-slate-800 dark:text-slate-100 mb-2">Hi! I'm your Network Assistant</h3>
				<p class="text-slate-500 dark:text-slate-400 text-sm max-w-md mx-auto mb-6">
					I can help you understand your network topology, troubleshoot issues, and answer questions about device health and connectivity.
				</p>
				<div class="flex flex-wrap justify-center gap-2">
					<button 
						v-for="suggestion in suggestions" 
						:key="suggestion"
						@click="sendMessage(suggestion)"
						class="px-3 py-1.5 text-xs bg-white dark:bg-slate-800 hover:bg-violet-50 dark:hover:bg-violet-900/30 border border-slate-200 dark:border-slate-600 hover:border-violet-400 dark:hover:border-violet-500 rounded-full text-slate-600 dark:text-slate-300 hover:text-violet-700 dark:hover:text-violet-300 transition-colors"
					>
						{{ suggestion }}
					</button>
				</div>
			</div>

			<!-- Message list -->
			<template v-for="(msg, idx) in messages" :key="idx">
				<!-- User message -->
				<div v-if="msg.role === 'user'" class="flex justify-end">
					<div class="max-w-[80%] bg-gradient-to-r from-violet-600 to-fuchsia-600 rounded-2xl rounded-tr-sm px-4 py-2.5 text-white text-sm shadow-sm">
						<div class="prose prose-sm prose-invert prose-user max-w-none" v-html="formatMessage(msg.content)"></div>
					</div>
				</div>

				<!-- Assistant message -->
				<div v-else class="flex gap-3">
					<div class="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center shadow-sm">
						<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
						</svg>
					</div>
					<div class="max-w-[85%] bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl rounded-tl-sm px-4 py-2.5 text-slate-700 dark:text-slate-200 text-sm shadow-sm">
						<div class="prose prose-sm dark:prose-invert max-w-none" v-html="formatMessage(msg.content)"></div>
					</div>
				</div>
			</template>

			<!-- Streaming indicator -->
			<div v-if="isStreaming && !currentStreamContent" class="flex gap-3">
				<div class="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center shadow-sm">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
					</svg>
				</div>
				<div class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
					<div class="flex gap-1">
						<span class="w-2 h-2 bg-violet-500 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
						<span class="w-2 h-2 bg-violet-500 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
						<span class="w-2 h-2 bg-violet-500 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
					</div>
				</div>
			</div>

			<!-- Streaming content -->
			<div v-if="isStreaming && currentStreamContent" class="flex gap-3">
				<div class="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center shadow-sm">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
					</svg>
				</div>
				<div class="max-w-[85%] bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl rounded-tl-sm px-4 py-2.5 text-slate-700 dark:text-slate-200 text-sm shadow-sm">
					<div class="prose prose-sm dark:prose-invert max-w-none" v-html="formatMessage(currentStreamContent)"></div>
					<span class="inline-block w-2 h-4 bg-violet-500 animate-pulse ml-0.5"></span>
				</div>
			</div>

			<!-- Error message -->
			<div v-if="error" class="flex gap-3">
				<div class="flex-shrink-0 w-8 h-8 rounded-lg bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-red-500 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
					</svg>
				</div>
				<div class="max-w-[85%] bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl rounded-tl-sm px-4 py-2.5 text-red-700 dark:text-red-300 text-sm">
					{{ error }}
				</div>
			</div>
		</div>

		<!-- Context indicator -->
		<div class="px-4 py-2 bg-slate-100 dark:bg-slate-800/50 border-t border-slate-200 dark:border-slate-700 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
			<!-- Loading state -->
			<template v-if="contextLoading">
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-amber-500 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
				</svg>
				<span class="text-amber-600 dark:text-amber-400">Loading network context...</span>
			</template>
			<!-- Ready state -->
			<template v-else-if="contextSummary && contextSummary.total_nodes > 0">
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
				</svg>
				<span>Network context: {{ contextSummary.total_nodes }} devices ({{ contextSummary.healthy_nodes }} healthy)</span>
			</template>
			<!-- Unavailable state -->
			<template v-else>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-slate-400 dark:text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
				</svg>
				<span class="text-slate-400 dark:text-slate-500">Network context unavailable</span>
			</template>
			<!-- Refresh button -->
			<button 
				@click="refreshContext"
				class="ml-auto p-1 rounded hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
				:class="contextRefreshing ? 'text-amber-500' : 'text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:hover:text-white'"
				:disabled="contextLoading || contextRefreshing"
				title="Refresh network context"
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" :class="{ 'animate-spin': contextRefreshing }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
				</svg>
			</button>
			<!-- Context toggle -->
			<button 
				@click="includeContext = !includeContext"
				class="text-xs px-2 py-0.5 rounded-md font-medium transition-colors"
				:class="includeContext 
					? 'text-emerald-700 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-400/10' 
					: 'text-slate-500 bg-slate-200 dark:bg-slate-700'"
				:disabled="contextLoading"
			>
				{{ includeContext ? 'Context ON' : 'Context OFF' }}
			</button>
		</div>

		<!-- Input Area -->
		<div class="p-3 border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
			<form @submit.prevent="handleSubmit" class="flex gap-2">
				<input
					v-model="inputMessage"
					type="text"
					placeholder="Ask about your network..."
					class="flex-1 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg px-4 py-2 text-slate-800 dark:text-white placeholder-slate-400 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20 outline-none text-sm"
					:disabled="isStreaming"
					@keydown.enter.exact.prevent="handleSubmit"
				/>
				<button
					type="submit"
					:disabled="!inputMessage.trim() || isStreaming"
					class="px-4 py-2 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 disabled:from-slate-400 disabled:to-slate-400 dark:disabled:from-slate-600 dark:disabled:to-slate-600 disabled:cursor-not-allowed rounded-lg text-white font-medium transition-all shadow-sm"
				>
					<svg v-if="!isStreaming" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
					</svg>
					<svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
					</svg>
				</button>
			</form>
		</div>
	</div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import axios from 'axios';
import { marked } from 'marked';

const emit = defineEmits(['close']);

interface ChatMessage {
	role: 'user' | 'assistant';
	content: string;
}

interface Provider {
	provider: string;
	available: boolean;
	default_model?: string;
	available_models?: string[];
}

interface ContextSummary {
	total_nodes: number;
	healthy_nodes: number;
	unhealthy_nodes: number;
	gateway_count: number;
	loading?: boolean;
	unavailable?: boolean;
}

interface ContextStatus {
	snapshot_available: boolean;
	loading: boolean;
	ready: boolean;
}

const messages = ref<ChatMessage[]>([]);
const inputMessage = ref('');
const isStreaming = ref(false);
const currentStreamContent = ref('');
const error = ref<string | null>(null);
const messagesContainer = ref<HTMLElement | null>(null);

const selectedProvider = ref('openai');
const selectedModel = ref('');
const availableProviders = ref<Provider[]>([]);
const includeContext = ref(true);
const contextSummary = ref<ContextSummary | null>(null);
const contextLoading = ref(true);
const contextRefreshing = ref(false);
const contextStatusPollInterval = ref<number | null>(null);

// Computed property for current provider's models
const currentProviderModels = computed(() => {
	const provider = availableProviders.value.find(p => p.provider === selectedProvider.value);
	return provider?.available_models || [];
});

const providerLabels: Record<string, string> = {
	openai: 'OpenAI',
	anthropic: 'Claude',
	gemini: 'Gemini',
	ollama: 'Ollama',
};

// Helper to get auth token from storage
function getAuthToken(): string | null {
	try {
		const stored = localStorage.getItem('cartographer_auth');
		if (stored) {
			const state = JSON.parse(stored);
			if (state.token && state.expiresAt > Date.now()) {
				return state.token;
			}
		}
	} catch (e) {
		console.error('Failed to get auth token:', e);
	}
	return null;
}

const suggestions = [
	"What's the health of my network?",
	"Are there any unhealthy devices?",
	"Show me my gateways",
	"Explain my network topology",
];

// Fetch available providers on mount
onMounted(async () => {
	await fetchProviders();
	await fetchContext();
});

// Cleanup polling on unmount
onUnmounted(() => {
	stopContextStatusPolling();
});

async function fetchProviders() {
	try {
		const response = await axios.get('/api/assistant/config');
		const providers = response.data.providers || [];
		availableProviders.value = providers.filter((p: Provider) => p.available);
		
		// Set default provider to first available
		if (availableProviders.value.length > 0) {
			selectedProvider.value = availableProviders.value[0].provider;
			// Set default model for the provider
			const defaultProvider = availableProviders.value[0];
			selectedModel.value = defaultProvider.default_model || defaultProvider.available_models?.[0] || '';
		}
	} catch (err) {
		console.error('Failed to fetch providers:', err);
		// Default to OpenAI if we can't fetch
		availableProviders.value = [{ provider: 'openai', available: true, default_model: 'gpt-4o-mini' }];
		selectedModel.value = 'gpt-4o-mini';
	}
}

function onProviderChange() {
	// Update model to the new provider's default
	const provider = availableProviders.value.find(p => p.provider === selectedProvider.value);
	if (provider) {
		selectedModel.value = provider.default_model || provider.available_models?.[0] || '';
	}
}

function formatModelName(model: string): string {
	// Shorten long model names for display
	if (model.length <= 25) return model;
	
	// Keep important parts visible
	const parts = model.split('-');
	if (parts.length >= 3) {
		// e.g., "claude-3-5-sonnet-20241022" -> "claude-3-5-sonnet"
		// Check if last part is a date
		const lastPart = parts[parts.length - 1];
		if (/^\d{8}$/.test(lastPart)) {
			return parts.slice(0, -1).join('-');
		}
	}
	
	return model.slice(0, 22) + '...';
}

async function fetchContext() {
	try {
		const response = await axios.get('/api/assistant/context');
		contextSummary.value = response.data;
		
		// Check if context is actually available or loading
		if (response.data.loading || response.data.total_nodes === 0) {
			contextLoading.value = true;
			// Start polling for context status
			startContextStatusPolling();
		} else {
			contextLoading.value = false;
			stopContextStatusPolling();
		}
	} catch (err) {
		console.error('Failed to fetch context:', err);
		contextLoading.value = true;
		startContextStatusPolling();
	}
}

async function fetchContextStatus() {
	try {
		const response = await axios.get('/api/assistant/context/status');
		const status: ContextStatus = response.data;
		
		if (status.ready && status.snapshot_available) {
			contextLoading.value = false;
			stopContextStatusPolling();
			// Refresh the full context
			await fetchContext();
		}
	} catch (err) {
		console.error('Failed to fetch context status:', err);
	}
}

function startContextStatusPolling() {
	if (contextStatusPollInterval.value) return; // Already polling
	
	contextStatusPollInterval.value = window.setInterval(() => {
		fetchContextStatus();
	}, 5000); // Poll every 5 seconds
}

function stopContextStatusPolling() {
	if (contextStatusPollInterval.value) {
		clearInterval(contextStatusPollInterval.value);
		contextStatusPollInterval.value = null;
	}
}

async function refreshContext() {
	if (contextRefreshing.value) return;
	
	contextRefreshing.value = true;
	try {
		// Call the refresh endpoint
		await axios.post('/api/assistant/context/refresh');
		// Then fetch the updated context
		await fetchContext();
	} catch (err) {
		console.error('Failed to refresh context:', err);
	} finally {
		contextRefreshing.value = false;
	}
}

// Configure marked for chat messages
marked.setOptions({
	breaks: true,  // Convert \n to <br>
	gfm: true,     // GitHub Flavored Markdown
});

function formatMessage(content: string): string {
	// Use marked to parse markdown
	const html = marked.parse(content, { async: false }) as string;
	return html;
}

async function sendMessage(content: string) {
	inputMessage.value = content;
	await handleSubmit();
}

async function handleSubmit() {
	const message = inputMessage.value.trim();
	if (!message || isStreaming.value) return;

	// Clear input and error
	inputMessage.value = '';
	error.value = null;

	// Add user message
	messages.value.push({ role: 'user', content: message });
	scrollToBottom();

	// Start streaming
	isStreaming.value = true;
	currentStreamContent.value = '';

	try {
		// Build conversation history (exclude current message)
		const history = messages.value.slice(0, -1).map(m => ({
			role: m.role,
			content: m.content,
		}));

		const authToken = getAuthToken();
		if (!authToken) {
			throw new Error('Not authenticated. Please log in again.');
		}

		const response = await fetch('/api/assistant/chat/stream', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'Authorization': `Bearer ${authToken}`,
			},
			body: JSON.stringify({
				message,
				provider: selectedProvider.value,
				model: selectedModel.value || undefined,
				conversation_history: history,
				include_network_context: includeContext.value,
			}),
		});

		if (!response.ok) {
			const errData = await response.json().catch(() => ({}));
			throw new Error(errData.detail || `HTTP ${response.status}`);
		}

		const reader = response.body?.getReader();
		if (!reader) throw new Error('No response body');

		const decoder = new TextDecoder();
		let buffer = '';

		while (true) {
			const { done, value } = await reader.read();
			if (done) break;

			buffer += decoder.decode(value, { stream: true });
			const lines = buffer.split('\n');
			buffer = lines.pop() || '';

			for (const line of lines) {
				if (line.startsWith('data: ')) {
					try {
						const data = JSON.parse(line.slice(6));
						
						if (data.type === 'content') {
							currentStreamContent.value += data.content;
							scrollToBottom();
						} else if (data.type === 'context') {
							// Update context summary if provided
							if (data.summary) {
								contextSummary.value = data.summary;
							}
						} else if (data.type === 'error') {
							error.value = data.error;
						} else if (data.type === 'done') {
							// Streaming complete
						}
					} catch (e) {
						// Ignore JSON parse errors for incomplete chunks
					}
				}
			}
		}

		// Add assistant message
		if (currentStreamContent.value) {
			messages.value.push({ role: 'assistant', content: currentStreamContent.value });
		}

	} catch (err: any) {
		console.error('Chat error:', err);
		error.value = err.message || 'Failed to get response';
	} finally {
		isStreaming.value = false;
		currentStreamContent.value = '';
		scrollToBottom();
	}
}

function scrollToBottom() {
	nextTick(() => {
		if (messagesContainer.value) {
			messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
		}
	});
}

// Auto-scroll when messages change
watch(messages, scrollToBottom, { deep: true });
</script>

<style scoped>
/* Custom scrollbar - light mode */
.overflow-y-auto::-webkit-scrollbar {
	width: 6px;
}
.overflow-y-auto::-webkit-scrollbar-track {
	background: transparent;
}
.overflow-y-auto::-webkit-scrollbar-thumb {
	background: #cbd5e1;
	border-radius: 3px;
}
.overflow-y-auto::-webkit-scrollbar-thumb:hover {
	background: #94a3b8;
}

/* Custom scrollbar - dark mode */
:root.dark .overflow-y-auto::-webkit-scrollbar-thumb {
	background: #475569;
}
:root.dark .overflow-y-auto::-webkit-scrollbar-thumb:hover {
	background: #64748b;
}

/* Prose base styles for assistant messages */
.prose :deep(code) {
	color: #1e293b;
	background: #f1f5f9;
	padding: 0.125rem 0.25rem;
	border-radius: 0.25rem;
	font-size: 0.875em;
}
.prose :deep(pre) {
	background: #f1f5f9;
	padding: 0.75rem;
	border-radius: 0.375rem;
	overflow-x: auto;
	margin: 0.5rem 0;
}
.prose :deep(pre code) {
	background: transparent;
	padding: 0;
}
.prose :deep(p) {
	margin: 0.5rem 0;
}
.prose :deep(p:first-child) {
	margin-top: 0;
}
.prose :deep(p:last-child) {
	margin-bottom: 0;
}
.prose :deep(ul),
.prose :deep(ol) {
	margin: 0.5rem 0;
	padding-left: 1.5rem;
}
.prose :deep(li) {
	margin: 0.25rem 0;
}
.prose :deep(ul) {
	list-style-type: disc;
}
.prose :deep(ol) {
	list-style-type: decimal;
}
.prose :deep(a) {
	color: #7c3aed;
	text-decoration: underline;
}
.prose :deep(a:hover) {
	color: #6d28d9;
}
.prose :deep(blockquote) {
	border-left: 3px solid #8b5cf6;
	padding-left: 0.75rem;
	margin: 0.5rem 0;
	color: #475569;
}
.prose :deep(h1),
.prose :deep(h2),
.prose :deep(h3),
.prose :deep(h4) {
	font-weight: 600;
	margin: 0.75rem 0 0.5rem 0;
}
.prose :deep(h1) {
	font-size: 1.25rem;
}
.prose :deep(h2) {
	font-size: 1.125rem;
}
.prose :deep(h3) {
	font-size: 1rem;
}
.prose :deep(table) {
	width: 100%;
	border-collapse: collapse;
	margin: 0.5rem 0;
}
.prose :deep(th),
.prose :deep(td) {
	border: 1px solid #e2e8f0;
	padding: 0.375rem 0.5rem;
	text-align: left;
}
.prose :deep(th) {
	background: #f8fafc;
	font-weight: 600;
}
.prose :deep(hr) {
	border: none;
	border-top: 1px solid #e2e8f0;
	margin: 0.75rem 0;
}

/* Prose overrides for dark mode - assistant messages */
.prose.dark\:prose-invert :deep(code) {
	color: #e2e8f0;
	background: #0f172a;
}
.prose.dark\:prose-invert :deep(pre) {
	background: #0f172a;
}
.prose.dark\:prose-invert :deep(a) {
	color: #a78bfa;
}
.prose.dark\:prose-invert :deep(a:hover) {
	color: #c4b5fd;
}
.prose.dark\:prose-invert :deep(blockquote) {
	border-left-color: #8b5cf6;
	color: #cbd5e1;
}
.prose.dark\:prose-invert :deep(th),
.prose.dark\:prose-invert :deep(td) {
	border-color: #475569;
}
.prose.dark\:prose-invert :deep(th) {
	background: #1e293b;
}
.prose.dark\:prose-invert :deep(hr) {
	border-top-color: #475569;
}

/* User message prose - lighter code backgrounds for violet bubble */
.prose-user :deep(code) {
	background: rgba(0, 0, 0, 0.2);
}
.prose-user :deep(pre) {
	background: rgba(0, 0, 0, 0.25);
}
.prose-user :deep(a) {
	color: #e0e7ff;
}
.prose-user :deep(a:hover) {
	color: #ffffff;
}
.prose-user :deep(blockquote) {
	border-left-color: #c4b5fd;
	color: #e0e7ff;
}
</style>
