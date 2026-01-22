import { Box } from '@mui/material';
import { MessageBlock } from '@spaik/react';
import { TextBlock } from '../MessageBlock/TextBlock';
import { ReasoningBlock } from '../MessageBlock/ReasoningBlock';
import { ToolCallBlock } from '../MessageBlock/ToolCallBlock';
import { ErrorBlock } from '../MessageBlock/ErrorBlock';

interface Props {
    blocks: MessageBlock[];
}

export function MessageContent({ blocks }: Props) {
    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {blocks.map((block) => {
                switch (block.type) {
                    case 'plain':
                        return <TextBlock key={block.id} content={block.content || ''} />;
                    case 'reasoning':
                        return <ReasoningBlock key={block.id} content={block.content || ''} />;
                    case 'tool_use':
                        return (
                            <ToolCallBlock
                                key={block.id}
                                toolName={block.tool_name}
                                args={block.tool_call_args}
                                response={block.tool_call_response}
                                error={block.tool_call_error}
                                streaming={block.streaming}
                            />
                        );
                    case 'error':
                        return <ErrorBlock key={block.id} content={block.content || ''} />;
                    default:
                        return <TextBlock key={block.id} content={block.content || ''} />;
                }
            })}
        </Box>
    );
}

