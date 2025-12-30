interface Props {
    toolCallArgs?: Record<string, unknown>;
}

export function ToolArgumentsDisplay({ toolCallArgs }: Props) {
    if (!toolCallArgs) {
        return null;
    }

    return (
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
                {JSON.stringify(toolCallArgs, null, 2)}
            </pre>
        </details>
    );
} 