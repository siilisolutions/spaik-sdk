import { AgentThemeProvider, AgentChat } from '@spaik/material';

export function App() {
    return (
        <AgentThemeProvider>
            <AgentChat 
                baseUrl="http://localhost:8000" 
                enableTTS={true}
                enableSTT={true}
                enableCopy={true}
            />
        </AgentThemeProvider>
    );
}
