import { useState } from 'react';
import { Id } from '../../stores/messageTypes';
import { ThreadMessage } from '../../api/ThreadsApiClient';
import { MessageRenderer } from '../MessageRenderer';

function ThreadMessageList({ messages }: { messages: ThreadMessage[] }) {
    if (messages.length === 0) {
        return (
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '200px',
                color: '#6c757d'
            }}>
                No messages yet
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {messages.map((message) => (
                <MessageRenderer key={message.id} messageId={message.id} />
            ))}
        </div>
    );
}

interface Props {
    threadId: Id | null;
    onSendMessage: (threadId: Id, message: string) => Promise<void>;
    messages: ThreadMessage[];
}

export function ThreadView({ threadId, onSendMessage, messages }: Props) {
    const [inputMessage, setInputMessage] = useState('');
    const [isSending, setIsSending] = useState(false);

    const handleSendMessage = async () => {
        if (!threadId || !inputMessage.trim() || isSending) return;

        setIsSending(true);
        try {
            await onSendMessage(threadId, inputMessage.trim());
            setInputMessage('');
        } catch (error) {
            console.error('Failed to send message:', error);
        } finally {
            setIsSending(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    if (!threadId) {
        return (
            <div style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: '#f8f9fa',
                color: '#6c757d',
                fontSize: '16px'
            }}>
                Select a thread to start chatting
            </div>
        );
    }

    return (
        <div style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            height: '100vh'
        }}>
            <div style={{
                padding: '16px 24px',
                borderBottom: '1px solid #e1e5e9',
                backgroundColor: 'white',
                boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
            }}>
                <h2 style={{
                    margin: 0,
                    fontSize: '18px',
                    fontWeight: '600',
                    color: '#212529'
                }}>
                    Thread: {threadId?.slice(0, 8)}...
                </h2>
            </div>

            <div style={{
                flex: 1,
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column'
            }}>
                <div style={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: '16px 24px'
                }}>
                    {messages.length === 0 ? (
                        <div style={{
                            textAlign: 'center',
                            color: '#6c757d',
                            fontSize: '14px',
                            padding: '40px 20px'
                        }}>
                            No messages yet. Start the conversation!
                        </div>
                    ) : (
                        <ThreadMessageList messages={messages} />
                    )}
                </div>

                <div style={{
                    padding: '16px 24px',
                    borderTop: '1px solid #e1e5e9',
                    backgroundColor: 'white'
                }}>
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
                        <textarea
                            value={inputMessage}
                            onChange={(e) => setInputMessage(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Type your message here..."
                            disabled={isSending}
                            style={{
                                flex: 1,
                                minHeight: '44px',
                                maxHeight: '120px',
                                padding: '12px',
                                borderRadius: '8px',
                                border: '1px solid #d1d5db',
                                resize: 'none',
                                fontSize: '14px',
                                fontFamily: 'inherit',
                                outline: 'none',
                                transition: 'border-color 0.2s',
                                backgroundColor: isSending ? '#f9f9f9' : 'white'
                            }}
                            onFocus={(e) => e.target.style.borderColor = '#007bff'}
                            onBlur={(e) => e.target.style.borderColor = '#d1d5db'}
                        />
                        <button
                            onClick={handleSendMessage}
                            disabled={!inputMessage.trim() || isSending}
                            style={{
                                padding: '12px 20px',
                                borderRadius: '8px',
                                border: 'none',
                                backgroundColor: (!inputMessage.trim() || isSending) ? '#6c757d' : '#007bff',
                                color: 'white',
                                fontSize: '14px',
                                fontWeight: '500',
                                cursor: (!inputMessage.trim() || isSending) ? 'not-allowed' : 'pointer',
                                transition: 'background-color 0.2s',
                                minWidth: '80px'
                            }}
                        >
                            {isSending ? 'Sending...' : 'Send'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
} 