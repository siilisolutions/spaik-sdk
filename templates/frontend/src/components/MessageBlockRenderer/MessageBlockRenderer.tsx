import { MessageBlock } from 'spaik-sdk-react';
import { getBlockTypeStyle } from './blockStyles';
import { BlockTypeHeader } from './BlockTypeHeader';
import { ToolNameDisplay } from './ToolNameDisplay';
import { BlockContent } from './BlockContent';
import { ToolArgumentsDisplay } from './ToolArgumentsDisplay';

interface Props {
    block: MessageBlock;
}

export function MessageBlockRenderer({ block }: Props) {
    return (
        <div style={getBlockTypeStyle(block.type)}>
            <BlockTypeHeader
                type={block.type}
                streaming={block.streaming}
            />

            <ToolNameDisplay toolName={block.tool_name} />
            <ToolArgumentsDisplay toolCallArgs={block.tool_call_args} />
            <BlockContent block={block} />

        </div>
    );
} 