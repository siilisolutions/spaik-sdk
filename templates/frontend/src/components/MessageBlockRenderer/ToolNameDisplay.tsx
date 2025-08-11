interface Props {
    toolName?: string;
}

export function ToolNameDisplay({ toolName }: Props) {
    if (!toolName) {
        return null;
    }

    return (
        <div style={{
            fontSize: '14px',
            fontWeight: 500,
            color: '#374151',
            marginBottom: '4px'
        }}>
            🛠️ Tool: {toolName}
        </div>
    );
} 