import { Id, useThread } from '@siili-ai-sdk/hooks';
import { ThreadHeader } from './ThreadHeader';
import { MessagesList } from './MessagesList';
import { MessageInput } from './MessageInput';
import { ErrorState, LoadingState } from './EmptyStates';

interface Props {
    threadId: Id;
}

export function ThreadView({ threadId }: Props) {
    const { thread, loading, error } = useThread(threadId);


    if (error) {
        return <ErrorState error={error} />;
    }
    if (loading || !thread) {
        return <LoadingState />;
    }

    return (
        <div style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            height: '100vh'
        }}>
            <ThreadHeader thread={thread} />

            <div style={{
                flex: 1,
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column'
            }}>
                <div style={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: '16px 24px'
                }}>
                    <MessagesList thread={thread} />
                </div>

                <MessageInput threadId={threadId} />
            </div>
        </div>
    );
} 