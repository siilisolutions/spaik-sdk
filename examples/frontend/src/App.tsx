import { AgentThemeProvider, AgentChat } from '@siilisolutions/ai-sdk-material';

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
