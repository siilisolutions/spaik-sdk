import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { Id } from './messageTypes';

interface StreamingStore {
    streamingContent: Map<Id, string>;
    appendContent: (id: Id, content: string) => void;
    getContent: (id: Id) => string;
    setContent: (id: Id, content: string) => void;
    clearContent: (id: Id) => void;
    clear: () => void;
}

const useStreamingStore = create<StreamingStore>()(
    subscribeWithSelector((set, get) => ({
        streamingContent: new Map(),

        appendContent: (id: Id, content: string) => {
            const state = get();
            const currentContent = state.streamingContent.get(id) || '';
            const newContent = currentContent + content;

            set({
                streamingContent: new Map(state.streamingContent.set(id, newContent)),
            });
        },

        getContent: (id: Id) => {
            return get().streamingContent.get(id) || '';
        },

        setContent: (id: Id, content: string) => {
            const state = get();
            set({
                streamingContent: new Map(state.streamingContent.set(id, content)),
            });
        },

        clearContent: (id: Id) => {
            const state = get();
            const newStreamingContent = new Map(state.streamingContent);
            newStreamingContent.delete(id);
            set({ streamingContent: newStreamingContent });
        },

        clear: () => {
            set({ streamingContent: new Map() });
        },
    }))
);

export function appendStreamingContent(id: Id, content: string): void {
    useStreamingStore.getState().appendContent(id, content);
}

export function getStreamingContent(id: Id): string {
    return useStreamingStore.getState().getContent(id);
}

export function setStreamingContent(id: Id, content: string): void {
    useStreamingStore.getState().setContent(id, content);
}

export function clearStreamingContent(id: Id): void {
    useStreamingStore.getState().clearContent(id);
}

export function getAllStreamingContent(): Map<Id, string> {
    return useStreamingStore.getState().streamingContent;
}