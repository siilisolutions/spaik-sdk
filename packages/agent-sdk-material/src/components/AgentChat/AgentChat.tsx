import { ReactNode, useMemo, useState } from 'react';
import { Box, Drawer, useMediaQuery, useTheme } from '@mui/material';
import { AbstractAgent, AgentSdkClientProvider, AgentSdkClient, createThreadsApiClient, Message, ThreadRepository, useAgentSdkClient } from 'spaik-sdk-react';
import { ThreadSidebar } from '../ThreadSidebar/ThreadSidebar.js';
import { ChatPanel } from '../ChatPanel/ChatPanel.js';
import { MarkdownProvider, CustomComponentRegistry } from '../../markdown/index.js';

export interface AgentChatProps {
    baseUrl?: string;
    agent?: AbstractAgent;
    threadRepository?: ThreadRepository;
    createAgent?: (threadId: string) => AbstractAgent;
    headers?: Record<string, string>;
    sidebarWidth?: number;
    sidebarHeader?: ReactNode;
    sidebarTitle?: string;
    customComponents?: CustomComponentRegistry;
    renderMessage?: (message: Message, messages: Message[]) => ReactNode;
    renderState?: (state: unknown) => ReactNode;
    enableTTS?: boolean;
    enableSTT?: boolean;
    enableCopy?: boolean;
    sttLanguage?: string;
}

function AgentChatContent(props: AgentChatProps) {
    const client = useAgentSdkClient();
    const theme = useTheme();
    const mobile = useMediaQuery(theme.breakpoints.down('md'));
    const [open, setOpen] = useState(false);
    const hasSidebar = Boolean(client.threadRepository);
    const sidebar = <ThreadSidebar width={props.sidebarWidth ?? 300} header={props.sidebarHeader} title={props.sidebarTitle} />;
    return <Box sx={{ display: 'flex', height: '100%', width: '100%', overflow: 'hidden' }}>
        {hasSidebar ? mobile ? <Drawer open={open} onClose={() => setOpen(false)}>{sidebar}</Drawer> : sidebar : null}
        <ChatPanel filesBaseUrl={props.baseUrl} showMenuButton={hasSidebar && mobile} onMenuClick={() => setOpen(value => !value)}
            enableTTS={props.enableTTS} enableSTT={props.enableSTT} enableCopy={props.enableCopy} sttLanguage={props.sttLanguage}
            renderMessage={props.renderMessage} renderState={props.renderState} />
    </Box>;
}

export function AgentChat(props: AgentChatProps) {
    const client = useMemo(() => {
        if (props.agent || props.threadRepository) return new AgentSdkClient({ agent: props.agent, threadRepository: props.threadRepository, createAgent: props.createAgent });
        if (props.baseUrl) return new AgentSdkClient(createThreadsApiClient({ baseUrl: props.baseUrl, headers: props.headers }));
        throw new Error('AgentChat requires an AG-UI agent or Spaik baseUrl');
    }, [props.agent, props.threadRepository, props.createAgent, props.baseUrl, props.headers]);
    return <AgentSdkClientProvider key={props.agent?.threadId ?? props.baseUrl} apiClient={client}>
        <MarkdownProvider customComponents={props.customComponents} filesBaseUrl={props.baseUrl}>
            <AgentChatContent {...props} />
        </MarkdownProvider>
    </AgentSdkClientProvider>;
}
