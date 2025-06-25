import { getStreamingContent } from '../stores/streamingStore';
import { Id } from '../stores/messageTypes';
import { MessageContent } from './MessageContent';
import { useEffect, useState } from 'react';

interface Props {
    blockId: Id;
}

export function StreamingMessageContent({ blockId }: Props) {
    const [content, setContent] = useState('');

    useEffect(() => {
        // Get initial content
        setContent(getStreamingContent(blockId));

        // Set up polling for streaming updates (simple approach)
        const interval = setInterval(() => {
            const streamingContent = getStreamingContent(blockId);
            setContent(streamingContent);
        }, 100);

        return () => clearInterval(interval);
    }, [blockId]);

    return <MessageContent content={content} />;
} 