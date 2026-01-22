import { Message } from '@spaik/react';
import { AuthorIndicator } from './AuthorIndicator';
import { MessageTimestamp } from './MessageTimestamp';

interface Props {
    message: Message;
}

export function MessageHeader({ message }: Props) {
    return (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '12px',
            paddingBottom: '8px',
            borderBottom: '1px solid #e5e7eb'
        }}>
            <AuthorIndicator message={message} />
            <MessageTimestamp timestamp={message.timestamp} />
        </div>
    );
} 