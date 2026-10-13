// Thread management hooks
export { useThread, useThreadActions, useAgent } from './stores/threadStore';
export { useThreadList, useThreadSelection, useThreadListActions } from './stores/threadListStore';
export { useFileUploadStore } from './stores/fileUploadStore';
export type { PendingUpload, UploadStatus } from './stores/fileUploadStore';

// Audio hooks (TTS/STT)
export { 
    useAudioStore,
    useTextToSpeech,
    useSpeechToText,
    usePushToTalk,
} from './stores/audioStore';
export type {
    UseTextToSpeechOptions,
    UseTextToSpeechReturn,
    UseSpeechToTextOptions,
    UseSpeechToTextReturn,
    UsePushToTalkOptions,
    UsePushToTalkReturn,
} from './stores/audioStore';

// Client and provider
export { AgentSdkClientProvider, useAgentSdkClient } from './client/AgentSdkClientProvider';
export { AgentSdkClient } from './client/AgentSdkClient';

// API client factory
export { createThreadsApiClient, ThreadsApiClient } from './api/ThreadsApiClient';
export { createFilesApiClient, FilesApiClient } from './api/FilesApiClient';
export { createAudioApiClient, AudioApiClient } from './api/AudioApiClient';
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
export type { TTSRequest, STTRequest, STTResponse } from './api/AudioApiClient';

// Core types
export type {
    Id,
    Thread,
    Message,
    Attachment,
} from './stores/messageTypes';

export { AbstractAgent, HttpAgent } from '@ag-ui/client';
export type { AgentSubscriber, RunAgentParameters } from '@ag-ui/client';
export type { ThreadRepository } from './api/ThreadsApiClient';
export type { AgentSdkClientConfig } from './client/AgentSdkClient';
export { messageText } from './stores/messageTypes';
