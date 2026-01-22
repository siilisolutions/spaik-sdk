import { ReactNode } from 'react';
import { Box, Button, List, Typography, Skeleton, Divider, IconButton } from '@mui/material';
import { useThreadList, useThreadSelection, useThreadActions } from 'spaik-sdk-react';
import { ThreadListItem } from './ThreadListItem';
import { useAgentTheme } from '../../theme/useAgentTheme';
import { AddIcon, DarkModeIcon, LightModeIcon, SmartToyIcon } from '../../utils/icons';

interface Props {
    width?: number | string;
    /** Optional header/logo content. If not provided, shows a default icon + title. */
    header?: ReactNode;
    /** Title shown in default header. Defaults to "Agent Chat" */
    title?: string;
}

export function ThreadSidebar({ width = 300, header, title = 'Agent Chat' }: Props) {
    const { selectedThreadId, selectThread } = useThreadSelection();
    const { threadSummaries, refresh } = useThreadList();
    const { createThread } = useThreadActions();
    const { toggleMode, isDark } = useAgentTheme();

    const handleCreateThread = async () => {
        try {
            const thread = await createThread({});
            await refresh();
            selectThread(thread.id);
        } catch (error) {
            console.error('Failed to create thread:', error);
        }
    };

    const defaultHeader = (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Box 
                sx={{ 
                    width: 36, 
                    height: 36, 
                    borderRadius: 2,
                    bgcolor: 'primary.main',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'primary.contrastText',
                }}
            >
                <SmartToyIcon sx={{ fontSize: 22 }} />
            </Box>
            <Typography variant="h6" fontWeight={700} color="text.primary">
                {title}
            </Typography>
        </Box>
    );

    return (
        <Box
            sx={{
                width,
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                bgcolor: 'background.default',
                borderRight: 1,
                borderColor: 'divider',
            }}
        >
            {/* Header / Logo Area */}
            <Box sx={{ px: 2, py: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                {header ?? defaultHeader}
                <IconButton onClick={toggleMode} size="small" sx={{ ml: 1 }}>
                    {isDark ? <LightModeIcon /> : <DarkModeIcon />}
                </IconButton>
            </Box>

            <Divider />

            {/* New Thread Button */}
            <Box sx={{ p: 2 }}>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={handleCreateThread}
                    fullWidth
                    sx={{ py: 1.25 }}
                >
                    New Thread
                </Button>
            </Box>

            {/* Thread List */}
            <Box sx={{ flex: 1, overflow: 'auto', px: 1 }}>
                <Typography
                    variant="overline"
                    color="text.secondary"
                    sx={{ px: 1, display: 'block', mb: 1 }}
                >
                    Recent Threads
                </Typography>

                {!threadSummaries ? (
                    <Box sx={{ px: 1 }}>
                        {[1, 2, 3].map((i) => (
                            <Skeleton
                                key={i}
                                variant="rounded"
                                height={56}
                                sx={{ mb: 1 }}
                            />
                        ))}
                    </Box>
                ) : threadSummaries.length === 0 ? (
                    <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{ px: 1, py: 2, textAlign: 'center' }}
                    >
                        No threads yet
                    </Typography>
                ) : (
                    <List disablePadding>
                        {threadSummaries.map((summary) => (
                            <ThreadListItem
                                key={summary.thread_id}
                                title={summary.title}
                                messageCount={summary.message_count}
                                lastActivity={summary.last_activity_time}
                                isSelected={selectedThreadId === summary.thread_id}
                                onClick={() => selectThread(summary.thread_id)}
                            />
                        ))}
                    </List>
                )}
            </Box>
        </Box>
    );
}
