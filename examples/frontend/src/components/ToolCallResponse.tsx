import { useEffect, useState } from 'react';
import { getToolCallResponse } from '../stores/toolCallResponseStore';
import { Id, ToolCallResponse as ToolCallResponseType } from '../stores/messageTypes';

interface Props {
    toolCallId?: Id;
    existingResponse?: ToolCallResponseType;
}

export function ToolCallResponse({ toolCallId, existingResponse }: Props) {
    const [response, setResponse] = useState<ToolCallResponseType | undefined>(existingResponse);

    useEffect(() => {
        if (existingResponse) {
            setResponse(existingResponse);
            return;
        }

        if (!toolCallId) return;

        // Get initial response
        const initialResponse = getToolCallResponse(toolCallId);
        setResponse(initialResponse);

        // Poll for updates if no response yet
        if (!initialResponse) {
            const interval = setInterval(() => {
                const updatedResponse = getToolCallResponse(toolCallId);
                if (updatedResponse) {
                    setResponse(updatedResponse);
                    clearInterval(interval);
                }
            }, 100);

            return () => clearInterval(interval);
        }
    }, [toolCallId, existingResponse]);

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

    if (response.error) {
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
                    {response.error}
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
                {response.response}
            </div>
        </div>
    );
} 