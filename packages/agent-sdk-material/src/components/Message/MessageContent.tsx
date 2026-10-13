import { Box } from '@mui/material';
import { Message, messageText } from 'spaik-sdk-react';
import { TextBlock } from '../MessageBlock/TextBlock';
import { ReasoningBlock } from '../MessageBlock/ReasoningBlock';
import { ToolCallBlock } from '../MessageBlock/ToolCallBlock';

interface Props { message: Message; messages?: Message[]; }

export function MessageContent({ message, messages = [] }: Props) {
    if (message.role === 'reasoning') return <ReasoningBlock content={message.content} />;
    if (message.role === 'activity') return <Box component="pre" sx={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(message.content, null, 2)}</Box>;
    return <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <TextBlock content={messageText(message)} />
        {message.role === 'assistant' && message.toolCalls?.map(call => {
            const result = messages.find(m => m.role === 'tool' && m.toolCallId === call.id);
            let args: Record<string, unknown> | undefined;
            try { args = JSON.parse(call.function.arguments); } catch { /* Arguments can still be streaming. */ }
            return <ToolCallBlock key={call.id} toolName={call.function.name} args={args}
                response={result ? messageText(result) : undefined} error={result?.role === 'tool' ? result.error ?? undefined : undefined}
                streaming={!result} />;
        })}
    </Box>;
}
