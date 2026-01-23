import { Message } from 'spaik-sdk-react';

interface Props {
    message: Message;
}

export function AuthorIndicator({ message }: Props) {
    return (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
        }}>
            <div style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                backgroundColor: message.ai ? '#3b82f6' : '#10b981'
            }} />
            <span style={{
                fontWeight: 500,
                color: '#111827'
            }}>
                {message.ai ? '🤖' : '👤'} {message.author_name}
            </span>
            <span style={{
                fontSize: '12px',
                color: '#6b7280'
            }}>
                ({message.ai ? 'AI' : 'Human'})
            </span>
        </div>
    );
} 