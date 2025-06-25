import { BaseEvent } from "../event/eventTypes";
import { parseEvent } from "../event/parseEvent";
import { appendStreamingContent } from "../stores/streamingStore";
import { addBlockToMessage, getAllMessages } from "../stores/messageStore";
import { addToolCallResponse } from "../stores/toolCallResponseStore";
import { addMessageToThread } from "../stores/threadStore";
import { Id } from "../stores/messageTypes";

export abstract class EventReaderClient {
    private jobId?: Id;
    private getThreadIdForJob?: (jobId: Id) => Id | undefined;
    private onStreamingComplete?: (threadId: Id) => void;
    private onMessageAdded?: (threadId: Id, messageId: Id) => void;
    private seenMessages = new Set<Id>(); // Track which messages we've already seen

    protected setJobContext(
        jobId: Id,
        getThreadIdForJob: (jobId: Id) => Id | undefined,
        onStreamingComplete?: (threadId: Id) => void,
        onMessageAdded?: (threadId: Id, messageId: Id) => void
    ): void {
        this.jobId = jobId;
        this.getThreadIdForJob = getThreadIdForJob;
        this.onStreamingComplete = onStreamingComplete;
        this.onMessageAdded = onMessageAdded;
    }

    protected onEvent(event: BaseEvent): void {
        switch (event.event_type) {
            case 'StreamingUpdated':
                appendStreamingContent(event.data.block_id, event.data.content);
                break;
            case 'BlockAdded':
                addBlockToMessage(event.data.message_id, event.data.block);

                // If this is a new message being added and we have thread context, link it to the thread
                if (this.jobId && this.getThreadIdForJob) {
                    const threadId = this.getThreadIdForJob(this.jobId);
                    if (threadId) {
                        // Get the message from store and add it to the thread
                        const message = getAllMessages().find(m => m.id === event.data.message_id);
                        if (message) {
                            addMessageToThread(threadId, message);

                            // Only notify for NEW messages (first time we see this message ID)
                            if (this.onMessageAdded && !this.seenMessages.has(event.data.message_id)) {
                                this.seenMessages.add(event.data.message_id);
                                this.onMessageAdded(threadId, event.data.message_id);
                            }
                        }
                    }
                }
                break;
            case 'MessageFullyAdded':
                console.log('🎯 MessageFullyAdded:', event);

                // Trigger thread reload when streaming is complete
                if (this.jobId && this.getThreadIdForJob && this.onStreamingComplete) {
                    const threadId = this.getThreadIdForJob(this.jobId);
                    if (threadId) {
                        this.onStreamingComplete(threadId);
                    }
                }
                break;
            case 'ToolResponseReceived':
                addToolCallResponse({
                    id: event.data.tool_call_id,
                    response: event.data.response as string,
                    error: undefined,
                });
                break;
            default:
                console.log('🎯 Unknown event:', event);
                break;
        }
    }

    protected abstract disconnect(): Promise<void>;

    protected handleRawEvent(event: MessageEvent): void {
        const parsedEvent = parseEvent({
            type: event.type,
            data: event.data
        });

        this.onEvent(parsedEvent);
        if (parsedEvent && this.shouldClose(parsedEvent)) {
            console.log('🎯 Stream ended, closing SSE connection');
            this.disconnect();
        }
    }
    protected shouldClose(event: BaseEvent): boolean {
        return event.event_type === 'MessageFullyAdded';
    }

    protected getEventTypes(): string[] {
        return [
            'StreamingUpdated',
            'BlockAdded',
            'MessageFullyAdded',
            'ToolResponseReceived',
        ];
    }
}