'use client';

import { MessageData } from '@/types';
import ReactMarkdown from 'react-markdown';
import { useState } from 'react';

export default function MessageBubble({
    message,
    onEdit,
    onDelete
}: {
    message: MessageData;
    onEdit?: (id: string, content: string) => void;
    onDelete?: (id: string) => void;
}) {
    const isAssistant = message.role === 'assistant';
    const [isEditing, setIsEditing] = useState(false);
    const [editContent, setEditContent] = useState(message.content);
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    const handleSaveEdit = () => {
        if (onEdit && editContent.trim() !== message.content) {
            onEdit(message._id.toString(), editContent);
        }
        setIsEditing(false);
        setIsMenuOpen(false);
    };

    return (
        <div className={`flex w-full mb-6 ${isAssistant ? 'justify-start' : 'justify-end'} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
            <div className={`max-w-[85%] md:max-w-[70%] flex flex-col ${isAssistant ? 'items-start' : 'items-end'}`}>
                <div className={`flex items-center space-x-2 mb-1 px-2`}>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                        {isAssistant ? (`AI ${message.aiProvider === 'gemini' ? 'Gemini' : 'OpenAI'}`) : 'You'}
                    </span>
                    <span className="text-[10px] text-slate-300">
                        {new Date(message.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                </div>

                <div className="relative group">
                    <div className={`
            px-4 py-3 rounded-2xl shadow-sm
            ${isAssistant
                            ? 'bg-white border border-slate-100 text-slate-800 rounded-tl-none'
                            : 'bg-indigo-600 text-white rounded-tr-none'
                        }
          `}>
                        {isEditing ? (
                            <div className="space-y-2 min-w-[300px]">
                                <textarea
                                    className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-slate-800 text-sm focus:ring-1 focus:ring-indigo-400 outline-none"
                                    value={editContent}
                                    onChange={(e) => setEditContent(e.target.value)}
                                    rows={3}
                                    autoFocus
                                />
                                <div className="flex justify-end space-x-2">
                                    <button
                                        onClick={() => setIsEditing(false)}
                                        className="px-3 py-1 text-xs font-medium text-slate-500 hover:text-slate-700"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={handleSaveEdit}
                                        className="px-3 py-1 text-xs font-bold bg-indigo-500 text-white rounded-md"
                                    >
                                        Save
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <div className="prose prose-sm max-w-none prose-slate prose-headings:text-indigo-600 prose-a:text-indigo-500">
                                <ReactMarkdown>{message.content}</ReactMarkdown>
                            </div>
                        )}
                    </div>

                    {!isAssistant && !isEditing && (
                        <div className={`absolute top-0 -left-10 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col space-y-1`}>
                            <button
                                onClick={() => setIsEditing(true)}
                                className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-indigo-600 transition-colors"
                                title="Edit message"
                            >
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                            </button>
                            <button
                                onClick={() => onDelete && onDelete(message._id.toString())}
                                className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-red-600 transition-colors"
                                title="Delete message"
                            >
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
