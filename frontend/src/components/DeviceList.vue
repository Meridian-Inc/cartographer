<template>
	<div class="h-full flex flex-col">
		<div class="p-3 border-b border-slate-200 dark:border-slate-700">
			<input
				v-model="query"
				type="text"
				placeholder="Search by IP, hostname, role..."
				class="w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 px-3 py-2 text-sm"
			/>
		</div>
		<div class="flex-1 overflow-auto">
			<ul>
				<li
					v-for="d in filtered"
					:key="d.id"
					@click="$emit('select', d.id)"
					class="px-3 py-2 border-b border-slate-100 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer flex items-center gap-2"
					:class="{'bg-amber-50 dark:bg-amber-900/30': d.id === selectedId }"
				>
					<span class="w-2 h-2 rounded-full" :class="roleDot(d.role)"></span>
					<span class="text-xs text-slate-500 dark:text-slate-400">{{ d.role }}</span>
					<span class="text-sm text-slate-800 dark:text-slate-200">{{ d.name }}</span>
				</li>
			</ul>
		</div>
	</div>
</template>

<script lang="ts" setup>
import { computed, ref } from "vue";
import type { TreeNode } from "../types/network";

const props = defineProps<{
	root: TreeNode;
	selectedId?: string;
}>();

defineEmits<{
	(e: "select", id: string): void;
}>();

const query = ref("");

function flatten(root: TreeNode): TreeNode[] {
	const res: TreeNode[] = [];
	const walk = (n: TreeNode, isRoot = false) => {
		// Don't add the root itself to the list
		if (!isRoot) {
			res.push(n);
		}
		for (const c of n.children || []) walk(c, false);
	};
	walk(root, true);
	return res.filter(n => n.role !== "group");
}

// Sort nodes by depth, parent position, and IP address (matching map layout)
function sortByDepthAndIP(nodes: TreeNode[], root: TreeNode): TreeNode[] {
	// Build a map of all nodes
	const allNodesMap = new Map<string, TreeNode>();
	nodes.forEach(n => allNodesMap.set(n.id, n));
	
	// Calculate depth for each node based on parentId chain
	const getDepth = (nodeId: string, visited = new Set<string>()): number => {
		if (nodeId === root.id) return 0;
		if (visited.has(nodeId)) return 1; // Prevent infinite loops
		visited.add(nodeId);
		
		const node = allNodesMap.get(nodeId);
		if (!node) return 1;
		
		const parentId = (node as any).parentId;
		if (!parentId || parentId === root.id) {
			return 1; // Direct connection to root
		}
		
		// Recursively get parent's depth
		return getDepth(parentId, visited) + 1;
	};
	
	// Group nodes by depth
	const nodesByDepth = new Map<number, TreeNode[]>();
	nodes.forEach(node => {
		const depth = getDepth(node.id);
		if (!nodesByDepth.has(depth)) {
			nodesByDepth.set(depth, []);
		}
		nodesByDepth.get(depth)!.push(node);
	});
	
	// Parse IP address for sorting
	const parseIpForSorting = (ipStr: string): number[] => {
		const match = ipStr.match(/(\d+)\.(\d+)\.(\d+)\.(\d+)/);
		if (match) {
			return [
				parseInt(match[1]),
				parseInt(match[2]),
				parseInt(match[3]),
				parseInt(match[4])
			];
		}
		return [0, 0, 0, 0];
	};
	
	const compareIps = (a: TreeNode, b: TreeNode): number => {
		const ipA = (a as any).ip || a.id;
		const ipB = (b as any).ip || b.id;
		const partsA = parseIpForSorting(ipA);
		const partsB = parseIpForSorting(ipB);
		
		for (let i = 0; i < 4; i++) {
			if (partsA[i] !== partsB[i]) {
				return partsA[i] - partsB[i];
			}
		}
		return 0;
	};
	
	// Track node sort order for parent-based sorting
	const nodeSortOrder = new Map<string, number>();
	nodeSortOrder.set(root.id, 0);
	
	// Sort each depth level, considering parent positions
	const maxDepth = Math.max(...Array.from(nodesByDepth.keys()), 0);
	for (let depth = 0; depth <= maxDepth; depth++) {
		const nodesAtDepth = nodesByDepth.get(depth) || [];
		if (nodesAtDepth.length === 0) continue;
		
		// Sort by: 1) parent's sort order, 2) IP address
		nodesAtDepth.sort((a, b) => {
			const parentIdA = (a as any).parentId || root.id;
			const parentIdB = (b as any).parentId || root.id;
			const parentOrderA = nodeSortOrder.get(parentIdA) ?? 999999;
			const parentOrderB = nodeSortOrder.get(parentIdB) ?? 999999;
			
			// First, compare by parent position
			if (parentOrderA !== parentOrderB) {
				return parentOrderA - parentOrderB;
			}
			
			// Within same parent group, sort by IP
			return compareIps(a, b);
		});
		
		// Record sort order for this depth (for next depth's sorting)
		nodesAtDepth.forEach((node, index) => {
			nodeSortOrder.set(node.id, index);
		});
	}
	
	// Flatten back to array in sorted order
	const sorted: TreeNode[] = [];
	for (let depth = 0; depth <= maxDepth; depth++) {
		const nodesAtDepth = nodesByDepth.get(depth) || [];
		sorted.push(...nodesAtDepth);
	}
	
	return sorted;
}

const all = computed(() => sortByDepthAndIP(flatten(props.root), props.root));
const filtered = computed(() => {
	const q = query.value.trim().toLowerCase();
	if (!q) return all.value;
	// Filter but maintain the sorted order
	return all.value.filter(n =>
		(n.name?.toLowerCase()?.includes(q)) ||
		(n.role || "").toLowerCase().includes(q) ||
		(n.ip || "").toLowerCase().includes(q) ||
		(n.hostname || "").toLowerCase().includes(q),
	);
});

function roleDot(role?: string) {
	switch (role) {
		case "gateway/router": return "bg-red-500";
		case "switch/ap": return "bg-blue-500";
		case "firewall": return "bg-orange-500";
		case "server": return "bg-green-500";
		case "service": return "bg-emerald-500";
		case "nas": return "bg-purple-500";
		case "client": return "bg-cyan-500";
		default: return "bg-gray-400";
	}
}
</script>


