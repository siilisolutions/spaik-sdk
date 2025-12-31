import { create } from 'zustand';
import { useMemo, useCallback, useRef } from 'react';
import { AudioApiClient, createAudioApiClient, TTSRequest } from '../api/AudioApiClient';

// ============================================================================
// Store Types
// ============================================================================

interface AudioState {
    // TTS state
    isPlaying: boolean;
    currentAudioUrl: string | null;
    ttsLoading: boolean;
    ttsError: string | null;

    // STT state
    isRecording: boolean;
    isTranscribing: boolean;
    transcript: string | null;
    sttError: string | null;

    // Actions
    setPlaying: (playing: boolean) => void;
    setCurrentAudioUrl: (url: string | null) => void;
    setTtsLoading: (loading: boolean) => void;
    setTtsError: (error: string | null) => void;
    setRecording: (recording: boolean) => void;
    setTranscribing: (transcribing: boolean) => void;
    setTranscript: (transcript: string | null) => void;
    setSttError: (error: string | null) => void;
    reset: () => void;
}

const initialState = {
    isPlaying: false,
    currentAudioUrl: null,
    ttsLoading: false,
    ttsError: null,
    isRecording: false,
    isTranscribing: false,
    transcript: null,
    sttError: null,
};

export const useAudioStore = create<AudioState>()((set) => ({
    ...initialState,

    setPlaying: (playing) => set({ isPlaying: playing }),
    setCurrentAudioUrl: (url) => set({ currentAudioUrl: url }),
    setTtsLoading: (loading) => set({ ttsLoading: loading }),
    setTtsError: (error) => set({ ttsError: error }),
    setRecording: (recording) => set({ isRecording: recording }),
    setTranscribing: (transcribing) => set({ isTranscribing: transcribing }),
    setTranscript: (transcript) => set({ transcript: transcript }),
    setSttError: (error) => set({ sttError: error }),
    reset: () => set(initialState),
}));

// ============================================================================
// TTS Hook
// ============================================================================

export interface UseTextToSpeechOptions {
    baseUrl: string;
    model?: string;
    voice?: string;
    speed?: number;
    format?: 'mp3' | 'opus' | 'wav';
}

export interface UseTextToSpeechReturn {
    speak: (text: string) => Promise<void>;
    stop: () => void;
    isPlaying: boolean;
    isLoading: boolean;
    error: string | null;
    audioUrl: string | null;
}

export function useTextToSpeech(options: UseTextToSpeechOptions): UseTextToSpeechReturn {
    const { baseUrl, model, voice, speed, format } = options;
    
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const abortControllerRef = useRef<AbortController | null>(null);
    
    const client = useMemo(
        () => createAudioApiClient({ baseUrl }),
        [baseUrl]
    );

    const {
        isPlaying,
        currentAudioUrl,
        ttsLoading,
        ttsError,
        setPlaying,
        setCurrentAudioUrl,
        setTtsLoading,
        setTtsError,
    } = useAudioStore();

    const stop = useCallback(() => {
        // Cancel any pending request
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
        }
        // Stop any playing audio
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
            audioRef.current = null;
        }
        if (currentAudioUrl) {
            URL.revokeObjectURL(currentAudioUrl);
        }
        setPlaying(false);
        setCurrentAudioUrl(null);
        setTtsLoading(false);
    }, [currentAudioUrl, setPlaying, setCurrentAudioUrl, setTtsLoading]);

    const speak = useCallback(async (text: string) => {
        // Stop any currently playing audio
        stop();
        
        setTtsLoading(true);
        setTtsError(null);

        // Create abort controller for this request
        const abortController = new AbortController();
        abortControllerRef.current = abortController;

        try {
            const request: TTSRequest = {
                text,
                model,
                voice,
                speed,
                format: format ?? 'mp3',
            };

            const audioBlob = await client.textToSpeech(request);
            
            // Check if we were aborted
            if (abortController.signal.aborted) {
                return;
            }
            
            const audioUrl = URL.createObjectURL(audioBlob);
            
            setCurrentAudioUrl(audioUrl);

            // Create and play audio
            const audio = new Audio(audioUrl);
            audioRef.current = audio;

            audio.onended = () => {
                setPlaying(false);
                URL.revokeObjectURL(audioUrl);
                setCurrentAudioUrl(null);
            };

            audio.onerror = () => {
                setTtsError('Failed to play audio');
                setPlaying(false);
                URL.revokeObjectURL(audioUrl);
                setCurrentAudioUrl(null);
            };

            await audio.play();
            setPlaying(true);
        } catch (err) {
            setTtsError(err instanceof Error ? err.message : 'TTS failed');
        } finally {
            setTtsLoading(false);
        }
    }, [client, model, voice, speed, format, stop, setTtsLoading, setTtsError, setCurrentAudioUrl, setPlaying]);

    return {
        speak,
        stop,
        isPlaying,
        isLoading: ttsLoading,
        error: ttsError,
        audioUrl: currentAudioUrl,
    };
}

