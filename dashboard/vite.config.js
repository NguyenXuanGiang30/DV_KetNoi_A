import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Data endpoints
      '/api/v1/analytics/events/recent': {
        target: 'http://localhost:8005',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/v1\/analytics/, '/api/v1')
      },
      '/api/v1/analytics/metrics': {
        target: 'http://localhost:8005',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/v1\/analytics/, '/api/v1')
      },
      '/api/v1/access/logs/recent': {
        target: 'http://localhost:8003',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/v1\/access/, '/access')
      },
      '/api/v1/notifications/recent': {
        target: 'http://localhost:8007',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/v1\/notifications/, '/api/v1/notifications')
      },

      // Health checks for services
      '/api/v1/ingestion/health': { target: 'http://localhost:8001', changeOrigin: true, rewrite: () => '/health' },
      '/api/v1/camera/health': { target: 'http://localhost:8002', changeOrigin: true, rewrite: () => '/health' },
      '/api/v1/access/health': { target: 'http://localhost:8003', changeOrigin: true, rewrite: () => '/health' },
      '/api/v1/vision/health': { target: 'http://localhost:8004', changeOrigin: true, rewrite: () => '/health' },
      '/api/v1/analytics/health': { target: 'http://localhost:8005', changeOrigin: true, rewrite: () => '/health' },
      '/api/v1/core/health': { target: 'http://localhost:8006', changeOrigin: true, rewrite: () => '/health' },
      '/api/v1/notifications/health': { target: 'http://localhost:8007', changeOrigin: true, rewrite: () => '/health' },
    }
  }
})
