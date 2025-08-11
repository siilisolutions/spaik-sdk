import { getTypeEmoji } from './blockStyles';

interface Props {
    type: string;
    streaming?: boolean;
}

export function BlockTypeHeader({ type, streaming }: Props) {
    if (type === 'plain') {
        return null;
    }

    return (
        <div style={{
            fontSize: '12px',
            fontWeight: 600,
            color: '#6b7280',
            textTransform: 'uppercase',
            marginBottom: '4px'
        }}>
            {getTypeEmoji(type)} {type}
            {streaming && (
                <span style={{ marginLeft: '8px', color: '#3b82f6' }}>
                    ✨ streaming...
                </span>
            )}
        </div>
    );
} 