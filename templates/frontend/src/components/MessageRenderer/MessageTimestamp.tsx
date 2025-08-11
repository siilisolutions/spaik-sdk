interface Props {
    timestamp: number;
}

export function MessageTimestamp({ timestamp }: Props) {
    const formatTimestamp = (timestamp: number) => {
        return new Date(timestamp).toLocaleString();
    };

    return (
        <div style={{
            fontSize: '12px',
            color: '#9ca3af'
        }}>
            ⏰ {formatTimestamp(timestamp)}
        </div>
    );
} 