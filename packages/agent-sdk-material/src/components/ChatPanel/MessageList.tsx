import { useEffect, useRef } from 'react';
import { Box, Skeleton } from '@mui/material';
import { Message } from 'spaik-sdk-react';
import { MessageCard } from '../Message/MessageCard';
import { TypingIndicator } from './TypingIndicator';

interface Props {
    messages: Message[] | undefined;
    isLoading?: boolean;
    filesBaseUrl?: string;
    showTypingIndicator?: boolean;
    enableTTS?: boolean;
    enableCopy?: boolean;
}

export function MessageList({ messages, isLoading, filesBaseUrl, showTypingIndicator, enableTTS = false, enableCopy = true }: Props) {
    const bottomRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        // Use setTimeout to ensure DOM is fully updated
        setTimeout(() => {
            bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 50);
    };

    // Scroll when message count changes
    useEffect(() => {
        scrollToBottom();
    }, [messages?.length]);

    // Scroll when typing indicator appears
    useEffect(() => {
        if (showTypingIndicator) {
            scrollToBottom();
        }
    }, [showTypingIndicator]);

    // Also scroll when last message content changes (streaming)
    const lastMessage = messages?.[messages.length - 1];
    const lastBlockContent = lastMessage?.blocks?.[lastMessage.blocks.length - 1]?.content;
    useEffect(() => {
        if (lastBlockContent) {
            scrollToBottom();
        }
    }, [lastBlockContent]);

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

    if (messages.length === 0 && !showTypingIndicator) {
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
                    enableTTS={enableTTS}
                    enableCopy={enableCopy}
                />
            ))}
            {showTypingIndicator && <TypingIndicator />}
            <div ref={bottomRef} />
        </Box>
    );
}