// ============================================================================
// STT Hook
// ============================================================================

export interface UseSpeechToTextOptions {
    baseUrl: string;
    model?: string;
    language?: string;
    prompt?: string;
    onTranscript?: (text: string) => void;
}

export interface UseSpeechToTextReturn {
    startRecording: () => Promise<void>;
    stopRecording: () => Promise<string | null>;
    isRecording: boolean;
    isTranscribing: boolean;
    transcript: string | null;
    error: string | null;
}

export function useSpeechToText(options: UseSpeechToTextOptions): UseSpeechToTextReturn {
    const { baseUrl, language, prompt, onTranscript } = options;

    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);

    const client = useMemo(
        () => createAudioApiClient({ baseUrl }),
        [baseUrl]
    );

    const {
        isRecording,
        isTranscribing,
        transcript,
        sttError,
        setRecording,
        setTranscribing,
        setTranscript,
        setSttError,
    } = useAudioStore();

    const startRecording = useCallback(async () => {
        try {
            setSttError(null);
            setTranscript(null);
            chunksRef.current = [];

            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Prefer webm/opus, fall back to whatever is available
            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                ? 'audio/webm;codecs=opus'
                : MediaRecorder.isTypeSupported('audio/webm')
                    ? 'audio/webm'
                    : 'audio/mp4';

            const mediaRecorder = new MediaRecorder(stream, { mimeType });
            mediaRecorderRef.current = mediaRecorder;

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    chunksRef.current.push(event.data);
                }
            };

            mediaRecorder.start(100); // Collect data every 100ms
            setRecording(true);
        } catch (err) {
            setSttError(err instanceof Error ? err.message : 'Failed to start recording');
        }
    }, [setRecording, setSttError, setTranscript]);

    const stopRecording = useCallback(async (): Promise<string | null> => {
        return new Promise((resolve) => {
            const mediaRecorder = mediaRecorderRef.current;
            
            if (!mediaRecorder || mediaRecorder.state === 'inactive') {
                setRecording(false);
                resolve(null);
                return;
            }

            mediaRecorder.onstop = async () => {
                // Stop all tracks
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
                
                setRecording(false);
                setTranscribing(true);

                try {
                    const audioBlob = new Blob(chunksRef.current, { 
                        type: mediaRecorder.mimeType 
                    });
                    
                    // Determine filename based on mime type
                    const filename = mediaRecorder.mimeType.includes('webm') 
                        ? 'audio.webm' 
                        : 'audio.mp4';

                    const response = await client.speechToText({
                        audio: audioBlob,
                        language,
                        prompt,
                        filename,
                    });

                    setTranscript(response.text);
                    onTranscript?.(response.text);
                    resolve(response.text);
                } catch (err) {
                    const errorMsg = err instanceof Error ? err.message : 'Transcription failed';
                    setSttError(errorMsg);
                    resolve(null);
                } finally {
                    setTranscribing(false);
                    chunksRef.current = [];
                }
            };

            mediaRecorder.stop();
        });
    }, [client, language, prompt, onTranscript, setRecording, setTranscribing, setTranscript, setSttError]);

    return {
        startRecording,
        stopRecording,
        isRecording,
        isTranscribing,
        transcript,
        error: sttError,
    };
}

// ============================================================================
// Push-to-Talk Hook (combines STT with auto-send)
// ============================================================================

export interface UsePushToTalkOptions {
    baseUrl: string;
    language?: string;
    onTranscript?: (text: string) => void;
    onSend?: (text: string) => Promise<void>;
}

export interface UsePushToTalkReturn {
    startRecording: () => Promise<void>;
    stopRecording: () => Promise<void>;
    isRecording: boolean;
    isTranscribing: boolean;
    isProcessing: boolean;
    error: string | null;
}

export function usePushToTalk(options: UsePushToTalkOptions): UsePushToTalkReturn {
    const { baseUrl, language, onTranscript, onSend } = options;

    const stt = useSpeechToText({
        baseUrl,
        language,
        onTranscript,
    });

    const stopRecording = useCallback(async () => {
        const text = await stt.stopRecording();
        if (text && onSend) {
            await onSend(text);
        }
    }, [stt, onSend]);

    return {
        startRecording: stt.startRecording,
        stopRecording,
        isRecording: stt.isRecording,
        isTranscribing: stt.isTranscribing,
        isProcessing: stt.isRecording || stt.isTranscribing,
        error: stt.error,
    };
}
