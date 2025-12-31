import { useEffect, useMemo, useState } from 'react';
import { Box, Drawer, useMediaQuery, useTheme } from '@mui/material';
import {
    AgentSdkClientProvider,
    AgentSdkClient,
    createThreadsApiClient,
    useThreadListActions,
    useThreadSelection,
} from '@siilisolutions/ai-sdk-react';
import { ThreadSidebar } from '../ThreadSidebar/ThreadSidebar';
import { ChatPanel } from '../ChatPanel/ChatPanel';

interface AgentChatContentProps {
    baseUrl: string;
    sidebarWidth?: number;
}

function AgentChatContent({ baseUrl, sidebarWidth = 300 }: AgentChatContentProps) {
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

    const sidebar = <ThreadSidebar width={sidebarWidth} />;

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
            />
        </Box>
    );
}

export interface AgentChatProps {
    baseUrl: string;
    sidebarWidth?: number;
}

export function AgentChat({ baseUrl, sidebarWidth }: AgentChatProps) {
    const apiClient = useMemo(() => {
        const threadsApi = createThreadsApiClient({ baseUrl });
        return new AgentSdkClient(threadsApi);
    }, [baseUrl]);

    return (
        <AgentSdkClientProvider apiClient={apiClient}>
            <AgentChatContent baseUrl={baseUrl} sidebarWidth={sidebarWidth} />
        </AgentSdkClientProvider>
    );
}
