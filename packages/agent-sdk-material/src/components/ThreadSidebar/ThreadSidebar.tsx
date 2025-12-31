import { Box, Button, List, Typography, Skeleton, Divider } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import LightModeIcon from '@mui/icons-material/LightMode';
import IconButton from '@mui/material/IconButton';
import { useThreadList, useThreadSelection, useThreadActions } from '@siilisolutions/ai-sdk-react';
import { ThreadListItem } from './ThreadListItem';
import { useAgentTheme } from '../../theme/useAgentTheme';

interface Props {
    width?: number | string;
}

export function ThreadSidebar({ width = 300 }: Props) {
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
            <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={handleCreateThread}
                    fullWidth
                    sx={{ py: 1.25 }}
                >
                    New Thread
                </Button>
                <IconButton onClick={toggleMode} size="small">
                    {isDark ? <LightModeIcon /> : <DarkModeIcon />}
                </IconButton>
            </Box>

            <Divider />

            <Box sx={{ flex: 1, overflow: 'auto', p: 1 }}>
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

