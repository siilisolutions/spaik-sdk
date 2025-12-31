import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            // Force Vite to use the source files directly instead of pre-bundled versions
            '@siilisolutions/ai-sdk-material': path.resolve(__dirname, '../../packages/agent-sdk-material/src/index.ts'),
            '@siilisolutions/ai-sdk-react': path.resolve(__dirname, '../../packages/agent-sdk-hooks/src/index.ts'),
        },
    },
    optimizeDeps: {
        // Don't pre-bundle our local packages
        exclude: ['@siilisolutions/ai-sdk-material', '@siilisolutions/ai-sdk-react'],
    },
})
