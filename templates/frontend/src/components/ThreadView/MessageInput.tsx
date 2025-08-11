import { useState } from 'react';
import { useThreadActions } from '@siili-ai-sdk/hooks';

interface Props {
    threadId: string;
}

export function MessageInput({ threadId }: Props) {
    const [inputMessage, setInputMessage] = useState('');
    const [isSending, setIsSending] = useState(false);
    const { sendMessage } = useThreadActions();
    const handleSendMessage = async () => {
        if (!inputMessage.trim() || isSending) return;

        setIsSending(true);
        try {
            await sendMessage(threadId, { content: inputMessage.trim() });
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

    return (
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
    );
} 