export function getBlockTypeStyle(type: string): React.CSSProperties {
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
}

export function getTypeEmoji(type: string) {
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
} 