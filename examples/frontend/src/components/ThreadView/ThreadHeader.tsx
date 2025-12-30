import { Thread } from '@siilisolutions/ai-sdk-react';

interface Props {
    thread: Thread;
}

export function ThreadHeader({ thread }: Props) {
    return (
        <div style={{
            padding: '16px 24px',
            borderBottom: '1px solid #e1e5e9',
            backgroundColor: 'white',
            boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
        }}>
            <h2 style={{
                margin: 0,
                fontSize: '18px',
                fontWeight: '600',
                color: '#212529'
            }}>
                {thread.id.slice(0, 8)}...
            </h2>
        </div>
    );
} 