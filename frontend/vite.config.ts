import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

/**
 * Create the Vite config used by the standalone chat frontend.
 */
export default defineConfig({
  plugins: [vue()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
