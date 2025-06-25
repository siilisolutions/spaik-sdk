import { useState, useEffect } from 'react';
import { AgentSdkClient } from './client/AgentSdkClient';
import { JobsApiClient } from './api/JobsApiClient';
import { createThreadsApiClient, ThreadSummary, ThreadMessage } from './api/ThreadsApiClient';
import { ThreadList } from './components/ThreadList/ThreadList';
import { ThreadView } from './components/ThreadView/ThreadView';
import { Id } from './stores/messageTypes';

const config = {
    baseUrl: 'http://localhost:8000',
    timeout: 30000,
    headers: {}
};

const jobsApiClient = new JobsApiClient(config);
const threadsApiClient = createThreadsApiClient(config);
const agentSdkClient = new AgentSdkClient(jobsApiClient, threadsApiClient);

export function App() {
    const [selectedThreadId, setSelectedThreadId] = useState<Id | null>(null);
    const [threadSummaries, setThreadSummaries] = useState<ThreadSummary[]>([]);
    const [currentThreadMessages, setCurrentThreadMessages] = useState<ThreadMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    // Set up streaming complete callback
    useEffect(() => {
        agentSdkClient.setStreamingCompleteCallback((threadId: Id) => {
            // Reload messages for the thread that just received new content
            if (threadId === selectedThreadId) {
                loadThreadMessages(threadId);
            }
        });

        // Set up real-time message addition callback
        agentSdkClient.setMessageAddedCallback((threadId: Id, messageId: Id) => {
            console.log('🎯 MessageAddedCallback:', threadId, messageId);
            // If a new AI message starts in the current thread, add optimistic placeholder
            if (threadId === selectedThreadId) {
                // Create optimistic AI message placeholder
                const optimisticAiMessage: ThreadMessage = {
                    id: messageId,
                    ai: true,
                    author_id: "assistant",
                    author_name: "Assistant",
                    timestamp: Date.now(),
                    blocks: [{
                        id: `block-${messageId}`,
                        streaming: true,
                        type: 'plain',
                        content: '...' // Placeholder content
                    }]
                };

                // Add to current thread messages optimistically
                setCurrentThreadMessages(prev => [...prev, optimisticAiMessage]);
            }
        });
    }, [selectedThreadId]);

    // Load threads on app start
    useEffect(() => {
        loadThreads();
    }, []);

    // Load messages when thread is selected
    useEffect(() => {
        if (selectedThreadId) {
            loadThreadMessages(selectedThreadId);
        } else {
            setCurrentThreadMessages([]);
        }
    }, [selectedThreadId]);

    async function loadThreads() {
        try {
            setIsLoading(true);
            const threads = await agentSdkClient.getThreads();
            setThreadSummaries(threads);
        } catch (error) {
            console.error('Failed to load threads:', error);
        } finally {
            setIsLoading(false);
        }
    }

    async function loadThreadMessages(threadId: Id) {
        try {
            const messages = await agentSdkClient.getThreadMessages(threadId);
            setCurrentThreadMessages(messages);
        } catch (error) {
            console.error('Failed to load thread messages:', error);
            setCurrentThreadMessages([]);
        }
    }

    async function handleCreateThread() {
        try {
            // Create empty thread
            const thread = await agentSdkClient.createThread({});

            // Refresh thread list and select the new thread
            await loadThreads();
            setSelectedThreadId(thread.thread_id);
        } catch (error) {
            console.error('Failed to create thread:', error);
        }
    }

    async function handleSendMessage(threadId: Id, message: string) {
        try {
            // 1. Optimistically add user message to UI
            const optimisticMessage: ThreadMessage = {
                id: `temp-${Date.now()}`, // Temporary ID
                ai: false,
                author_id: "user-1",
                author_name: "User",
                timestamp: Date.now(),
                blocks: [{
                    id: `temp-block-${Date.now()}`,
                    streaming: false,
                    type: 'plain',
                    content: message
                }]
            };

            // Add optimistic message to message store so MessageRenderer can find it
            agentSdkClient.addOptimisticMessage(optimisticMessage, threadId);

            // Add to current thread messages immediately for UI feedback
            if (threadId === selectedThreadId) {
                setCurrentThreadMessages(prev => [...prev, optimisticMessage]);
            }

            // 2. Launch job with thread context
            await agentSdkClient.launchJobForThread(threadId, message);

            // Note: Don't reload immediately - let the streaming events handle updates
        } catch (error) {
            console.error('Failed to send message:', error);
            // Reload messages to remove optimistic message if job failed
            if (threadId === selectedThreadId) {
                await loadThreadMessages(threadId);
            }
            throw error;
        }
    }

    function handleThreadSelect(threadId: Id) {
        setSelectedThreadId(threadId);
    }

    return (
        <div style={{
            display: 'flex',
            height: '100vh',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
        }}>
            <ThreadList
                threadSummaries={threadSummaries}
                selectedThreadId={selectedThreadId}
                onThreadSelect={handleThreadSelect}
                onCreateThread={handleCreateThread}
            />

            <ThreadView
                threadId={selectedThreadId}
                messages={currentThreadMessages}
                onSendMessage={handleSendMessage}
            />

            {isLoading && (
                <div style={{
                    position: 'fixed',
                    top: '20px',
                    right: '20px',
                    padding: '12px 20px',
                    backgroundColor: '#007bff',
                    color: 'white',
                    borderRadius: '6px',
                    fontSize: '14px',
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                }}>
                    Loading threads...
                </div>
            )}
        </div>
    );
}