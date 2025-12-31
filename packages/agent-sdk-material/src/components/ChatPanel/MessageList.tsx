import { useEffect, useRef } from 'react';
import { Box, Skeleton } from '@mui/material';
import { Message } from '@siilisolutions/ai-sdk-react';
import { MessageCard } from '../Message/MessageCard';

interface Props {
    messages: Message[] | undefined;
    isLoading?: boolean;
    filesBaseUrl?: string;
}

export function MessageList({ messages, isLoading, filesBaseUrl }: Props) {
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    if (isLoading || !messages) {
        return (
            <Box sx={{ p: 3 }}>
                {[1, 2, 3].map((i) => (
                    <Skeleton
                        key={i}
                        variant="rounded"
                        height={100}
                        sx={{ mb: 2 }}
                    />
                ))}
            </Box>
        );
    }

    if (messages.length === 0) {
        return (
            <Box
                sx={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'text.secondary',
                }}
            >
                Start a conversation...
            </Box>
        );
    }

    return (
        <Box
            sx={{
                flex: 1,
                overflow: 'auto',
                p: 3,
            }}
        >
            {messages.map((message) => (
                <MessageCard
                    key={message.id}
                    message={message}
                    filesBaseUrl={filesBaseUrl}
                />
            ))}
            <div ref={bottomRef} />
        </Box>
    );
}

