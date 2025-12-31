import type { PendingUpload } from '@siilisolutions/ai-sdk-react';

interface Props {
    uploads: PendingUpload[];
    onRemove: (id: string) => void;
}

export function PendingUploads({ uploads, onRemove }: Props) {
    if (uploads.length === 0) return null;

    return (
        <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '8px',
            padding: '8px 0',
        }}>
            {uploads.map((upload) => (
                <div
                    key={upload.id}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '6px 10px',
                        backgroundColor: upload.status === 'error' ? '#fef2f2' : '#f3f4f6',
                        borderRadius: '6px',
                        fontSize: '13px',
                        border: upload.status === 'error' ? '1px solid #fecaca' : '1px solid #e5e7eb',
                    }}
                >
                    <span style={{ maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {upload.file.name}
                    </span>
                    {upload.status === 'uploading' && (
                        <span style={{ color: '#6b7280' }}>
                            {upload.progress}%
                        </span>
                    )}
                    {upload.status === 'completed' && (
                        <span style={{ color: '#10b981' }}>✓</span>
                    )}
                    {upload.status === 'error' && (
                        <span style={{ color: '#ef4444' }} title={upload.error}>✕</span>
                    )}
                    <button
                        type="button"
                        onClick={() => onRemove(upload.id)}
                        style={{
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            padding: '2px',
                            color: '#9ca3af',
                            fontSize: '12px',
                        }}
                        title="Remove"
                    >
                        ✕
                    </button>
                </div>
            ))}
        </div>
    );
}

