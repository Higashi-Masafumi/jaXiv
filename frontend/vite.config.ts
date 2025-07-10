import { reactRouter } from "@react-router/dev/vite";
import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [tailwindcss(), reactRouter(), tsconfigPaths()],
  define: {
    // React Router v7での環境変数設定
    "import.meta.env.VITE_BACKEND_BASE_URL": JSON.stringify(
      process.env.VITE_BACKEND_BASE_URL ||
        process.env.REACT_APP_BACKEND_URL ||
        "http://localhost:8000"
    ),
  },
});
