import { defineConfig } from '@playwright/test';

export default defineConfig({
    testDir: './tests/browser',
    timeout: 30000,
    use: { baseURL: 'http://localhost:5173', headless: true, permissions: ['microphone'], launchOptions: { args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'] } },
    webServer: [
        { command: 'packages/agent-sdk/.venv/bin/python -m uvicorn server:app --app-dir tests/browser --port 8000', url: 'http://localhost:8000/docs', reuseExistingServer: false },
        { command: 'bun run --cwd examples/frontend dev --host localhost', url: 'http://localhost:5173', reuseExistingServer: false },
    ],
});
