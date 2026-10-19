import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

/**
 * Dual-run proxy (Sprint #1 / TASK 8 boundary):
 * - Default: all /api → FastAPI :8000
 * - When VITE_USE_SPRING_PRODUCTS=true:
 *     /api/products      → Spring :8080  (full CRUD exists)
 *     /api/inventory     → Spring :8080  (stock-in/out + ledger)
 *     /api/orders        → Spring :8080  (create/list/get exist; SPA does not call this yet)
 *     /api/expenses      → Spring :8080  (TASK 14 SPA list/filter; FastAPI fallback when flag off)
 *     /api/vendors       → Spring :8080  (SPA contract + remaining FastAPI vendor routes)
 *     /api/dashboard     → Spring :8080  (TASK 13 SPA cutover; FastAPI fallback when flag off)
 *     /api/purchase-orders → Spring :8080  (TASK 17 create/list/deliver; FastAPI fallback when flag off)
 *     everything else    → FastAPI (auth, AI)
 * JWT is shared via the same SECRET_KEY + users table.
 *
 * Production builds use a single VITE_API_URL; this split applies to Vite DEV proxy.
 */
export default defineConfig(({ mode }) => {
  if (mode === "production" && process.env.VITE_API_URL === undefined) {
    throw new Error("VITE_API_URL is required for production build (can be empty string for same-origin reverse-proxy).");
  }
  const fastapi = process.env.VITE_FASTAPI_URL || "http://127.0.0.1:8000";
  const spring = process.env.VITE_SPRING_URL || "http://127.0.0.1:8080";
  const useSpringProducts = process.env.VITE_USE_SPRING_PRODUCTS === "true";

  const proxy = useSpringProducts
    ? {
        "/api/products": { target: spring, changeOrigin: true },
        "/api/inventory": { target: spring, changeOrigin: true },
        "/api/orders": { target: spring, changeOrigin: true },
        "/api/expenses": { target: spring, changeOrigin: true },
        "/api/vendors": { target: spring, changeOrigin: true },
        "/api/dashboard": { target: spring, changeOrigin: true },
        "/api/purchase-orders": { target: spring, changeOrigin: true },
        "/api": { target: fastapi, changeOrigin: true },
      }
    : {
        "/api": { target: fastapi, changeOrigin: true },
      };

  return {
    server: {
      host: "::",
      port: 3000,
      allowedHosts: [".trycloudflare.com"],
      hmr: { overlay: false },
      proxy,
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
