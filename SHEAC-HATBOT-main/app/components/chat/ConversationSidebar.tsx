'use client';

import { ConversationData } from '@/types';
import { useState } from 'react';

export default function ConversationSidebar({
    conversations,
    activeConversationId,
    onSelectConversation,
    onNewConversation,
    onDeleteConversation
}: {
    conversations: ConversationData[];
    activeConversationId?: string;
    onSelectConversation: (id: string) => void;
    onNewConversation: () => void;
    onDeleteConversation: (id: string) => void;
}) {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    const handleSelect = (id: string) => {
        onSelectConversation(id);
        // Auto-close on mobile after selection
        if (window.innerWidth < 768) {
            setIsSidebarOpen(false);
        }
    };

    const handleNew = () => {
        onNewConversation();
        if (window.innerWidth < 768) {
            setIsSidebarOpen(false);
        }
    };

    return (
        <>
            {/* Mobile Backdrop */}
            {isSidebarOpen && (
                <div
                    className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-20 md:hidden"
                    onClick={() => setIsSidebarOpen(false)}
                />
            )}

            {/* Mobile toggle - now in top corner for better reach/standard UI */}
            <div className="md:hidden fixed top-4 left-4 z-40">
                <button
                    onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                    className="p-2.5 bg-white border border-slate-200 rounded-xl shadow-xl text-indigo-600 active:scale-95 transition-transform"
                >
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        {isSidebarOpen ? (
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        ) : (
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h8m-8 6h16" />
                        )}
                    </svg>
                </button>
            </div>

            <aside className={`
                fixed md:relative inset-y-0 left-0 z-30 w-72 bg-white border-r border-slate-200 
                transition-transform duration-300 ease-in-out shadow-2xl md:shadow-none
                ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
            `}>
                <div className="h-full flex flex-col">
                    <div className="p-4 pt-20 md:pt-4 space-y-4">
                        <button
                            onClick={handleNew}
                            className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-indigo-50 text-indigo-700 rounded-xl font-bold border border-indigo-100 hover:bg-indigo-100 transition-colors group"
                        >
                            <svg className="w-5 h-5 group-hover:rotate-90 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                            </svg>
                            <span>New Conversation</span>
                        </button>
                    </div>

                    <div className="flex-grow overflow-y-auto px-3 py-2 space-y-1">
                        <h3 className="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">History</h3>
                        {conversations.length === 0 ? (
                            <div className="px-3 py-4 text-center">
                                <p className="text-sm text-slate-400">No conversations yet.</p>
                            </div>
                        ) : (
                            conversations.map((conv) => (
                                <div
                                    key={conv._id.toString()}
                                    className="group relative"
                                >
                                    <button
                                        onClick={() => handleSelect(conv._id.toString())}
                                        className={`
                                            w-full text-left px-3 py-2.5 rounded-xl transition-all flex items-center space-x-3
                                            ${activeConversationId === conv._id.toString()
                                                ? 'bg-indigo-50 text-indigo-700 border-l-4 border-indigo-600'
                                                : 'text-slate-500 hover:bg-slate-50 hover:text-slate-700'}
                                        `}
                                    >
                                        <svg className={`w-4 h-4 ${activeConversationId === conv._id.toString() ? 'text-indigo-600' : 'text-slate-300'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                                        </svg>
                                        <span className="truncate text-sm font-medium pr-6">{conv.title}</span>
                                    </button>

                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onDeleteConversation(conv._id.toString());
                                        }}
                                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 opacity-100 lg:opacity-0 lg:group-hover:opacity-100 hover:bg-red-50 hover:text-red-500 rounded-lg transition-all text-slate-300"
                                    >
                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                        </svg>
                                    </button>
                                </div>
                            ))
                        )}
                    </div>

                    <div className="p-4 border-t border-slate-100 bg-slate-50">
                        <div className="flex items-center space-x-3 text-slate-500">
                            <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-xs">
                                S
                            </div>
                            <div className="text-xs">
                                <p className="font-bold text-slate-700">Premium Plan</p>
                                <p className="text-slate-400">Unlimited AI usage</p>
                            </div>
                        </div>
                    </div>
                </div>
            </aside>
        </>
    );
}
