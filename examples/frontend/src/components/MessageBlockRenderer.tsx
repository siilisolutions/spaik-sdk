import { MessageBlock } from '../stores/messageTypes';
import { MessageContent } from './MessageContent';
import { StreamingMessageContent } from './StreamingMessageContent';
import { ToolCallResponse } from './ToolCallResponse';

interface Props {
    block: MessageBlock;
}

export function MessageBlockRenderer({ block }: Props) {
    const getBlockTypeStyle = (type: string): React.CSSProperties => {
        const baseStyle: React.CSSProperties = {
            padding: '12px',
            margin: '8px 0',
            borderRadius: '4px',
        };

        switch (type) {
            case 'reasoning':
                return {
                    ...baseStyle,
                    backgroundColor: '#eff6ff',
                    borderLeft: '4px solid #60a5fa',
                };
            case 'tool_use':
                return {
                    ...baseStyle,
                    backgroundColor: '#f0fdf4',
                    borderLeft: '4px solid #4ade80',
                };
            case 'error':
                return {
                    ...baseStyle,
                    backgroundColor: '#fef2f2',
                    borderLeft: '4px solid #f87171',
                };
            default:
                return {
                    ...baseStyle,
                    backgroundColor: '#f9fafb',
                };
        }
    };

    const getTypeEmoji = (type: string) => {
        switch (type) {
            case 'reasoning':
                return '🤔';
            case 'tool_use':
                return '🔧';
            case 'error':
                return '💥';
            default:
                return '💬';
        }
    };

    const shouldUseStreaming = (blockType: string, isStreaming: boolean) => {
        return isStreaming && (blockType === 'reasoning' || blockType === 'plain');
    };

    return (
        <div style={getBlockTypeStyle(block.type)}>
            {block.type !== 'plain' && (
                <div style={{
                    fontSize: '12px',
                    fontWeight: 600,
                    color: '#6b7280',
                    textTransform: 'uppercase',
                    marginBottom: '4px'
                }}>
                    {getTypeEmoji(block.type)} {block.type}
                    {block.streaming && (
                        <span style={{ marginLeft: '8px', color: '#3b82f6' }}>
                            ✨ streaming...
                        </span>
                    )}
                </div>
            )}

            {block.tool_name && (
                <div style={{
                    fontSize: '14px',
                    fontWeight: 500,
                    color: '#374151',
                    marginBottom: '4px'
                }}>
                    🛠️ Tool: {block.tool_name}
                </div>
            )}

            {/* Render content based on block type and streaming status */}
            {block.type === 'tool_use' ? (
                <ToolCallResponse
                    toolCallId={block.tool_call_id}
                />
            ) : shouldUseStreaming(block.type, block.streaming) ? (
                <StreamingMessageContent blockId={block.id} />
            ) : (
                block.content && <MessageContent content={block.content} />
            )}

            {block.tool_call_args && (
                <details style={{ marginTop: '8px' }}>
                    <summary style={{
                        fontSize: '12px',
                        cursor: 'pointer',
                        color: '#6b7280'
                    }}>
                        📋 Tool Arguments
                    </summary>
                    <pre style={{
                        fontSize: '12px',
                        backgroundColor: '#f3f4f6',
                        padding: '8px',
                        marginTop: '4px',
                        borderRadius: '4px',
                        overflowX: 'auto'
                    }}>
                        {JSON.stringify(block.tool_call_args, null, 2)}
                    </pre>
                </details>
            )}
        </div>
    );
} 