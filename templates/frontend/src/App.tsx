import { useMemo } from 'react';
import { HttpAgent } from 'spaik-sdk-react';
import { AgentThemeProvider, AgentChat } from 'spaik-sdk-material';

export function App() {
    const endpoint = new URLSearchParams(window.location.search).get('agent');
    const agent = useMemo(() => endpoint ? new HttpAgent({ url: endpoint, threadId: 'external-conversation' }) : undefined, [endpoint]);
    return <AgentThemeProvider>
        <AgentChat agent={agent} baseUrl={agent ? undefined : 'http://localhost:8000'}
            enableTTS={!agent} enableSTT={!agent} enableCopy />
    </AgentThemeProvider>;
}
