'use client';

import { useState, useRef, useEffect } from 'react';

export default function MessageInput({
    onSend,
    isLoading
}: {
    onSend: (content: string, provider: 'openai' | 'gemini') => void;
    isLoading?: boolean;
}) {
    const [content, setContent] = useState('');
    const [provider, setProvider] = useState<'openai' | 'gemini'>('openai');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleSend = () => {
        if (content.trim() && !isLoading) {
            onSend(content.trim(), provider);
            setContent('');
        }
    };

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
        }
    }, [content]);

    return (
        <div className="bg-white border-t border-slate-200 p-4 md:p-6 pb-8">
            <div className="max-w-4xl mx-auto">
                <div className="relative group">
                    <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500/20 to-violet-500/20 rounded-2xl blur opacity-0 group-focus-within:opacity-100 transition duration-500"></div>
                    <div className="relative bg-slate-50 border border-slate-200 focus-within:border-indigo-300 rounded-2xl transition-all duration-200 p-2 pl-4 flex flex-col items-stretch">

                        <div className="flex items-center space-x-2 mb-2 pt-1">
                            <button
                                onClick={() => setProvider('openai')}
                                className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all ${provider === 'openai' ? 'bg-indigo-600 text-white shadow-sm' : 'bg-slate-200 text-slate-500'}`}
                            >
                                GPT-4o (OpenAI)
                            </button>
                            <button
                                onClick={() => setProvider('gemini')}
                                className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all ${provider === 'gemini' ? 'bg-indigo-600 text-white shadow-sm' : 'bg-slate-200 text-slate-500'}`}
                            >
                                Gemini 2.0
                            </button>
                        </div>

                        <div className="flex items-end">
                            <textarea
                                ref={textareaRef}
                                className="flex-grow bg-transparent border-none focus:ring-0 outline-none p-0 pb-1 text-slate-800 placeholder:text-slate-400 resize-none min-h-[24px]"
                                placeholder="Ask anything or talk about the FAQs..."
                                rows={1}
                                value={content}
                                onChange={(e) => setContent(e.target.value)}
                                onKeyDown={handleKeyDown}
                            />

                            <button
                                onClick={handleSend}
                                disabled={!content.trim() || isLoading}
                                className={`
                    ml-2 p-2 rounded-xl transition-all flex items-center justify-center
                    ${content.trim() && !isLoading
                                        ? 'bg-indigo-600 text-white shadow-md hover:bg-indigo-700 active:scale-95'
                                        : 'bg-slate-200 text-slate-400 cursor-not-allowed'}
                  `}
                            >
                                {isLoading ? (
                                    <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                ) : (
                                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                                    </svg>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
                <p className="text-[10px] text-slate-400 mt-2 text-center uppercase tracking-widest font-semibold">
                    SheaBot can make mistakes. Check important info.
                </p>
            </div>
        </div>
    );
}
