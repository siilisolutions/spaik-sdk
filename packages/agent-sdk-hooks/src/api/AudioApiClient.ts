import { z } from 'zod';
import { BaseApiClient, BaseApiClientConfig } from './BaseApiClient';

export const STTResponseSchema = z.object({
    text: z.string(),
});

export type STTResponse = z.infer<typeof STTResponseSchema>;

export interface TTSRequest {
    text: string;
    model?: string;
    voice?: string;
    speed?: number;
    format?: 'mp3' | 'opus' | 'aac' | 'flac' | 'wav' | 'pcm';
}

export interface STTRequest {
    audio: Blob;
    language?: string;
    prompt?: string;
    filename?: string;
}

export class AudioApiClient extends BaseApiClient {
    constructor(config: BaseApiClientConfig) {
        super(config);
    }

    /**
     * Convert text to speech audio.
     * @param request TTS request with text and optional voice/model settings
     * @returns Audio blob in the specified format
     */
    async textToSpeech(request: TTSRequest): Promise<Blob> {
        const response = await this.axiosInstance.post('/audio/speech', {
            text: request.text,
            model: request.model,
            voice: request.voice ?? 'alloy',
            speed: request.speed ?? 1.0,
            format: request.format ?? 'mp3',
        }, {
            responseType: 'blob',
        });
        return response.data as Blob;
    }

    /**
     * Transcribe audio to text using Whisper.
     * @param request STT request with audio blob
     * @returns Transcribed text
     */
    async speechToText(request: STTRequest): Promise<STTResponse> {
        const formData = new FormData();
        const filename = request.filename || 'audio.webm';
        formData.append('file', request.audio, filename);
        
        if (request.language) {
            formData.append('language', request.language);
        }
        if (request.prompt) {
            formData.append('prompt', request.prompt);
        }

        return this.postFormData('/audio/transcribe', STTResponseSchema, formData);
    }
}

export function createAudioApiClient(config: BaseApiClientConfig): AudioApiClient {
    return new AudioApiClient(config);
}
