import { MessageBlock } from 'spaik-sdk-react';
import { MessageText } from './MessageText';
import { ToolCallResponse } from '../ToolCallResponse';

interface Props {
    block: MessageBlock;
}

export function BlockContent({ block }: Props) {
    if (block.type === 'tool_use') {
        return (
            <ToolCallResponse block={block} />
        );
    }

    return <MessageText content={block.content ?? ""} streaming={block.streaming} />;
} 