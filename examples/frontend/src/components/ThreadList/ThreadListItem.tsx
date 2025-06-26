import { Id } from '../../stores/messageTypes';

interface Props {
    threadId: Id;
    title: string;
    messageCount: number;
    lastActivity: number;
    isSelected: boolean;
    onClick: () => void;
}

export function ThreadListItem({ title, messageCount, lastActivity, isSelected, onClick }: Props) {
    const formatTime = (timestamp: number) => {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffMins < 1) return 'now';
        if (diffMins < 60) return `${diffMins}m`;
        if (diffHours < 24) return `${diffHours}h`;
        if (diffDays < 7) return `${diffDays}d`;
        return date.toLocaleDateString();
    };

    return (
        <div
            onClick={onClick}
            className={`thread-list-item ${isSelected ? 'selected' : ''}`}
            style={{
                padding: '12px',
                margin: '2px 0',
                borderRadius: '6px',
                backgroundColor: isSelected ? '#e3f2fd' : 'white',
                border: isSelected ? '1px solid #2196f3' : '1px solid transparent',
                cursor: 'pointer',
                transition: 'all 0.2s',
                boxShadow: isSelected ? '0 2px 4px rgba(33, 150, 243, 0.1)' : '0 1px 2px rgba(0,0,0,0.05)',
            }}

        >
            <div style={{
                fontWeight: '500',
                fontSize: '14px',
                color: '#212529',
                marginBottom: '4px',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
            }}>
                {title}
            </div>
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: '12px',
                color: '#6c757d'
            }}>
                <span>{messageCount} messages</span>
                <span>{formatTime(lastActivity)}</span>
            </div>
        </div>
    );
} 