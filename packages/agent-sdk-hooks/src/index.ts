// Thread management hooks
export { useThread, useThreadActions, getStreamingHandlers } from './stores/threadStore';
export { useThreadList, useThreadSelection, useThreadListActions } from './stores/threadListStore';
export { useFileUploadStore } from './stores/fileUploadStore';
export type { PendingUpload, UploadStatus } from './stores/fileUploadStore';

// Client and provider
export { AgentSdkClientProvider, useAgentSdkClient } from './client/AgentSdkClientProvider';
export { AgentSdkClient } from './client/AgentSdkClient';

// API client factory
export { createThreadsApiClient, ThreadsApiClient } from './api/ThreadsApiClient';
export { createFilesApiClient, FilesApiClient } from './api/FilesApiClient';
export type { BaseApiClientConfig } from './api/BaseApiClient';
export { BaseApiClient } from './api/BaseApiClient';

export type {
    CreateThreadRequest,
    CreateMessageRequest,
    AttachmentRequest,
    ThreadSummary,
    ListThreadsFilters,
} from './api/ThreadsApiClient';

export type { FileMetadata } from './api/FilesApiClient';

// Core types
export type {
    Id,
    Thread,
    Message,
    MessageBlock,
    BlockType,
    Attachment,
} from './stores/messageTypes';

// Event types for advanced usage
export type { BaseEvent } from './event/eventTypes';
export { EventProcessor } from './event/EventProcessor'; 