// import { useThreadStore } from '../../stores/threadStore';
import { ThreadSummary } from '../../api/ThreadsApiClient';
import { Id } from '../../stores/messageTypes';

const styles = `
  .thread-list-item:hover {
    background-color: #f5f5f5 !important;
  }
  .thread-list-item.selected:hover {
    background-color: #e3f2fd !important;
  }
  .create-thread-btn:hover {
    background-color: #0056b3 !important;
  }
`;

interface Props {
    onThreadSelect: (threadId: Id) => void;
    onCreateThread: () => void;
    selectedThreadId?: Id | null;
    threadSummaries?: ThreadSummary[];
}

export function ThreadList({ onThreadSelect, onCreateThread, selectedThreadId, threadSummaries = [] }: Props) {
    // Temporarily remove zustand to isolate the issue
    // const threads = useThreadStore((state) => Array.from(state.threads.values()));

    return (
        <>
            <style>{styles}</style>
            <div style={{
                width: '300px',
                height: '100vh',
                borderRight: '1px solid #e1e5e9',
                backgroundColor: '#f8f9fa',
                display: 'flex',
                flexDirection: 'column'
            }}>
                <div style={{
                    padding: '16px',
                    borderBottom: '1px solid #e1e5e9',
                    backgroundColor: 'white'
                }}>
                    <button
                        onClick={onCreateThread}
                        className="create-thread-btn"
                        style={{
                            width: '100%',
                            padding: '12px',
                            backgroundColor: '#007bff',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            fontSize: '14px',
                            fontWeight: '500',
                            cursor: 'pointer',
                            transition: 'background-color 0.2s'
                        }}

                    >
                        + New Thread
                    </button>
                </div>

                <div style={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: '8px'
                }}>
                    <h3 style={{
                        margin: '0 0 12px 0',
                        padding: '0 8px',
                        fontSize: '12px',
                        fontWeight: '600',
                        color: '#6c757d',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px'
                    }}>
                        Recent Threads
                    </h3>

                    {threadSummaries.length === 0 ? (
                        <div style={{
                            padding: '20px 8px',
                            textAlign: 'center',
                            color: '#6c757d',
                            fontSize: '14px'
                        }}>
                            No threads yet. Create your first thread!
                        </div>
                    ) : (
                        <>
                            {threadSummaries.map((threadSummary) => (
                                <ThreadListItem
                                    key={threadSummary.thread_id}
                                    threadId={threadSummary.thread_id}
                                    title={threadSummary.title}
                                    messageCount={threadSummary.message_count}
                                    lastActivity={threadSummary.last_activity_time}
                                    isSelected={selectedThreadId === threadSummary.thread_id}
                                    onClick={() => onThreadSelect(threadSummary.thread_id)}
                                />
                            ))}

                        </>
                    )}
                </div>
            </div>
        </>
    );
}

interface ThreadListItemProps {
    threadId: Id;
    title: string;
    messageCount: number;
    lastActivity: number;
    isSelected: boolean;
    onClick: () => void;
}

function ThreadListItem({ title, messageCount, lastActivity, isSelected, onClick }: ThreadListItemProps) {
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