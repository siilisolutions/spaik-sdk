import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { Id, Message, MessageBlock } from './messageTypes';

interface MessageStore {
    messages: Map<Id, Message>;
    messageIds: Id[];
    addMessage: (message: Message) => void;
    addBlock: (messageId: Id, block: MessageBlock) => void;
    getMessage: (messageId: Id) => Message | undefined;
    getAllMessages: () => Message[];
    clear: () => void;
}

export const useMessageStore = create<MessageStore>()(
    subscribeWithSelector((set, get) => ({
        messages: new Map(),
        messageIds: [],

        addMessage: (message: Message) => {
            const state = get();
            const newMessages = new Map(state.messages.set(message.id, message));
            // Sort message IDs by timestamp instead of alphabetically
            const sortedIds = Array.from(newMessages.keys()).sort((a, b) => {
                const messageA = newMessages.get(a);
                const messageB = newMessages.get(b);
                if (!messageA || !messageB) return 0;
                return messageA.timestamp - messageB.timestamp;
            });
            set({
                messages: newMessages,
                messageIds: sortedIds,
            });
        },

        addBlock: (messageId: Id, block: MessageBlock) => {
            const state = get();
            let message = state.messages.get(messageId);

            // Create message if it doesn't exist
            if (!message) {
                message = {
                    id: messageId,
                    ai: true, // Default assumption for new messages
                    author_id: 'system',
                    author_name: 'System',
                    timestamp: Date.now(),
                    blocks: [],
                };
            }

            // Add the block to the message
            const updatedMessage = {
                ...message,
                blocks: [...message.blocks, block],
            };

            const newMessages = new Map(state.messages.set(messageId, updatedMessage));
            // Sort message IDs by timestamp instead of alphabetically
            const sortedIds = Array.from(newMessages.keys()).sort((a, b) => {
                const messageA = newMessages.get(a);
                const messageB = newMessages.get(b);
                if (!messageA || !messageB) return 0;
                return messageA.timestamp - messageB.timestamp;
            });
            set({
                messages: newMessages,
                messageIds: sortedIds,
            });
        },

        getMessage: (messageId: Id) => {
            return get().messages.get(messageId);
        },

        getAllMessages: () => {
            return Array.from(get().messages.values());
        },

        clear: () => {
            set({ messages: new Map(), messageIds: [] });
        },
    }))
);

export function addMessage(message: Message): void {
    useMessageStore.getState().addMessage(message);
}

export function addBlockToMessage(messageId: Id, block: MessageBlock): void {
    useMessageStore.getState().addBlock(messageId, block);
}

export function getMessage(messageId: Id): Message | undefined {
    return useMessageStore.getState().getMessage(messageId);
}

export function getAllMessages(): Message[] {
    return useMessageStore.getState().getAllMessages();
}

export function useAllMessageIds(): Id[] {
    return useMessageStore((state) => state.messageIds);
}
