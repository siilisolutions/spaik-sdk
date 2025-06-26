import React from 'react'
import ReactDOM from 'react-dom/client'
import { App } from './App.tsx'
import { AgentSdkClientProvider, AgentSdkClient, ThreadsApiClient } from '@siili-ai-sdk/hooks';


ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <AgentSdkClientProvider apiClient={new AgentSdkClient(new ThreadsApiClient({
            baseUrl: 'http://localhost:8000'
        }))}>
            <App />
        </AgentSdkClientProvider>

    </React.StrictMode>,
) 