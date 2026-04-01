import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "src") },
  },
  server: {
    port: 5173,
    proxy: {
      "/chat/stream": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/demo/lesson/generate/stream": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/chat": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/lesson": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/quiz": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/progress": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/demo": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
