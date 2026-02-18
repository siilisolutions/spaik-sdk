import { BaseEvent } from "./eventTypes";
import { parseEvent } from "./parseEvent";
import { Id } from "../stores/messageTypes";
import { getStreamingHandlers } from "../stores/threadStore";

export class EventProcessor {

    constructor(private readonly threadId: Id) { }

    public handleRawEvent(event: string): void {
        const parsedEvent = parseEvent(event);
        if (!parsedEvent) return;

        this.onEvent(parsedEvent);
    }

    protected onEvent(event: BaseEvent): void {
        const handlers = getStreamingHandlers();
        switch (event.event_type) {
            case 'StreamingUpdated':
                handlers.appendStreamingContent(this.threadId, event.data.block_id, event.data.content);
                break;
            case 'BlockAdded':
                handlers.addBlock(this.threadId, event.data.message_id, event.data.block);
                break;
            case 'MessageAdded':
                handlers.addMessage(this.threadId, event.data);
                break;
            case 'MessageFullyAdded':
                handlers.completeMessageStreaming(this.threadId, event.data.message_id);
                break;
            case 'BlockFullyAdded':
                handlers.completeBlockStreaming(this.threadId, event.data.block_id);
                break;
            case 'ToolResponseReceived':
                handlers.addToolCallResponse(this.threadId, event.data.block_id, event.data.response);
                break;
            case 'Error':
                console.error('Server error event:', event.data.error_message);
                break;
        }
    }

}
