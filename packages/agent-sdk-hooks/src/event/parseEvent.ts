import { BaseEvent, EventSchema } from './eventTypes';
import { nullToUndefined } from '../utils/nullToUndefined';

export function parseEvent(rawEvent: string): BaseEvent | undefined {
    let parsedData: unknown;
    try {
        parsedData = JSON.parse(rawEvent);
    } catch {
        console.warn('Failed to parse event JSON (skipping):', rawEvent);
        return undefined;
    }
    const withoutNulls = nullToUndefined(parsedData);
    const parseResult = EventSchema.safeParse(withoutNulls);

    if (parseResult.success) {
        return parseResult.data;
    }

    console.warn('Unrecognized event (skipping):', {
        errors: parseResult.error.errors,
        rawEvent,
    });
    return undefined;
}
