import { StreamingIndicator } from './StreamingIndicator';

interface Props {
    content?: string;
    streaming?: boolean;
}

export function MessageText({ content, streaming }: Props) {
    return (
        <div style={{
            fontSize: '14px',
            whiteSpace: 'pre-wrap'
        }}>
            {content}
            <StreamingIndicator visible={streaming} />
        </div>
    );
} 