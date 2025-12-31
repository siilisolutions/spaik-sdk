import { MarkdownRenderer } from '../../markdown/MarkdownRenderer';

interface Props {
    content: string;
}

export function TextBlock({ content }: Props) {
    if (!content) return null;

    return <MarkdownRenderer content={content} />;
}
