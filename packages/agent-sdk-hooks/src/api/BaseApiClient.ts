import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import z from 'zod';
import { nullToUndefined } from '../utils/nullToUndefined';

export interface BaseApiClientConfig {
    baseUrl: string;
    timeout?: number;
    headers?: Record<string, string>;
}

export abstract class BaseApiClient {
    protected axiosInstance: AxiosInstance;

    constructor(config: BaseApiClientConfig) {
        this.axiosInstance = axios.create({
            baseURL: config.baseUrl,
            timeout: config.timeout ?? 30000,
            headers: {
                'Content-Type': 'application/json',
                ...config.headers,
            },
        });

        this.setupInterceptors();
    }

    protected setupInterceptors(): void {
        // Request interceptor
        this.axiosInstance.interceptors.request.use(
            (config) => config,
            (error) => Promise.reject(error)
        );

        // Response interceptor
        this.axiosInstance.interceptors.response.use(
            (response) => response,
            (error) => {
                if (error.response?.status >= 500) {
                    console.error('Server error:', error.response.data);
                }
                return Promise.reject(error);
            }
        );
    }

    private parseResponse<T>(response: AxiosResponse<T>, responseSchema: z.ZodSchema<T>): T {
        const cleanedData = nullToUndefined(response.data);
        return responseSchema.parse(cleanedData);
    }

    protected async get<T>(url: string, responseSchema: z.ZodSchema<T>, config?: AxiosRequestConfig): Promise<T> {
        const response = await this.axiosInstance.get<T>(url, config);
        return this.parseResponse(response, responseSchema);
    }

    protected async post<T>(url: string, responseSchema: z.ZodSchema<T>, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
        const response = await this.axiosInstance.post<T>(url, data, config);
        return this.parseResponse(response, responseSchema);
    }

    protected async put<T>(url: string, responseSchema: z.ZodSchema<T>, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
        const response = await this.axiosInstance.put<T>(url, data, config);
        return this.parseResponse(response, responseSchema);
    }

    protected async delete<T>(url: string, responseSchema: z.ZodSchema<T>, config?: AxiosRequestConfig): Promise<T> {
        const response = await this.axiosInstance.delete<T>(url, config);
        return this.parseResponse(response, responseSchema);
    }
    protected async postStream(
        url: string,
        data: unknown,
        onChunk: (chunk: string) => void,
        signal?: AbortSignal
    ): Promise<void> {
        const fullUrl = new URL(url, this.axiosInstance.defaults.baseURL).toString();

        // Build headers explicitly for fetch
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache',
        };

        // Add auth headers if they exist
        const commonHeaders = this.axiosInstance.defaults.headers.common;
        if (commonHeaders) {
            Object.entries(commonHeaders).forEach(([key, value]) => {
                if (value !== undefined && value !== null) {
                    headers[key] = String(value);
                }
            });
        }

        const response = await fetch(fullUrl, {
            method: 'POST',
            headers,
            body: JSON.stringify(data),
            signal,
        });

        if (!response.ok) {
            throw new Error(`Stream request failed: ${response.status}`);
        }

        if (!response.body) {
            throw new Error('Response body is null');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        try {
            // eslint-disable-next-line no-constant-condition
            while (true) {
                const { done, value } = await reader.read();

                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                // Process complete SSE events
                const events = buffer.split('\n\n');
                buffer = events.pop() || ''; // Keep incomplete event

                for (const event of events) {
                    if (event.trim()) {
                        onChunk(event);
                    }
                }
            }
        } finally {
            reader.releaseLock();
        }
    }
} 