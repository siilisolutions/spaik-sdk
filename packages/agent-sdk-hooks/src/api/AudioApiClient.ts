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
     * Get the streaming TTS URL for direct audio element usage.
     * This allows audio to start playing before the full response is received.
     */
    getStreamingTTSUrl(request: TTSRequest): string {
        // We'll use POST via fetch, but for streaming we construct the endpoint URL
        return `${this.axiosInstance.defaults.baseURL}/audio/speech/stream`;
    }

    /**
     * Stream text to speech audio using fetch.
     * Returns a Response that can be used to get a ReadableStream.
     */
    async textToSpeechStream(request: TTSRequest, signal?: AbortSignal): Promise<Response> {
        const url = `${this.axiosInstance.defaults.baseURL}/audio/speech/stream`;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: request.text,
                model: request.model,
                voice: request.voice ?? 'alloy',
                speed: request.speed ?? 1.0,
                format: request.format ?? 'mp3',
            }),
            signal,
        });

        if (!response.ok) {
            throw new Error(`TTS stream error: ${response.status}`);
        }

        return response;
    }

    /**
     * Convert text to speech audio (non-streaming, waits for full response).
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
        
        // Always send language - default to 'en' to prevent auto-detect issues
        formData.append('language', request.language || 'en');
        
        if (request.prompt) {
            formData.append('prompt', request.prompt);
        }

        console.log('[STT] Sending request with language:', request.language || 'en');
        return this.postFormData('/audio/transcribe', STTResponseSchema, formData);
    }
}

export function createAudioApiClient(config: BaseApiClientConfig): AudioApiClient {
    return new AudioApiClient(config);
}
