import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import z from 'zod';

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

    private parseResponse<T>(response: AxiosResponse<T>, responseSchema: z.ZodType<T, z.ZodTypeDef, unknown>): T {
        return responseSchema.parse(response.data);
    }

    protected async get<T>(url: string, responseSchema: z.ZodType<T, z.ZodTypeDef, unknown>, config?: AxiosRequestConfig): Promise<T> {
        const response = await this.axiosInstance.get<T>(url, config);
        return this.parseResponse(response, responseSchema);
    }

    protected async post<T>(url: string, responseSchema: z.ZodType<T, z.ZodTypeDef, unknown>, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
        const response = await this.axiosInstance.post<T>(url, data, config);
        return this.parseResponse(response, responseSchema);
    }

    protected async put<T>(url: string, responseSchema: z.ZodType<T, z.ZodTypeDef, unknown>, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
        const response = await this.axiosInstance.put<T>(url, data, config);
        return this.parseResponse(response, responseSchema);
    }

    protected async delete<T>(url: string, responseSchema: z.ZodType<T, z.ZodTypeDef, unknown>, config?: AxiosRequestConfig): Promise<T> {
        const response = await this.axiosInstance.delete<T>(url, config);
        return this.parseResponse(response, responseSchema);
    }

    protected async postFormData<T>(url: string, responseSchema: z.ZodType<T, z.ZodTypeDef, unknown>, formData: FormData): Promise<T> {
        const response = await this.axiosInstance.post<T>(url, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return this.parseResponse(response, responseSchema);
    }

    protected async getBlob(url: string): Promise<Blob> {
        const response = await this.axiosInstance.get(url, { responseType: 'blob' });
        return response.data as Blob;
    }

}
