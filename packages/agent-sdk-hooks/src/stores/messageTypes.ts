import { z } from 'zod';

// Base schemas - Made more flexible for real-world UUIDs
export const IdSchema = z.string().min(1);

// Block types (align with backend MessageBlockType)
export const BlockTypeSchema = z.enum(['plain', 'reasoning', 'tool_use', 'error']);

// Message block schema (align with backend MessageBlock)
export const MessageBlockSchema = z.object({
    id: IdSchema,
    streaming: z.boolean(),
    type: BlockTypeSchema,
    content: z.string().optional(),
    tool_call_id: z.string().optional(),
    tool_call_args: z.record(z.string(), z.any()).optional(),
    tool_name: z.string().optional(),
    tool_call_response: z.string().optional(),
    tool_call_error: z.string().optional(),
});

// Attachment schema (align with backend Attachment)
export const AttachmentSchema = z.object({
    file_id: z.string(),
    mime_type: z.string(),
    filename: z.string().optional(),
});

// Message schema (align with backend ThreadMessage)
export const MessageSchema = z.object({
    id: IdSchema,
    ai: z.boolean(),
    author_id: z.string(),
    author_name: z.string(),
    timestamp: z.number(),
    blocks: z.array(MessageBlockSchema),
    attachments: z.array(AttachmentSchema).optional(),
});

// ToolCallResponse schema (align with backend ToolCallResponse)
export const ToolCallResponseSchema = z.object({
    id: IdSchema,
    response: z.string(),
    error: z.string().optional(),
});

export const ThreadSchema = z.object({
    id: IdSchema,
    messages: z.array(MessageSchema),
});

// Type exports
export type Id = z.infer<typeof IdSchema>;
export type BlockType = z.infer<typeof BlockTypeSchema>;
export type MessageBlock = z.infer<typeof MessageBlockSchema>;
export type Attachment = z.infer<typeof AttachmentSchema>;
export type Message = z.infer<typeof MessageSchema>;
export type ToolCallResponse = z.infer<typeof ToolCallResponseSchema>;
export type Thread = z.infer<typeof ThreadSchema>;
