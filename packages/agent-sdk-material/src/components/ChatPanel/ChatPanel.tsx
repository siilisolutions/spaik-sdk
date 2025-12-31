import { useState, useEffect, useRef } from 'react';
import { Box, Typography, IconButton } from '@mui/material';
import { useThread, useThreadSelection } from '@siilisolutions/ai-sdk-react';
import { ChatHeader } from './ChatHeader';
import { MessageList } from './MessageList';
import { MessageInput } from '../MessageInput/MessageInput';
import { MenuIcon } from '../../utils/icons';

interface Props {
    filesBaseUrl?: string;
    onMenuClick?: () => void;
    showMenuButton?: boolean;
}

export function ChatPanel({ filesBaseUrl, onMenuClick, showMenuButton }: Props) {
    const { selectedThreadId } = useThreadSelection();
    const { thread, loading } = useThread(selectedThreadId || '');
    const [waitingForResponse, setWaitingForResponse] = useState(false);
    const prevMessageCountRef = useRef(0);

    // Clear waiting state when we get new messages (AI started responding)
    useEffect(() => {
        const currentCount = thread?.messages?.length ?? 0;
        if (currentCount > prevMessageCountRef.current) {
            // New message arrived, check if it's from AI
            const lastMessage = thread?.messages?.[currentCount - 1];
            if (lastMessage?.ai) {
                setWaitingForResponse(false);
            }
        }
        prevMessageCountRef.current = currentCount;
    }, [thread?.messages]);

    // Clear waiting state when thread changes
    useEffect(() => {
        setWaitingForResponse(false);
        prevMessageCountRef.current = thread?.messages?.length ?? 0;
    }, [selectedThreadId]);

    const handleMessageSent = () => {
        setWaitingForResponse(true);
    };

    if (!selectedThreadId) {
        return (
            <Box
                sx={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    bgcolor: 'background.default',
                }}
            >
                {showMenuButton && (
                    <Box sx={{ p: 1 }}>
                        <IconButton onClick={onMenuClick} edge="start">
                            <MenuIcon />
                        </IconButton>
                    </Box>
                )}
                <Box
                    sx={{
                        flex: 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                    }}
                >
                    <Typography color="text.secondary" variant="h6">
                        Select or create a thread to start chatting
                    </Typography>
                </Box>
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
            <ChatHeader 
                title={title} 
                onMenuClick={onMenuClick}
                showMenuButton={showMenuButton}
            />
            <MessageList
                messages={thread?.messages}
                isLoading={loading}
                filesBaseUrl={filesBaseUrl}
                showTypingIndicator={waitingForResponse}
            />
            <MessageInput 
                threadId={selectedThreadId} 
                filesBaseUrl={filesBaseUrl}
                onMessageSent={handleMessageSent}
            />
        </Box>
    );
}
