import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

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

    protected async get<T>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
        return this.axiosInstance.get<T>(url, config);
    }

    protected async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
        return this.axiosInstance.post<T>(url, data, config);
    }

    protected async put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
        return this.axiosInstance.put<T>(url, data, config);
    }

    protected async delete<T>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
        return this.axiosInstance.delete<T>(url, config);
    }
} 