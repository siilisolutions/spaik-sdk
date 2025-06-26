interface Props {
    visible?: boolean;
}

export function StreamingIndicator({ visible = true }: Props) {
    if (!visible) return null;

    return (
        <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '2px',
            marginLeft: '4px'
        }}>
            <div style={{
                width: '4px',
                height: '4px',
                backgroundColor: '#666',
                borderRadius: '50%',
                animation: 'streamingDot 1.4s infinite ease-in-out both',
                animationDelay: '0s'
            }} />
            <div style={{
                width: '4px',
                height: '4px',
                backgroundColor: '#666',
                borderRadius: '50%',
                animation: 'streamingDot 1.4s infinite ease-in-out both',
                animationDelay: '0.16s'
            }} />
            <div style={{
                width: '4px',
                height: '4px',
                backgroundColor: '#666',
                borderRadius: '50%',
                animation: 'streamingDot 1.4s infinite ease-in-out both',
                animationDelay: '0.32s'
            }} />
            <style>{`
                @keyframes streamingDot {
                    0%, 80%, 100% {
                        transform: scale(0);
                        opacity: 0.5;
                    }
                    40% {
                        transform: scale(1);
                        opacity: 1;
                    }
                }
            `}</style>
        </div>
    );
} 