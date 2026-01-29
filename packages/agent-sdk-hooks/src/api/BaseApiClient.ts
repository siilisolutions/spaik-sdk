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

    protected async postFormData<T>(url: string, responseSchema: z.ZodSchema<T>, formData: FormData): Promise<T> {
        const response = await this.axiosInstance.post<T>(url, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return this.parseResponse(response, responseSchema);
    }

    protected async getBlob(url: string): Promise<Blob> {
        const response = await this.axiosInstance.get(url, { responseType: 'blob' });
        return response.data as Blob;
    }

    protected async postStream(
        url: string,
        data: unknown,
        onChunk: (chunk: string) => void,
        signal?: AbortSignal
    ): Promise<void> {
        // Concatenate baseURL and url directly to preserve the path portion of baseURL
        // Using new URL() here would incorrectly treat '/threads/...' as an absolute path
        // and ignore the path in baseURL (e.g., '/api/chat')
        const baseUrl = this.axiosInstance.defaults.baseURL || '';
        const fullUrl = baseUrl + url;

        // Build headers explicitly for fetch
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache',
        };

        // Add all headers from axios instance (including custom headers from config)
        const axiosHeaders = this.axiosInstance.defaults.headers;

        // Add common headers
        if (axiosHeaders.common) {
            Object.entries(axiosHeaders.common).forEach(([key, value]) => {
                if (value !== undefined && value !== null && typeof value === 'string') {
                    headers[key] = value;
                }
            });
        }

        // Add POST-specific headers
        if (axiosHeaders.post) {
            Object.entries(axiosHeaders.post).forEach(([key, value]) => {
                if (value !== undefined && value !== null && typeof value === 'string') {
                    headers[key] = value;
                }
            });
        }

        // Add root-level headers (where custom headers like X-Project-Id are stored)
        Object.entries(axiosHeaders).forEach(([key, value]) => {
            // Skip the method-specific header objects
            if (['common', 'delete', 'get', 'head', 'post', 'put', 'patch'].includes(key)) {
                return;
            }
            if (value !== undefined && value !== null && typeof value === 'string') {
                headers[key] = value;
            }
        });

        const response = await fetch(fullUrl, {
            method: 'POST',
            headers,
            body: JSON.stringify(data),
            signal,
            credentials: 'include', // Include cookies for authentication
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