// Thread management hooks
export { useThread, useThreadActions, useAgent } from './stores/threadStore.js';
export { useThreadList, useThreadSelection, useThreadListActions } from './stores/threadListStore.js';
export { useFileUploadStore } from './stores/fileUploadStore.js';
export type { PendingUpload, UploadStatus } from './stores/fileUploadStore.js';

// Audio hooks (TTS/STT)
export { 
    useAudioStore,
    useTextToSpeech,
    useSpeechToText,
    usePushToTalk,
} from './stores/audioStore.js';
export type {
    UseTextToSpeechOptions,
    UseTextToSpeechReturn,
    UseSpeechToTextOptions,
    UseSpeechToTextReturn,
    UsePushToTalkOptions,
    UsePushToTalkReturn,
} from './stores/audioStore.js';

// Client and provider
export { AgentSdkClientProvider, useAgentSdkClient } from './client/AgentSdkClientProvider.js';
export { AgentSdkClient } from './client/AgentSdkClient.js';

// API client factory
export { createThreadsApiClient, ThreadsApiClient } from './api/ThreadsApiClient.js';
export { createFilesApiClient, FilesApiClient } from './api/FilesApiClient.js';
export { createAudioApiClient, AudioApiClient } from './api/AudioApiClient.js';
export type { BaseApiClientConfig } from './api/BaseApiClient.js';
export { BaseApiClient } from './api/BaseApiClient.js';

export type {
    CreateThreadRequest,
    CreateMessageRequest,
    AttachmentRequest,
    ThreadSummary,
    ListThreadsFilters,
} from './api/ThreadsApiClient.js';

export type { FileMetadata } from './api/FilesApiClient.js';
export type { TTSRequest, STTRequest, STTResponse } from './api/AudioApiClient.js';

// Core types
export type {
    Id,
    Thread,
    Message,
    Attachment,
} from './stores/messageTypes.js';

export { AbstractAgent, HttpAgent } from '@ag-ui/client';
export type { AgentSubscriber, RunAgentParameters } from '@ag-ui/client';
export type { ThreadRepository } from './api/ThreadsApiClient.js';
export type { AgentSdkClientConfig } from './client/AgentSdkClient.js';
export { messageText } from './stores/messageTypes.js';
