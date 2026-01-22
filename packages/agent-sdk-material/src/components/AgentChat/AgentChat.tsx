import { useEffect, useMemo, useState, ReactNode } from 'react';
import { Box, Drawer, useMediaQuery, useTheme } from '@mui/material';
import {
    AgentSdkClientProvider,
    AgentSdkClient,
    createThreadsApiClient,
    useThreadListActions,
    useThreadSelection,
} from '@spaik/react';
import { ThreadSidebar } from '../ThreadSidebar/ThreadSidebar';
import { ChatPanel } from '../ChatPanel/ChatPanel';
import { MarkdownProvider, CustomComponentRegistry } from '../../markdown';

interface AgentChatContentProps {
    baseUrl: string;
    sidebarWidth?: number;
    sidebarHeader?: ReactNode;
    sidebarTitle?: string;
    enableTTS?: boolean;
    enableSTT?: boolean;
    enableCopy?: boolean;
    sttLanguage?: string;
}

function AgentChatContent({ baseUrl, sidebarWidth = 300, sidebarHeader, sidebarTitle, enableTTS, enableSTT, enableCopy, sttLanguage }: AgentChatContentProps) {
    const { refresh } = useThreadListActions();
    const { selectedThreadId } = useThreadSelection();
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));
    const [mobileOpen, setMobileOpen] = useState(false);

    useEffect(() => {
        refresh();
    }, [refresh]);

    // Close drawer when thread is selected on mobile
    useEffect(() => {
        if (isMobile && selectedThreadId) {
            setMobileOpen(false);
        }
    }, [selectedThreadId, isMobile]);

    const handleDrawerToggle = () => {
        setMobileOpen(!mobileOpen);
    };

    const sidebar = <ThreadSidebar width={sidebarWidth} header={sidebarHeader} title={sidebarTitle} />;

    return (
        <Box
            sx={{
                display: 'flex',
                height: '100%',
                width: '100%',
                overflow: 'hidden',
            }}
        >
            {/* Mobile drawer */}
            {isMobile ? (
                <Drawer
                    variant="temporary"
                    open={mobileOpen}
                    onClose={handleDrawerToggle}
                    ModalProps={{ keepMounted: true }}
                    sx={{
                        '& .MuiDrawer-paper': {
                            width: sidebarWidth,
                            boxSizing: 'border-box',
                        },
                    }}
                >
                    {sidebar}
                </Drawer>
            ) : (
                sidebar
            )}
            <ChatPanel 
                filesBaseUrl={baseUrl} 
                onMenuClick={isMobile ? handleDrawerToggle : undefined}
                showMenuButton={isMobile}
                enableTTS={enableTTS}
                enableSTT={enableSTT}
                enableCopy={enableCopy}
                sttLanguage={sttLanguage}
            />
        </Box>
    );
}

export interface AgentChatProps {
    /** Base URL for the agent API (e.g., "http://localhost:8000") */
    baseUrl: string;
    /** Width of the sidebar in pixels */
    sidebarWidth?: number;
    /** Optional custom header/logo for the sidebar */
    sidebarHeader?: ReactNode;
    /** Title shown in default sidebar header. Defaults to "Agent Chat" */
    sidebarTitle?: string;
    /** 
     * Custom components for markdown rendering.
     * Keys are component names (e.g., "MyCard"), values are React components.
     * Use in AI responses as: <MyCard prop="value" />
     */
    customComponents?: CustomComponentRegistry;
    /** Enable text-to-speech (listen button) on AI messages. Requires /audio/speech endpoint. */
    enableTTS?: boolean;
    /** Enable speech-to-text (push-to-talk button) in message input. Requires /audio/transcribe endpoint. */
    enableSTT?: boolean;
    /** Enable copy button on AI messages (default: true) */
    enableCopy?: boolean;
    /** Language code for STT (e.g., 'en', 'fi'). Defaults to 'en' to prevent auto-detect confusion. */
    sttLanguage?: string;
}

export function AgentChat({ 
    baseUrl, 
    sidebarWidth, 
    sidebarHeader, 
    sidebarTitle,
    customComponents = {},
    enableTTS = false,
    enableSTT = false,
    enableCopy = true,
    sttLanguage = 'en',
}: AgentChatProps) {
    const apiClient = useMemo(() => {
        const threadsApi = createThreadsApiClient({ baseUrl });
        return new AgentSdkClient(threadsApi);
    }, [baseUrl]);

    return (
        <AgentSdkClientProvider apiClient={apiClient}>
            <MarkdownProvider customComponents={customComponents} filesBaseUrl={baseUrl}>
                <AgentChatContent 
                    baseUrl={baseUrl} 
                    sidebarWidth={sidebarWidth}
                    sidebarHeader={sidebarHeader}
                    sidebarTitle={sidebarTitle}
                    enableTTS={enableTTS}
                    enableSTT={enableSTT}
                    enableCopy={enableCopy}
                    sttLanguage={sttLanguage}
                />
            </MarkdownProvider>
        </AgentSdkClientProvider>
    );
}
