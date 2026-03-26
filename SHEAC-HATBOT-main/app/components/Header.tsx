'use client';

import Link from 'next/link';
import { useState } from 'react';

export default function Header() {
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    return (
        <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16 items-center">
                    <div className="flex items-center">
                        <Link href="/" className="flex items-center space-x-2 group">
                            <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-200 group-hover:scale-105 transition-transform duration-200">
                                <span className="text-white font-bold text-xl">S</span>
                            </div>
                            <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-violet-600">
                                SheaBot
                            </span>
                        </Link>
                    </div>

                    <nav className="hidden md:flex items-center space-x-8">
                        <Link href="/" className="text-slate-600 hover:text-indigo-600 font-medium transition-colors">
                            Home
                        </Link>
                        <Link href="/chat" className="text-slate-600 hover:text-indigo-600 font-medium transition-colors">
                            Chat
                        </Link>
                    </nav>

                    {/* Mobile menu button */}
                    <div className="md:hidden flex items-center">
                        <button
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                            className="text-slate-600 hover:text-indigo-600 focus:outline-none"
                        >
                            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                {isMenuOpen ? (
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                ) : (
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                )}
                            </svg>
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile menu */}
            {isMenuOpen && (
                <div className="md:hidden bg-white border-t border-slate-100 px-4 pt-2 pb-6 space-y-3">
                    <Link href="/" className="block px-3 py-2 text-slate-600 font-medium border-b border-slate-50">
                        Home
                    </Link>
                    <Link href="/chat" className="block px-3 py-2 text-slate-600 font-medium border-b border-slate-50">
                        Chat
                    </Link>
                </div>
            )}
        </header>
    );
}
