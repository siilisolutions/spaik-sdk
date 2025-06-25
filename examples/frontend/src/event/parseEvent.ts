import { BaseEvent, EventSchema } from './eventTypes';
import { nullToUndefined } from '../utils/nullToUndefined';

export interface RawEventData {
    type: string;
    data: string;
}

export function parseEvent(rawEvent: RawEventData): BaseEvent {
    const parsedData = JSON.parse(rawEvent.data);
    const withoutNulls = nullToUndefined(parsedData);
    const parseResult = EventSchema.safeParse(withoutNulls);


    if (parseResult.success) {
        return parseResult.data;
    } else {
        // Log the parsing error but continue - this helps debug schema mismatches
        console.error('Event schema validation failed:', {
            eventType: rawEvent.type,
            eventData: JSON.parse(rawEvent.data),
            errors: parseResult.error.errors
        });
        throw new Error('Event schema validation failed');
    }

}
