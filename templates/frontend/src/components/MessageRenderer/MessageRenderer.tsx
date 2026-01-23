import { Message } from 'spaik-sdk-react';
import { MessageContent } from './MessageContent';
import { MessageHeader } from './MessageHeader';

interface Props {
    message: Message;
}

export function MessageRenderer({ message }: Props) {

    return (
        <div style={{
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '16px',
            backgroundColor: 'white',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)'
        }}>
            <MessageHeader message={message} />
            <MessageContent message={message} />
        </div>
    );
} 