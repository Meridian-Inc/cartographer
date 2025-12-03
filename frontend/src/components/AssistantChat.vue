<template>
	<div class="flex flex-col h-full bg-slate-900 rounded-lg border border-slate-700 overflow-hidden">
		<!-- Header -->
		<div class="flex flex-col bg-gradient-to-r from-violet-900/50 to-fuchsia-900/50 border-b border-slate-700">
			<!-- Title row -->
			<div class="flex items-center justify-between px-4 py-2">
				<div class="flex items-center gap-3">
					<div class="p-2 bg-gradient-to-br from-violet-500 to-fuchsia-500 rounded-lg">
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
						</svg>
					</div>
					<div>
						<h2 class="font-semibold text-white text-sm">Network Assistant</h2>
					</div>
				</div>
				<!-- Close button -->
				<button 
					@click="$emit('close')"
					class="p-1.5 rounded hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
					title="Close assistant"
				>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>
			<!-- Model selection row -->
			<div class="flex items-center gap-2 px-4 pb-2">
				<!-- Provider selector -->
				<select 
					v-model="selectedProvider" 
					@change="onProviderChange"
					class="text-xs bg-slate-800 border border-slate-600 rounded px-2 py-1.5 text-slate-200 focus:border-violet-500 focus:ring-1 focus:ring-violet-500 outline-none"
					:disabled="isStreaming"
				>
					<option v-for="p in availableProviders" :key="p.provider" :value="p.provider">
						{{ providerLabels[p.provider] || p.provider }}
					</option>
				</select>
				<!-- Model selector -->
				<select 
					v-model="selectedModel" 
					class="text-xs bg-slate-800 border border-slate-600 rounded px-2 py-1.5 text-slate-200 focus:border-violet-500 focus:ring-1 focus:ring-violet-500 outline-none flex-1 min-w-0"
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
			class="flex-1 overflow-y-auto p-4 space-y-4"
		>
			<!-- Welcome message -->
			<div v-if="messages.length === 0" class="text-center py-8">
				<div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 mb-4">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
					</svg>
				</div>
				<h3 class="text-lg font-medium text-white mb-2">Hi! I'm your Network Assistant</h3>
				<p class="text-slate-400 text-sm max-w-md mx-auto mb-6">
					I can help you understand your network topology, troubleshoot issues, and answer questions about device health and connectivity.
				</p>
				<div class="flex flex-wrap justify-center gap-2">
					<button 
						v-for="suggestion in suggestions" 
						:key="suggestion"
						@click="sendMessage(suggestion)"
						class="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 border border-slate-600 hover:border-violet-500 rounded-full text-slate-300 hover:text-white transition-colors"
					>
						{{ suggestion }}
					</button>
				</div>
			</div>

			<!-- Message list -->
			<template v-for="(msg, idx) in messages" :key="idx">
				<!-- User message -->
				<div v-if="msg.role === 'user'" class="flex justify-end">
					<div class="max-w-[80%] bg-violet-600 rounded-2xl rounded-tr-sm px-4 py-2.5 text-white text-sm">
						{{ msg.content }}
					</div>
				</div>

				<!-- Assistant message -->
				<div v-else class="flex gap-3">
					<div class="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
						<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3" />
						</svg>
					</div>
					<div class="max-w-[85%] bg-slate-800 rounded-2xl rounded-tl-sm px-4 py-2.5 text-slate-200 text-sm">
						<div class="prose prose-sm prose-invert max-w-none" v-html="formatMessage(msg.content)"></div>
					</div>
				</div>
			</template>

			<!-- Streaming indicator -->
			<div v-if="isStreaming && !currentStreamContent" class="flex gap-3">
				<div class="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5" />
					</svg>
				</div>
				<div class="bg-slate-800 rounded-2xl rounded-tl-sm px-4 py-3">
					<div class="flex gap-1">
						<span class="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
						<span class="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
						<span class="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
					</div>
				</div>
			</div>

			<!-- Streaming content -->
			<div v-if="isStreaming && currentStreamContent" class="flex gap-3">
				<div class="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5" />
					</svg>
				</div>
				<div class="max-w-[85%] bg-slate-800 rounded-2xl rounded-tl-sm px-4 py-2.5 text-slate-200 text-sm">
					<div class="prose prose-sm prose-invert max-w-none" v-html="formatMessage(currentStreamContent)"></div>
					<span class="inline-block w-2 h-4 bg-violet-400 animate-pulse ml-0.5"></span>
				</div>
			</div>

			<!-- Error message -->
			<div v-if="error" class="flex gap-3">
				<div class="flex-shrink-0 w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
					</svg>
				</div>
				<div class="max-w-[85%] bg-red-900/30 border border-red-800 rounded-2xl rounded-tl-sm px-4 py-2.5 text-red-300 text-sm">
					{{ error }}
				</div>
			</div>
		</div>

		<!-- Context indicator -->
		<div v-if="contextSummary" class="px-4 py-2 bg-slate-800/50 border-t border-slate-700 flex items-center gap-2 text-xs text-slate-400">
			<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
			<span>Network context: {{ contextSummary.total_nodes }} devices ({{ contextSummary.healthy_nodes }} healthy)</span>
			<button 
				@click="includeContext = !includeContext"
				class="ml-auto text-xs"
				:class="includeContext ? 'text-emerald-400' : 'text-slate-500'"
			>
				{{ includeContext ? 'Context ON' : 'Context OFF' }}
			</button>
		</div>

		<!-- Input Area -->
		<div class="p-4 border-t border-slate-700 bg-slate-800/50">
			<form @submit.prevent="handleSubmit" class="flex gap-2">
				<input
					v-model="inputMessage"
					type="text"
					placeholder="Ask about your network..."
					class="flex-1 bg-slate-900 border border-slate-600 rounded-xl px-4 py-2.5 text-white placeholder-slate-400 focus:border-violet-500 focus:ring-1 focus:ring-violet-500 outline-none text-sm"
					:disabled="isStreaming"
					@keydown.enter.exact.prevent="handleSubmit"
				/>
				<button
					type="submit"
					:disabled="!inputMessage.trim() || isStreaming"
					class="px-4 py-2.5 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed rounded-xl text-white font-medium transition-all"
				>
					<svg v-if="!isStreaming" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
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
import { ref, computed, onMounted, nextTick, watch } from 'vue';
import axios from 'axios';

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
	} catch (err) {
		console.error('Failed to fetch context:', err);
	}
}

function formatMessage(content: string): string {
	// Basic markdown-like formatting
	let formatted = content
		// Code blocks
		.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="bg-slate-900 rounded p-2 my-2 overflow-x-auto"><code>$2</code></pre>')
		// Inline code
		.replace(/`([^`]+)`/g, '<code class="bg-slate-900 px-1 rounded">$1</code>')
		// Bold
		.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
		// Italic
		.replace(/\*([^*]+)\*/g, '<em>$1</em>')
		// Line breaks
		.replace(/\n/g, '<br/>');
	
	return formatted;
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
/* Custom scrollbar */
.overflow-y-auto::-webkit-scrollbar {
	width: 6px;
}
.overflow-y-auto::-webkit-scrollbar-track {
	background: transparent;
}
.overflow-y-auto::-webkit-scrollbar-thumb {
	background: #475569;
	border-radius: 3px;
}
.overflow-y-auto::-webkit-scrollbar-thumb:hover {
	background: #64748b;
}

/* Prose overrides for dark mode */
.prose-invert code {
	color: #e2e8f0;
}
.prose-invert pre {
	background: #0f172a;
}
</style>
