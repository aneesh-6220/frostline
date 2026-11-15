import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// The Python API (UI/api/server.py) serves /api. In development Vite proxies to it; in production the API serves dist/.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 5173, proxy: { "/api": "http://127.0.0.1:8000" } },
  preview: { proxy: { "/api": "http://127.0.0.1:8000" } },
  build: {
    target: "es2022",
    chunkSizeWarningLimit: 5000,
    rolldownOptions: {
      output: {
        advancedChunks: {
          groups: [
            { name: "plotly", test: /plotly\.js-dist-min/ },
            { name: "react", test: /node_modules[\\/](react|react-dom|react-router|scheduler)[\\/]/ },
          ],
        },
      },
    },
  },
});
