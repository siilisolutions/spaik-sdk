import { MessageBlock } from '@spaik/react';

interface Props {
    block: MessageBlock
}

export function ToolCallResponse({ block }: Props) {
    const response = block.tool_call_response;
    const error = block.tool_call_error;
    if (!response) {
        return (
            <div style={{
                padding: '8px',
                backgroundColor: '#fef3c7',
                border: '1px dashed #f59e0b',
                borderRadius: '4px',
                fontSize: '14px',
                color: '#92400e'
            }}>
                ⏳ Waiting for tool response...
            </div>
        );
    }

    if (error) {
        return (
            <div style={{
                padding: '8px',
                backgroundColor: '#fef2f2',
                border: '1px solid #fca5a5',
                borderRadius: '4px',
                fontSize: '14px'
            }}>
                <div style={{
                    color: '#dc2626',
                    fontWeight: 500,
                    marginBottom: '4px'
                }}>
                    ❌ Tool Error:
                </div>
                <div style={{ color: '#7f1d1d' }}>
                    {error}
                </div>
            </div>
        );
    }

    return (
        <div style={{
            padding: '8px',
            backgroundColor: '#f0fdf4',
            border: '1px solid #bbf7d0',
            borderRadius: '4px',
            fontSize: '14px'
        }}>
            <div style={{
                color: '#166534',
                fontWeight: 500,
                marginBottom: '4px'
            }}>
                ✅ Tool Response:
            </div>
            <div style={{
                color: '#15803d',
                whiteSpace: 'pre-wrap'
            }}>
                {response}
            </div>
        </div>
    );
} 