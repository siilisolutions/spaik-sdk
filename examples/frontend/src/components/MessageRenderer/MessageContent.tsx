import { Message } from '../../stores/messageTypes';
import { MessageBlockRenderer } from '../MessageBlockRenderer/MessageBlockRenderer';
import { EmptyMessageContent } from './EmptyMessageContent';

interface Props {
    message: Message;
}

export function MessageContent({ message }: Props) {
    if (message.blocks.length === 0) {
        return <EmptyMessageContent />;
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {message.blocks.map((block) => (
                <MessageBlockRenderer key={block.id} block={block} />
            ))}
        </div>
    );
} 