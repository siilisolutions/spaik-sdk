
import { useThreadList, useThreadSelection } from '../../stores/threadListStore';
import { useThreadActions } from '../../stores/threadStore';
import { ThreadListItem } from './ThreadListItem';

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


export function ThreadList() {
    const { selectedThreadId, selectThread } = useThreadSelection();
    const { threadSummaries, refresh } = useThreadList();
    const { createThread } = useThreadActions();
    async function handleCreateThread() {
        try {
            const thread = await createThread({});
            // Refresh thread list and select the new thread
            await refresh();
            selectThread(thread.id);
        } catch (error) {
            console.error('Failed to create thread:', error);
        }
    }
    if (!threadSummaries) {
        return (<div style={{
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '12px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            borderRadius: '6px',
            fontSize: '14px',
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
        }}>
            Loading threads...
        </div>)
    }
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
                        onClick={handleCreateThread}
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
                                    onClick={() => selectThread(threadSummary.thread_id)}
                                />
                            ))}

                        </>
                    )}
                </div>
            </div>
        </>
    );
}

