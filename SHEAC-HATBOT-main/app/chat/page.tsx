'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import ConversationSidebar from '@/app/components/chat/ConversationSidebar';
import MessageBubble from '@/app/components/chat/MessageBubble';
import MessageInput from '@/app/components/chat/MessageInput';
import { ConversationData, MessageData } from '@/types';

export default function ChatPage() {
    const router = useRouter();

    const [conversations, setConversations] = useState<ConversationData[]>([]);
    const [activeConversationId, setActiveConversationId] = useState<string | undefined>();
    const [messages, setMessages] = useState<MessageData[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isHistoryLoading, setIsHistoryLoading] = useState(true);

    const messageEndRef = useRef<HTMLDivElement>(null);

    // Fetch conversations on mount
    useEffect(() => {
        fetchConversations();
    }, []);

    // Scroll to bottom on new messages
    useEffect(() => {
        messageEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isLoading]);

    const fetchConversations = async () => {
        setIsHistoryLoading(true);
        try {
            const res = await fetch('/api/conversations');
            if (res.ok) {
                const data = await res.json();
                setConversations(data);
            }
        } catch (err) {
            console.error('Failed to fetch conversations', err);
        } finally {
            setIsHistoryLoading(false);
        }
    };

    const fetchMessages = async (id: string) => {
        try {
            const res = await fetch(`/api/conversations/${id}`);
            if (res.ok) {
                const data = await res.json();
                setMessages(data.messages || []);
                setActiveConversationId(id);
            }
        } catch (err) {
            console.error('Failed to fetch messages', err);
        }
    };

    const handleNewConversation = () => {
        setActiveConversationId(undefined);
        setMessages([]);
    };

    const handleDeleteConversation = async (id: string) => {
        if (confirm('Are you sure you want to delete this conversation?')) {
            try {
                const res = await fetch(`/api/conversations/${id}`, { method: 'DELETE' });
                if (res.ok) {
                    setConversations(conversations.filter(c => c._id.toString() !== id));
                    if (activeConversationId === id) {
                        handleNewConversation();
                    }
                }
            } catch (err) {
                console.error('Failed to delete conversation', err);
            }
        }
    };

    const handleSendMessage = async (content: string, aiProvider: 'openai' | 'gemini') => {
        setIsLoading(true);

        // Optimistic update for user message
        const tempUserMessage: any = {
            _id: 'temp-' + Date.now(),
            role: 'user',
            content,
            createdAt: new Date(),
        };
        setMessages(prev => [...prev, tempUserMessage]);

        try {
            const res = await fetch('/api/messages', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    conversationId: activeConversationId,
                    content,
                    aiProvider,
                }),
            });

            if (res.ok) {
                const data = await res.json();

                // Update messages with real ones from server
                setMessages(prev => {
                    const filtered = prev.filter(m => !m._id.toString().startsWith('temp-'));
                    return [...filtered, data.userMessage, data.assistantMessage];
                });

                // Update active conversation ID if it was a new one
                if (!activeConversationId) {
                    setActiveConversationId(data.conversationId);
                    fetchConversations(); // Refresh sidebar to show new conversation
                } else {
                    // Move current conversation to top of sidebar
                    setConversations(prev => {
                        const current = prev.find(c => c._id.toString() === data.conversationId);
                        const others = prev.filter(c => c._id.toString() !== data.conversationId);
                        if (current) return [current, ...others];
                        return prev;
                    });
                }
            } else {
                let errorMessage = 'Failed to send message';
                try {
                    const errorData = await res.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (e) {
                    // Ignore json parse error
                }
                throw new Error(errorMessage);
            }
        } catch (err: any) {
            console.error('Send message error:', err);
            // Remove the temp message on error? Or show error state.
            alert(`Error: ${err.message || 'Failed to get AI response. Please try again.'}`);
        } finally {
            setIsLoading(false);
        }
    };

    const handleEditMessage = async (id: string, content: string) => {
        try {
            const res = await fetch(`/api/messages/${id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content }),
            });

            if (res.ok) {
                setMessages(prev => prev.map(m => m._id.toString() === id ? { ...m, content } : m));
            }
        } catch (err) {
            console.error('Edit message error:', err);
        }
    };

    const handleDeleteMessage = async (id: string) => {
        if (confirm('Delete this message?')) {
            try {
                const res = await fetch(`/api/messages/${id}`, { method: 'DELETE' });
                if (res.ok) {
                    setMessages(prev => prev.filter(m => m._id.toString() !== id));
                }
            } catch (err) {
                console.error('Delete message error:', err);
            }
        }
    };

    // Loading state removed


    return (
        <div className="flex h-[calc(100vh-64px)] overflow-hidden">
            <ConversationSidebar
                conversations={conversations}
                activeConversationId={activeConversationId}
                onSelectConversation={fetchMessages}
                onNewConversation={handleNewConversation}
                onDeleteConversation={handleDeleteConversation}
            />

            <main className="flex-grow flex flex-col min-w-0 bg-slate-50 relative">
                <div className="flex-grow overflow-y-auto px-4 md:px-8 py-6">
                    <div className="max-w-4xl mx-auto">
                        {messages.length === 0 && !isLoading ? (
                            <div className="h-[60vh] flex flex-col items-center justify-center text-center space-y-6">
                                <div className="w-20 h-20 bg-indigo-100 rounded-2xl flex items-center justify-center text-indigo-600">
                                    <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                                    </svg>
                                </div>
                                <div>
                                    <h2 className="text-2xl font-bold text-slate-800">Hello, Guest!</h2>
                                    <p className="text-slate-500 mt-2">How can SheaBot help you today?</p>
                                </div>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-xl">
                                    {[
                                        "What are the office hours?",
                                        "How do I reset my password?",
                                        "Tell me about SheaBot's history",
                                        "What features are available?"
                                    ].map((suggestion, i) => (
                                        <button
                                            key={i}
                                            onClick={() => handleSendMessage(suggestion, 'openai')}
                                            className="p-3 bg-white border border-slate-200 rounded-xl text-sm text-slate-600 hover:border-indigo-400 hover:text-indigo-600 text-left transition-all"
                                        >
                                            {suggestion}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <>
                                {messages.map((msg) => (
                                    <MessageBubble
                                        key={msg._id.toString()}
                                        message={msg}
                                        onEdit={handleEditMessage}
                                        onDelete={handleDeleteMessage}
                                    />
                                ))}
                                {isLoading && (
                                    <div className="flex justify-start mb-6 animate-pulse">
                                        <div className="bg-white border border-slate-100 rounded-2xl rounded-tl-none px-4 py-3 flex space-x-2">
                                            <div className="w-2 h-2 bg-slate-200 rounded-full animate-bounce"></div>
                                            <div className="w-2 h-2 bg-slate-200 rounded-full animate-bounce delay-75"></div>
                                            <div className="w-2 h-2 bg-slate-200 rounded-full animate-bounce delay-150"></div>
                                        </div>
                                    </div>
                                )}
                                <div ref={messageEndRef} />
                            </>
                        )}
                    </div>
                </div>

                <MessageInput onSend={handleSendMessage} isLoading={isLoading} />
            </main>
        </div>
    );
}
