import type { Attachment } from '@spaik/react';

interface Props {
    attachments: Attachment[];
}

const API_BASE = 'http://localhost:8000';

export function AttachmentDisplay({ attachments }: Props) {
    if (attachments.length === 0) return null;

    return (
        <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '8px',
            marginTop: '12px',
        }}>
            {attachments.map((attachment) => (
                <AttachmentItem key={attachment.file_id} attachment={attachment} />
            ))}
        </div>
    );
}

function AttachmentItem({ attachment }: { attachment: Attachment }) {
    const fileUrl = `${API_BASE}/files/${attachment.file_id}`;
    const isImage = attachment.mime_type.startsWith('image/');
    const isPdf = attachment.mime_type === 'application/pdf';

    if (isImage) {
        return (
            <a href={fileUrl} target="_blank" rel="noopener noreferrer">
                <img
                    src={fileUrl}
                    alt={attachment.filename || 'Attached image'}
                    style={{
                        maxWidth: '200px',
                        maxHeight: '150px',
                        borderRadius: '6px',
                        border: '1px solid #e5e7eb',
                        objectFit: 'cover',
                    }}
                />
            </a>
        );
    }

    if (isPdf) {
        return (
            <a
                href={fileUrl}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 12px',
                    backgroundColor: '#f3f4f6',
                    borderRadius: '6px',
                    border: '1px solid #e5e7eb',
                    textDecoration: 'none',
                    color: '#374151',
                    fontSize: '13px',
                }}
            >
                📄 {attachment.filename || 'Document.pdf'}
            </a>
        );
    }

    return (
        <a
            href={fileUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 12px',
                backgroundColor: '#f3f4f6',
                borderRadius: '6px',
                border: '1px solid #e5e7eb',
                textDecoration: 'none',
                color: '#374151',
                fontSize: '13px',
            }}
        >
            📎 {attachment.filename || 'Attachment'}
        </a>
    );
}

