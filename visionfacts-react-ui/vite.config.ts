import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('node_modules/react/') || 
                id.includes('node_modules/react-dom/') || 
                id.includes('node_modules/scheduler/')) {
              return 'vendor-react';
            }
            if (id.includes('node_modules/exceljs/') || id.includes('node_modules/file-saver/')) {
              return 'vendor-excel';
            }
            if (id.includes('node_modules/framer-motion/')) {
              return 'vendor-motion';
            }
            if (id.includes('node_modules/react-markdown/') || 
                id.includes('node_modules/remark-') || 
                id.includes('node_modules/micromark') ||
                id.includes('node_modules/mdast-') ||
                id.includes('node_modules/unist-') ||
                id.includes('node_modules/remark-gfm')) {
              return 'vendor-markdown';
            }
            if (id.includes('node_modules/lucide-react/')) {
              return 'vendor-icons';
            }
            return 'vendor';
          }
        },
      },
    },
    chunkSizeWarningLimit: 1000, // Optional: increase limit if preferred, but splitting is better
  },
})
