import type { PendingUpload } from 'spaik-sdk-react';

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
            gap: '6px',
            marginBottom: '10px',
        }}>
            {uploads.map((upload) => (
                <div
                    key={upload.id}
                    style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '4px 8px 4px 10px',
                        backgroundColor: upload.status === 'error' ? '#fef2f2' : '#f3f4f6',
                        borderRadius: '16px',
                        fontSize: '12px',
                        color: upload.status === 'error' ? '#dc2626' : '#4b5563',
                    }}
                >
                    {upload.status === 'uploading' && (
                        <span style={{ 
                            width: '12px', 
                            height: '12px', 
                            border: '2px solid #d1d5db',
                            borderTopColor: '#3b82f6',
                            borderRadius: '50%',
                            animation: 'spin 0.8s linear infinite',
                        }} />
                    )}
                    {upload.status === 'completed' && (
                        <span style={{ color: '#10b981', fontSize: '11px' }}>✓</span>
                    )}
                    {upload.status === 'error' && (
                        <span style={{ fontSize: '11px' }}>!</span>
                    )}
                    <span style={{ 
                        maxWidth: '120px', 
                        overflow: 'hidden', 
                        textOverflow: 'ellipsis', 
                        whiteSpace: 'nowrap',
                    }}>
                        {upload.file.name}
                    </span>
                    <button
                        type="button"
                        onClick={() => onRemove(upload.id)}
                        style={{
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            padding: '0',
                            width: '16px',
                            height: '16px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: '#9ca3af',
                            fontSize: '14px',
                            borderRadius: '50%',
                            transition: 'all 0.15s',
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.backgroundColor = '#e5e7eb';
                            e.currentTarget.style.color = '#6b7280';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.backgroundColor = 'transparent';
                            e.currentTarget.style.color = '#9ca3af';
                        }}
                        title="Remove"
                    >
                        ×
                    </button>
                </div>
            ))}
            <style>{`
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
}
