import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { Id, ToolCallResponse } from './messageTypes';

interface ToolCallResponseStore {
    responses: Map<Id, ToolCallResponse>;
    addResponse: (response: ToolCallResponse) => void;
    getResponse: (toolCallId: Id) => ToolCallResponse | undefined;
    getAllResponses: () => ToolCallResponse[];
    removeResponse: (toolCallId: Id) => void;
    clear: () => void;
}

export const useToolCallResponseStore = create<ToolCallResponseStore>()(
    subscribeWithSelector((set, get) => ({
        responses: new Map(),

        addResponse: (response: ToolCallResponse) => {
            const state = get();
            set({
                responses: new Map(state.responses.set(response.id, response)),
            });
        },

        getResponse: (toolCallId: Id) => {
            return get().responses.get(toolCallId);
        },

        getAllResponses: () => {
            return Array.from(get().responses.values());
        },

        removeResponse: (toolCallId: Id) => {
            const state = get();
            const newResponses = new Map(state.responses);
            newResponses.delete(toolCallId);
            set({ responses: newResponses });
        },

        clear: () => {
            set({ responses: new Map() });
        },
    }))
);

export function addToolCallResponse(response: ToolCallResponse): void {
    useToolCallResponseStore.getState().addResponse(response);
}

export function getToolCallResponse(toolCallId: Id): ToolCallResponse | undefined {
    return useToolCallResponseStore.getState().getResponse(toolCallId);
}

export function removeToolCallResponse(toolCallId: Id): void {
    useToolCallResponseStore.getState().removeResponse(toolCallId);
}

export function getAllToolCallResponses(): ToolCallResponse[] {
    return useToolCallResponseStore.getState().getAllResponses();
}