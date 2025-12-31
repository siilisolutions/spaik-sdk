import { useEffect, useMemo } from 'react';
import { Box } from '@mui/material';
import {
    AgentSdkClientProvider,
    AgentSdkClient,
    createThreadsApiClient,
    useThreadListActions,
} from '@siilisolutions/ai-sdk-react';
import { ThreadSidebar } from '../ThreadSidebar/ThreadSidebar';
import { ChatPanel } from '../ChatPanel/ChatPanel';

interface AgentChatContentProps {
    baseUrl: string;
    sidebarWidth?: number | string;
    showSidebar?: boolean;
}

function AgentChatContent({ baseUrl, sidebarWidth = 300, showSidebar = true }: AgentChatContentProps) {
    const { refresh } = useThreadListActions();

    useEffect(() => {
        refresh();
    }, [refresh]);

    return (
        <Box
            sx={{
                display: 'flex',
                height: '100%',
                width: '100%',
                overflow: 'hidden',
            }}
        >
            {showSidebar && <ThreadSidebar width={sidebarWidth} />}
            <ChatPanel filesBaseUrl={baseUrl} />
        </Box>
    );
}

export interface AgentChatProps {
    baseUrl: string;
    sidebarWidth?: number | string;
    showSidebar?: boolean;
}

export function AgentChat({ baseUrl, sidebarWidth, showSidebar }: AgentChatProps) {
    const apiClient = useMemo(() => {
        const threadsApi = createThreadsApiClient({ baseUrl });
        return new AgentSdkClient(threadsApi);
    }, [baseUrl]);

    return (
        <AgentSdkClientProvider apiClient={apiClient}>
            <AgentChatContent baseUrl={baseUrl} sidebarWidth={sidebarWidth} showSidebar={showSidebar} />
        </AgentSdkClientProvider>
    );
}

