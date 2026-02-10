import { BaseEvent, EventSchema } from './eventTypes';
import { nullToUndefined } from '../utils/nullToUndefined';

export function parseEvent(rawEvent: string): BaseEvent | undefined {
    const parsedData = JSON.parse(rawEvent);
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
