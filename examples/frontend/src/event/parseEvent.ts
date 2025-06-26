import { BaseEvent, EventSchema } from './eventTypes';
import { nullToUndefined } from '../utils/nullToUndefined';

export function parseEvent(rawEvent: string): BaseEvent {
    const parsedData = JSON.parse(rawEvent);
    const withoutNulls = nullToUndefined(parsedData);
    const parseResult = EventSchema.safeParse(withoutNulls);


    if (parseResult.success) {
        return parseResult.data;
    } else {
        // Log the parsing error but continue - this helps debug schema mismatches
        console.error('Event schema validation failed:', {
            errors: parseResult.error.errors,
            rawEvent
        });
        throw new Error('Event schema validation failed');
    }

}
