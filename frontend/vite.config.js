import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0', // Разрешаем доступ с любых IP
    port: 3000,
    strictPort: true,
    hmr: {
      host: 'localhost', // Для горячей перезагрузки
      protocol: 'ws'
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'esbuild'
  },
  base: './'
})