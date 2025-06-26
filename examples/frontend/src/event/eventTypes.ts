import z from "zod";
import { IdSchema, MessageBlockSchema, MessageSchema } from "../stores/messageTypes";

export const BaseEventSchema = z.object({
    id: IdSchema,
    event_type: z.string(),
    data: z.unknown().optional(),
});

export const StreamingUpdatedEventSchema = z.object({
    event_type: z.literal('StreamingUpdated'),
    data: z.object({
        block_id: IdSchema,
        content: z.string(),
    }),
    // Allow extra fields that might be present
}).passthrough();

export const BlockAddedEventSchema = z.object({
    event_type: z.literal('BlockAdded'),
    thread_id: IdSchema,
    data: z.object({
        message_id: IdSchema,
        block: MessageBlockSchema,
    }),
}).passthrough();

export const MessageFullyAddedEventSchema = z.object({
    thread_id: IdSchema,
    event_type: z.literal('MessageFullyAdded'),
    data: z.object({
        message_id: IdSchema,
    }),
}).passthrough();

export const BlockFullyAddedEventSchema = z.object({
    thread_id: IdSchema,
    event_type: z.literal('BlockFullyAdded'),
    data: z.object({
        message_id: IdSchema,
        block_id: IdSchema,
    }),
}).passthrough();


export const MessageAddedEventSchema = z.object({
    thread_id: IdSchema,
    event_type: z.literal('MessageAdded'),
    data: MessageSchema,
}).passthrough();



export const ToolResponseReceivedEventSchema = z.object({
    event_type: z.literal('ToolResponseReceived'),
    data: z.object({
        response: z.string(),
        block_id: IdSchema,
        tool_call_id: IdSchema,
    }),
}).passthrough();

// Standard events with event_type
export const EventSchema = z.discriminatedUnion('event_type', [
    StreamingUpdatedEventSchema,
    BlockAddedEventSchema,
    MessageFullyAddedEventSchema,
    BlockFullyAddedEventSchema,
    MessageAddedEventSchema,
    ToolResponseReceivedEventSchema,
]);


export type BaseEvent = z.infer<typeof EventSchema>;
export type StreamingUpdatedEvent = z.infer<typeof StreamingUpdatedEventSchema>;
export type BlockAddedEvent = z.infer<typeof BlockAddedEventSchema>;
export type MessageFullyAddedEvent = z.infer<typeof MessageFullyAddedEventSchema>;
export type MessageAddedEvent = z.infer<typeof MessageAddedEventSchema>;
export type ToolResponseReceivedEvent = z.infer<typeof ToolResponseReceivedEventSchema>;

