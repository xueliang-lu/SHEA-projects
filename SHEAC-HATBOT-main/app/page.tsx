'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function LandingPage() {
  const router = useRouter();

  // Auth modals removed for "free for all" mode

  return (
    <div className="relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full -z-10 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-200/30 blur-[120px] rounded-full"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-violet-200/30 blur-[120px] rounded-full"></div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-32">
        <div className="text-center space-y-8 max-w-4xl mx-auto">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-600 text-sm font-semibold animate-in fade-in slide-in-from-bottom-4 duration-700">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
            <span>Version 2.0 is here</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-slate-900 animate-in fade-in slide-in-from-bottom-6 duration-700 delay-100">
            Chat with AI, <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-violet-600">Simpler & Smarter</span>
          </h1>

          <p className="text-xl text-slate-600 max-w-2xl mx-auto animate-in fade-in slide-in-from-bottom-8 duration-700 delay-200">
            The next generation of conversational AI. Powered by OpenAI and Gemini, with a built-in RAG system for personalized FAQ knowledge.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-4 pt-8 animate-in fade-in slide-in-from-bottom-10 duration-700 delay-300">
            <Link
              href="/chat"
              className="w-full sm:w-auto px-8 py-4 bg-indigo-600 text-white rounded-2xl font-bold text-lg shadow-xl shadow-indigo-200 hover:bg-indigo-700 hover:-translate-y-1 transition-all duration-200 active:scale-95 text-center"
            >
              Start Chatting Now
            </Link>
          </div>

          <div className="pt-20 animate-in fade-in zoom-in-95 duration-1000 delay-500">
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-violet-600 rounded-2xl blur opacity-20 group-hover:opacity-30 transition duration-1000 group-hover:duration-200"></div>
              <div className="relative bg-white rounded-2xl border border-slate-100 shadow-2xl overflow-hidden aspect-video max-w-5xl mx-auto flex items-center justify-center text-slate-300">
                <div className="text-center p-10">
                  <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4 border border-slate-100">
                    <svg className="w-10 h-10 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                  </div>
                  <h3 className="text-2xl font-bold text-slate-800">Experience ChatGPT-like Interface</h3>
                  <p className="text-slate-500 mt-2">Sign in to start chatting with our intelligent bots.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <section className="py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900">Why Choose SheaBot?</h2>
            <p className="text-slate-600 mt-4">Powerful features designed for the best chat experience.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { title: "Dual AI Engines", desc: "Toggle between OpenAI's GPT-4o and Google's Gemini Flash for the best perspective.", icon: "⚡" },
              { title: "FAQ Knowledge Base", desc: "Our RAG system reads your FAQ files to provide accurate company-specific answers.", icon: "📚" },
              { title: "Full History", desc: "Access your entire chat history anytime. Search, edit, and manage your conversations.", icon: "🕒" }
            ].map((f, i) => (
              <div key={i} className="bg-white p-8 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow">
                <div className="text-4xl mb-4">{f.icon}</div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">{f.title}</h3>
                <p className="text-slate-600">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Auth Modals Removed */}
    </div>
  );
}