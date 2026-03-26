import { Document } from 'mongoose';

// User types removed

// Conversation types
export interface ConversationBase {
  userId: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  lastMessageAt: Date;
}

export interface ConversationData extends ConversationBase {
  _id: string;
}

export interface IConversation extends Document, ConversationBase { }

// Message types
export interface MessageBase {
  conversationId: string;
  role: 'user' | 'assistant';
  content: string;
  aiProvider?: 'openai' | 'gemini';
  createdAt: Date;
}

export interface MessageData extends MessageBase {
  _id: string;
}

export interface IMessage extends Document, MessageBase { }

// FAQ types
export interface FAQBase {
  question: string;
  answer: string;
  embedding?: number[];
  category?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface IFAQ extends Document, FAQBase { }

// API Request/Response types
export interface SendMessageRequest {
  conversationId?: string;
  content: string;
  aiProvider: 'openai' | 'gemini';
}

export interface SendMessageResponse {
  userMessage: IMessage;
  aiMessage: IMessage;
  conversation: IConversation;
}

export interface ConversationWithMessages extends IConversation {
  messages: IMessage[];
}

// Component prop types
export interface MessageBubbleProps {
  message: MessageData;
  onEdit?: (id: string, content: string) => void;
  onDelete?: (id: string) => void;
}

export interface ChatInterfaceProps {
  conversationId?: string;
}

export interface ConversationSidebarProps {
  conversations: ConversationData[];
  activeConversationId?: string;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string) => void;
}

export interface MessageInputProps {
  onSend: (content: string, provider: 'openai' | 'gemini') => void;
  isLoading?: boolean;
}
