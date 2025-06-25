import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { Id, Thread, Message } from './messageTypes';

interface ThreadStore {
    threads: Map<Id, Thread>;
    addThread: (thread: Thread) => void;
    getThread: (threadId: Id) => Thread | undefined;
    getAllThreads: () => Thread[];
    addMessageToThread: (threadId: Id, message: Message) => void;
    clear: () => void;
}

export const useThreadStore = create<ThreadStore>()(
    subscribeWithSelector((set, get) => ({
        threads: new Map(),

        addThread: (thread: Thread) => {
            const state = get();
            set({
                threads: new Map(state.threads.set(thread.id, thread)),
            });
        },

        getThread: (threadId: Id) => {
            return get().threads.get(threadId);
        },

        getAllThreads: () => {
            return Array.from(get().threads.values());
        },

        addMessageToThread: (threadId: Id, message: Message) => {
            const state = get();
            const thread = state.threads.get(threadId);
            if (!thread) return;
            const updatedThread = {
                ...thread,
                messages: [...thread.messages, message.id],
            };
            set({
                threads: new Map(state.threads.set(threadId, updatedThread)),
            });
        },

        clear: () => {
            set({ threads: new Map() });
        },
    }))
);

export function addThread(thread: Thread): void {
    useThreadStore.getState().addThread(thread);
}

export function getThread(threadId: Id): Thread | undefined {
    return useThreadStore.getState().getThread(threadId);
}

export function getAllThreads(): Thread[] {
    return useThreadStore.getState().getAllThreads();
}

export function addMessageToThread(threadId: Id, message: Message): void {
    useThreadStore.getState().addMessageToThread(threadId, message);
}

export function clearThreads(): void {
    useThreadStore.getState().clear();
} 