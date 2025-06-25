interface Props {
    content: string;
}

export function MessageContent({ content }: Props) {
    return (
        <div style={{
            fontSize: '14px',
            whiteSpace: 'pre-wrap'
        }}>
            {content}
        </div>
    );
} 