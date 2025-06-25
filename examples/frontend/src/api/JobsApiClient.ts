import { BaseApiClient, BaseApiClientConfig } from './BaseApiClient';
import { Id, IdSchema } from '../stores/messageTypes';
import z from 'zod';

export class JobsApiClient extends BaseApiClient {
    constructor(config: BaseApiClientConfig) {
        super(config);
    }

    async launchJob(request: LaunchJobRequest): Promise<Id> {
        try {
            const validatedRequest = LaunchJobRequestSchema.parse(request);
            const response = await this.post<LaunchJobResponse>('/jobs/launch', validatedRequest);
            const validatedResponse = LaunchJobResponseSchema.parse(response.data);
            return validatedResponse.job_id;
        } catch (error) {
            throw new Error(`Failed to launch job: ${error}`);
        }
    }
}

export function createLLMApiClient(config: BaseApiClientConfig): JobsApiClient {
    return new JobsApiClient(config);
}

export const LaunchJobRequestSchema = z.object({
    message: z.string(),
    thread_id: IdSchema.optional(),
});

export const LaunchJobResponseSchema = z.object({
    job_id: IdSchema,
});


// Type exports
export type LaunchJobRequest = z.infer<typeof LaunchJobRequestSchema>;
export type LaunchJobResponse = z.infer<typeof LaunchJobResponseSchema>;
