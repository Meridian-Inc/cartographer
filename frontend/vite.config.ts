import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { readFileSync } from "fs";
import { resolve } from "path";

// Read version from package.json
const packageJson = JSON.parse(
	readFileSync(resolve(__dirname, "package.json"), "utf-8")
);

export default defineConfig({
	plugins: [vue()],
	define: {
		__APP_VERSION__: JSON.stringify(packageJson.version),
	},
	server: {
		port: 5173,
		proxy: {
			"/api": {
				target: "http://localhost:8000",
				changeOrigin: true,
			},
		},
	},
})


