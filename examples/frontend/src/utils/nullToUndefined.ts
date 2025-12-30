
export function nullToUndefined<T>(input: T): T {
    if (input === null) return undefined as unknown as T;
    if (Array.isArray(input)) {
        return input.map(nullToUndefined) as unknown as T;
    }
    if (typeof input === 'object' && input !== null) {
        const result: Record<string, unknown> = {};
        for (const [key, value] of Object.entries(input)) {
            result[key] = nullToUndefined(value);
        }
        return result as unknown as T;
    }
    return input;
} 