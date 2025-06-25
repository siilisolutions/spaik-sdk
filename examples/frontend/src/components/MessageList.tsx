import { useAllMessageIds } from '../stores/messageStore';
import { MessageRenderer } from './MessageRenderer';

export function MessageList() {
    const messageIds = useAllMessageIds();

    if (messageIds.length === 0) {
        return (
            <div className="flex items-center justify-center h-64 text-gray-500">
                No messages yet
            </div>
        );
    }

    return (
        <div className="space-y-4 p-4">
            {messageIds.map((messageId) => (
                <MessageRenderer key={messageId} messageId={messageId} />
            ))}
        </div>
    );
}
