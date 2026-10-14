// Theme
export { AgentThemeProvider, AgentThemeContext } from './theme/AgentThemeProvider.js';
export type { AgentThemeContextValue, ThemeMode } from './theme/AgentThemeProvider.js';
export { useAgentTheme } from './theme/useAgentTheme.js';
export { lightTheme, darkTheme } from './theme/defaultTheme.js';

// Main Component
export { AgentChat } from './components/AgentChat/AgentChat.js';
export type { AgentChatProps } from './components/AgentChat/AgentChat.js';

// Chat Panel
export { ChatPanel } from './components/ChatPanel/ChatPanel.js';
export { ChatHeader } from './components/ChatPanel/ChatHeader.js';
export { MessageList } from './components/ChatPanel/MessageList.js';

// Thread Sidebar
export { ThreadSidebar } from './components/ThreadSidebar/ThreadSidebar.js';
export { ThreadListItem } from './components/ThreadSidebar/ThreadListItem.js';

// Message Components
export { MessageCard } from './components/Message/MessageCard.js';
export { MessageHeader } from './components/Message/MessageHeader.js';
export { MessageContent } from './components/Message/MessageContent.js';
export { AttachmentGallery } from './components/Message/AttachmentGallery.js';

// Message Block Components
export { TextBlock } from './components/MessageBlock/TextBlock.js';
export { ReasoningBlock } from './components/MessageBlock/ReasoningBlock.js';
export { ToolCallBlock } from './components/MessageBlock/ToolCallBlock.js';
export { ErrorBlock } from './components/MessageBlock/ErrorBlock.js';

// Input Components
export { MessageInput } from './components/MessageInput/MessageInput.js';
export { AttachButton } from './components/MessageInput/AttachButton.js';
export { PendingAttachments } from './components/MessageInput/PendingAttachments.js';

// Audio Controls
export { SpeakButton, PushToTalkButton, CopyButton, ImageActions } from './components/AudioControls/index.js';

// Markdown
export { MarkdownProvider, useMarkdownContext, MarkdownRenderer, StoredImage } from './markdown/index.js';
export type { CustomComponentProps, CustomComponentRegistry } from './markdown/index.js';

// Utilities
export { formatTimestamp, formatFullTimestamp } from './utils/formatTime.js';

// Icons (for custom usage)
export {
    VolumeUpIcon,
    VolumeOffIcon,
    MicIcon,
    MicOffIcon,
    ContentCopyIcon,
    CheckIcon,
    DownloadIcon,
} from './utils/icons.js';

