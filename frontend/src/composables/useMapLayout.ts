import type { TreeNode } from "../types/network";

export interface SavedLayout {
	version: number;
	timestamp: string;
	positions: Record<string, { x: number; y: number }>;
	root?: TreeNode;
}

// Shared state across components
const positions: Map<string, { x: number; y: number }> = new Map();

export function useMapLayout() {
	function applySavedPositions(root: TreeNode, saved?: SavedLayout) {
		if (!saved) return;
		const walk = (n: TreeNode) => {
			const pos = saved.positions[n.id];
			if (pos) {
				n.fx = pos.x;
				n.fy = pos.y;
				positions.set(n.id, { x: pos.x, y: pos.y });
			}
			for (const c of n.children || []) walk(c);
		};
		walk(root);
	}

	function updatePosition(id: string, x: number, y: number) {
		positions.set(id, { x, y });
	}

	function exportLayout(root: TreeNode): SavedLayout {
		// Ensure we include all nodes, even those not dragged yet (use current fx/fy if set)
		const map: Record<string, { x: number; y: number }> = {};
		const walk = (n: TreeNode) => {
			const p = positions.get(n.id) || (typeof n.fx === "number" && typeof n.fy === "number" ? { x: n.fx, y: n.fy } : undefined);
			if (p) map[n.id] = { x: p.x, y: p.y };
			for (const c of n.children || []) walk(c);
		};
		walk(root);
		return {
			version: 1,
			timestamp: new Date().toISOString(),
			positions: map,
			root: root,
		};
	}

	function importLayout(jsonText: string): SavedLayout {
		const parsed = JSON.parse(jsonText) as SavedLayout;
		return parsed;
	}

	function clearPositions() {
		positions.clear();
	}

	return {
		positions,
		applySavedPositions,
		updatePosition,
		exportLayout,
		importLayout,
		clearPositions,
	};
}


