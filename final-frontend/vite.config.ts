import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

export default defineConfig(({ mode }) => {
  if (mode === "production" && !process.env.VITE_API_URL) {
    throw new Error("VITE_API_URL is required for production build. Set it when building (e.g. docker build --build-arg VITE_API_URL=https://api.example.com).");
  }
  return {
    server: {
      host: "::",
      port: 3000,
      hmr: { overlay: false },
      proxy: {
        "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
      },
    },
    plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
    resolve: {
      alias: { "@": path.resolve(__dirname, "./src") },
    },
    esbuild: {
      drop: mode === "production" ? ["console", "debugger"] : undefined,
    },
  };
});
