import { Box, Typography } from '@mui/material';
import { useThread, useThreadSelection } from '@siilisolutions/ai-sdk-react';
import { ChatHeader } from './ChatHeader';
import { MessageList } from './MessageList';
import { MessageInput } from '../MessageInput/MessageInput';

interface Props {
    filesBaseUrl?: string;
}

export function ChatPanel({ filesBaseUrl }: Props) {
    const { selectedThreadId } = useThreadSelection();
    const { thread, loading } = useThread(selectedThreadId || '');

    if (!selectedThreadId) {
        return (
            <Box
                sx={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    bgcolor: 'background.default',
                }}
            >
                <Typography color="text.secondary" variant="h6">
                    Select or create a thread to start chatting
                </Typography>
            </Box>
        );
    }

    const firstMessage = thread?.messages?.[0];
    const title = firstMessage?.blocks?.[0]?.content?.slice(0, 40) || 'Chat';

    return (
        <Box
            sx={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
                bgcolor: 'background.default',
            }}
        >
            <ChatHeader title={title} />
            <MessageList
                messages={thread?.messages}
                isLoading={loading}
                filesBaseUrl={filesBaseUrl}
            />
            <MessageInput threadId={selectedThreadId} filesBaseUrl={filesBaseUrl} />
        </Box>
    );
}

