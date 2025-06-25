import { useMessageStore } from '../stores/messageStore';
import { Id } from '../stores/messageTypes';
import { MessageBlockRenderer } from './MessageBlockRenderer';

interface Props {
    messageId: Id;
}

export function MessageRenderer({ messageId }: Props) {
    const message = useMessageStore((state) => state.getMessage(messageId));

    if (!message) {
        return (
            <div style={{
                padding: '16px',
                color: '#6b7280',
                fontStyle: 'italic'
            }}>
                🚫 Message not found: {messageId}
            </div>
        );
    }

    const formatTimestamp = (timestamp: number) => {
        return new Date(timestamp).toLocaleString();
    };

    return (
        <div style={{
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '16px',
            backgroundColor: 'white',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)'
        }}>
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '12px',
                paddingBottom: '8px',
                borderBottom: '1px solid #e5e7eb'
            }}>
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
                <div style={{
                    fontSize: '12px',
                    color: '#9ca3af'
                }}>
                    ⏰ {formatTimestamp(message.timestamp)}
                </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {message.blocks.length === 0 ? (
                    <div style={{
                        color: '#6b7280',
                        fontStyle: 'italic'
                    }}>
                        📭 No content
                    </div>
                ) : (
                    message.blocks.map((block) => (
                        <MessageBlockRenderer key={block.id} block={block} />
                    ))
                )}
            </div>
        </div>
    );
}
