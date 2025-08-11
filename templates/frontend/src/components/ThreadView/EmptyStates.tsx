export function NoThreadSelected() {
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

export function LoadingState() {
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
            Loading...
        </div>
    );
}

interface ErrorStateProps {
    error: string;
}

export function ErrorState({ error }: ErrorStateProps) {
    return (
        <div style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: '#f8f9fa',
            color: '#dc3545',
            fontSize: '16px'
        }}>
            Error loading thread: {error}
        </div>
    );
} 