import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/signup": "http://localhost:5000",
      "/login": "http://localhost:5000",
      "/books": "http://localhost:5000",
      "/borrow": "http://localhost:5000",
      "/return": "http://localhost:5000",
      "/history": "http://localhost:5000",
      "/recommendations": "http://localhost:5000",
      "/book-pdf": "http://localhost:5000",
      "/overdue": "http://localhost:5000",
      "/admin": "http://localhost:5000",
    },
  },
});
