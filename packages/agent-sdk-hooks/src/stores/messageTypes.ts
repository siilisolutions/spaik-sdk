import { MessageSchema } from '@ag-ui/core/schemas';
import type { Message } from '@ag-ui/core';
import { z } from 'zod';

export { MessageSchema };
export type { Message };
export type Id = string;
export const IdSchema = z.string().min(1);
export const AttachmentSchema = z.object({ file_id: z.string(), mime_type: z.string(), filename: z.string().optional() });
export type Attachment = z.infer<typeof AttachmentSchema>;
export const ThreadSchema = z.object({
    id: IdSchema,
    messages: z.array(z.custom<Message>(value => MessageSchema.safeParse(value).success)),
    message_metadata: z.record(z.string(), z.record(z.string(), z.unknown())).default({}),
});
export type Thread = z.infer<typeof ThreadSchema>;

export function messageText(message: Message): string {
    if (message.role === 'activity' || !('content' in message) || !message.content) return '';
    if (typeof message.content === 'string') return message.content;
    return message.content.filter(part => part.type === 'text').map(part => part.text).join('\n');
}
