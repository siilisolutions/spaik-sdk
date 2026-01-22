import { Thread, Message } from '@spaik/react';
import { MessageRenderer } from '../MessageRenderer/MessageRenderer';

interface Props {
    thread: Thread;
}

export function MessagesList({ thread }: Props) {
    if (thread.messages.length === 0) {
        return (
            <div style={{
                textAlign: 'center',
                color: '#6c757d',
                fontSize: '14px',
                padding: '40px 20px'
            }}>
                No messages yet. Start the conversation!
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {thread.messages.map((message: Message) => (
                <MessageRenderer key={message.id} message={message} />
            ))}
        </div>
    );
} 