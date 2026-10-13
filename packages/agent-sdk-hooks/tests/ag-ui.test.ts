import { expect, test } from 'bun:test';
import { HttpAgent } from '@ag-ui/client';
import { AgentSdkClient } from '../src/client/AgentSdkClient';

function eventStream(events: unknown[]) {
    const bytes = new TextEncoder().encode(events.map(event => `data: ${JSON.stringify(event)}\n\n`).join(''));
    // Deliberately split inside JSON strings and UTF-8 sequences.
    return new Response(new ReadableStream({ start(controller) {
        for (let index = 0; index < bytes.length; index += 3) controller.enqueue(bytes.slice(index, index + 3));
        controller.close();
    } }), { headers: { 'Content-Type': 'text/event-stream' } });
}

test('independent AG-UI server: fragmented messages, tools, state and cancellation', async () => {
    const agent = new HttpAgent({ url: 'http://independent/agent', threadId: 'thread', fetch: async (_, init) => {
        const input = JSON.parse(String(init.body));
        return eventStream([
            { type: 'RUN_STARTED', threadId: input.threadId, runId: input.runId },
            { type: 'STATE_SNAPSHOT', snapshot: { progress: 1 } },
            { type: 'TEXT_MESSAGE_START', messageId: 'assistant', role: 'assistant' },
            { type: 'TEXT_MESSAGE_CONTENT', messageId: 'assistant', delta: 'Hyvää päivää' },
            { type: 'TOOL_CALL_START', toolCallId: 'tool', toolCallName: 'weather', parentMessageId: 'assistant' },
            { type: 'TOOL_CALL_ARGS', toolCallId: 'tool', delta: '{"city":"Helsinki"}' },
            { type: 'TOOL_CALL_END', toolCallId: 'tool' },
            { type: 'TOOL_CALL_RESULT', toolCallId: 'tool', messageId: 'result', content: 'sunny', role: 'tool' },
            { type: 'TEXT_MESSAGE_END', messageId: 'assistant' },
            { type: 'RUN_FINISHED', threadId: input.threadId, runId: input.runId },
        ]);
    } });
    const client = new AgentSdkClient({ agent });
    await client.sendMessage('thread', { content: 'hello' });
    expect(agent.messages[0].role).toBe('user');
    expect(agent.messages.find(m => m.id === 'assistant')?.content).toBe('Hyvää päivää');
    expect(agent.messages.find(m => m.role === 'tool')?.content).toBe('sunny');
    expect(agent.state).toEqual({ progress: 1 });
    expect(agent.isRunning).toBe(false);
});

test('errors leave the official client usable', async () => {
    const agent = new HttpAgent({ url: 'http://independent/agent', threadId: 'thread', fetch: async (_, init) => {
        const input = JSON.parse(String(init.body));
        return eventStream([{ type: 'RUN_STARTED', threadId: input.threadId, runId: input.runId }, { type: 'RUN_ERROR', message: 'failed' }]);
    } });
    const client = new AgentSdkClient({ agent });
    await expect(client.sendMessage('thread', { content: 'hello' })).rejects.toThrow('failed');
    expect(agent.isRunning).toBe(false);
});
