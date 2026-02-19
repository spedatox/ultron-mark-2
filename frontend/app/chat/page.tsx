"use client";

import { useState, useEffect, useRef } from "react";
import { sendChatMessage, fetchSessions, fetchSessionMessages, uploadFile, streamChat } from "@/lib/api";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Message {
  id?: number;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  attachment_url?: string;
}

interface Session {
  id: number;
  title: string;
  updated_at: string;
}

export default function ChatPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    // Responsive sidebar: close on mobile by default
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setIsSidebarOpen(false);
      }
    };
    
    // Check on mount
    if (window.innerWidth < 768) {
      setIsSidebarOpen(false);
    }

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    if (currentSessionId) {
      loadMessages(currentSessionId);
    } else {
        // Reset to welcome message if no session selected
        setMessages([{
            role: "assistant",
            content: "Ultron Mark II Online. Select a memory archive or initialize a new directive.",
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }]);
    }
  }, [currentSessionId]);

  useEffect(() => {
    smartScroll();
  }, [messages]);

  const smartScroll = () => {
    const container = scrollContainerRef.current;
    if (!container) return;

    const lastMsg = messages[messages.length - 1];
    // Always scroll for user messages or if it's the very first load
    if (lastMsg?.role === "user" || messages.length <= 1) {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
        return;
    }

    // For AI messages (streaming), only scroll if user is near the bottom
    const distanceToBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
    if (distanceToBottom < 200) {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  };

  async function loadSessions() {
    try {
      const data = await fetchSessions();
      setSessions(data);
    } catch (error) {
      console.error("Failed to load sessions", error);
    }
  }

  async function loadMessages(sessionId: number) {
    try {
      const data = await fetchSessionMessages(sessionId);
      // Transform backend data to UI format
      const uiMessages = data.map((m: any) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        timestamp: new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        attachment_url: m.attachment_url
      }));
      setMessages(uiMessages);
    } catch (error) {
      console.error("Failed to load messages", error);
    }
  }

  async function handleNewSession() {
    setCurrentSessionId(null);
    setMessages([{
        role: "assistant",
        content: "New sequence initialized. Awaiting input.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }]);
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files[0]) {
        const file = e.target.files[0];
        try {
            const res = await uploadFile(file);
            // For now, we just append the file URL to the input or send it immediately
            // Let's append a marker to the input
            setInput(prev => prev + ` [Attached: ${res.filename}] `);
        } catch (error) {
            alert("Upload failed");
        }
    }
  }

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg: Message = {
      role: "user",
      content: input,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      // Create placeholder for bot message
      const botMsg: Message = {
        role: "assistant",
        content: "",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, botMsg]);

      // Use streaming API
      const res = await streamChat(userMsg.content, currentSessionId || undefined);
      
      if (!res.body) throw new Error("No response body");
      
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let accumulatedContent = "";

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        const chunkValue = decoder.decode(value, { stream: !done });
        accumulatedContent += chunkValue;
        
        setMessages(prev => {
            const newMessages = [...prev];
            const lastMsg = newMessages[newMessages.length - 1];
            if (lastMsg.role === "assistant") {
                lastMsg.content = accumulatedContent;
            }
            return newMessages;
        });
      }

      // If this was a new session, refresh sessions list
      if (!currentSessionId) {
        const sessionsData = await fetchSessions();
        setSessions(sessionsData);
        if (sessionsData.length > 0) {
             setCurrentSessionId(sessionsData[0].id);
        }
      }
      
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "System Malfunction: Connection interrupted.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed top-20 bottom-0 left-0 right-0 flex bg-white dark:bg-[#0a0f1a] overflow-hidden">
      {/* Mobile Backdrop */}
      {isSidebarOpen && (
        <div 
            className="fixed inset-0 bg-black/20 dark:bg-black/40 z-10 md:hidden"
            onClick={() => setIsSidebarOpen(false)}
        ></div>
      )}

      {/* Sidebar (Memory Archives) */}
      <div className={`${isSidebarOpen ? 'w-64 border-r' : 'w-0'} transition-all duration-300 border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-[#0f172a] flex flex-col overflow-hidden absolute md:relative z-20 h-full`}>
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center min-w-[16rem]">
            <button 
                onClick={handleNewSession}
                className="flex-1 flex items-center gap-2 px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 hover:border-cyan-400 text-slate-600 dark:text-slate-300 hover:text-cyan-600 dark:hover:text-cyan-400 transition-all rounded-sm group"
            >
                <span className="text-lg font-light">+</span>
                <span className="text-xs font-bold uppercase tracking-wider">New Sequence</span>
            </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-2 space-y-1 min-w-[16rem]">
            <div className="px-2 py-2 text-[10px] font-mono text-slate-400 dark:text-slate-500 uppercase tracking-widest">Memory Archives</div>
            {sessions.map(session => (
                <button
                    key={session.id}
                    onClick={() => setCurrentSessionId(session.id)}
                    className={`w-full text-left px-3 py-3 rounded-sm text-xs font-medium truncate transition-colors border-l-2 ${
                        currentSessionId === session.id 
                        ? 'bg-white dark:bg-slate-800 border-cyan-500 text-cyan-700 dark:text-cyan-400 shadow-sm' 
                        : 'border-transparent text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100'
                    }`}
                >
                    {session.title}
                </button>
            ))}
        </div>
        
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 min-w-[16rem]">
            <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-500 dark:text-slate-300 font-bold text-xs">
                    SP
                </div>
                <div className="flex-1 min-w-0">
                    <div className="text-xs font-bold text-slate-900 dark:text-slate-100 truncate">Ahmet Erol Bayrak</div>
                    <div className="text-[10px] text-slate-500 dark:text-slate-400 truncate">Admin Access</div>
                </div>
            </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative">
        {/* Toggle Sidebar Button (Mobile/Desktop) */}
        <button 
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="absolute top-4 left-4 z-10 p-2 text-slate-400 hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors"
        >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
        </button>

        {/* Messages */}
        <div ref={scrollContainerRef} className="flex-1 overflow-y-auto p-4 sm:p-8 space-y-6 scroll-smooth">
          {messages.filter(msg => msg.content || msg.role === "user").map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-center"}`}>
              <div className={`max-w-3xl w-full flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                
                {/* Avatar */}
                <div className={`w-8 h-8 rounded-sm flex-shrink-0 flex items-center justify-center text-xs font-bold ${
                    msg.role === "user" ? "bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300" : "bg-cyan-500 text-white"
                }`}>
                    {msg.role === "user" ? "AEB" : "U"}
                </div>

                {/* Content */}
                <div className={`flex-1 space-y-1 ${msg.role === "user" ? "text-right" : "text-left"}`}>
                    <div className="text-[10px] font-mono text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                        {msg.role === "user" ? "User Input" : "Ultron Response"} • {msg.timestamp}
                    </div>
                    <div className={`prose prose-sm dark:prose-invert max-w-none ${msg.role === "user" ? "text-slate-800 dark:text-slate-200" : "text-slate-600 dark:text-slate-300"}`}>
                        <ReactMarkdown 
                            remarkPlugins={[remarkGfm]}
                            components={{
                                // ChatGPT-style heading styling
                                h1: ({node, ...props}) => <h1 className="text-2xl font-bold text-slate-900 dark:text-white mt-6 mb-4 pb-2 border-b border-slate-200 dark:border-slate-700" {...props} />,
                                h2: ({node, ...props}) => <h2 className="text-xl font-bold text-slate-900 dark:text-white mt-5 mb-3" {...props} />,
                                h3: ({node, ...props}) => <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mt-4 mb-2" {...props} />,
                                h4: ({node, ...props}) => <h4 className="text-base font-semibold text-slate-800 dark:text-slate-100 mt-3 mb-2" {...props} />,
                                // Paragraphs
                                p: ({node, ...props}) => <p className="whitespace-pre-wrap leading-7 mb-4 text-slate-700 dark:text-slate-300" {...props} />,
                                // Links
                                a: ({node, ...props}) => <a className="text-cyan-600 dark:text-cyan-400 hover:text-cyan-500 dark:hover:text-cyan-300 underline underline-offset-2 transition-colors" {...props} />,
                                // Lists
                                ul: ({node, ...props}) => <ul className="list-disc pl-6 mb-4 space-y-2 marker:text-slate-400 dark:marker:text-slate-500" {...props} />,
                                ol: ({node, ...props}) => <ol className="list-decimal pl-6 mb-4 space-y-2 marker:text-slate-500 dark:marker:text-slate-400" {...props} />,
                                li: ({node, ...props}) => <li className="leading-7 text-slate-700 dark:text-slate-300" {...props} />,
                                // Inline code
                                code: ({node, className, ...props}) => {
                                    const isCodeBlock = className?.includes('language-');
                                    if (isCodeBlock) {
                                        return <code className={`${className} block`} {...props} />;
                                    }
                                    return <code className="bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded text-[13px] font-mono text-pink-600 dark:text-pink-400 border border-slate-200 dark:border-slate-700" {...props} />;
                                },
                                // Code blocks
                                pre: ({node, ...props}) => (
                                    <pre className="bg-slate-900 dark:bg-black text-slate-100 p-4 rounded-xl overflow-x-auto mb-4 text-[13px] font-mono leading-6 border border-slate-700 dark:border-slate-800 shadow-lg" {...props} />
                                ),
                                // Blockquotes
                                blockquote: ({node, ...props}) => (
                                    <blockquote className="border-l-4 border-cyan-500 dark:border-cyan-400 pl-4 py-1 my-4 bg-slate-50 dark:bg-slate-800/50 rounded-r-lg italic text-slate-600 dark:text-slate-400" {...props} />
                                ),
                                // Tables
                                table: ({node, ...props}) => (
                                    <div className="overflow-x-auto mb-4">
                                        <table className="min-w-full border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden" {...props} />
                                    </div>
                                ),
                                thead: ({node, ...props}) => <thead className="bg-slate-100 dark:bg-slate-800" {...props} />,
                                th: ({node, ...props}) => <th className="px-4 py-2 text-left text-sm font-semibold text-slate-800 dark:text-slate-200 border-b border-slate-200 dark:border-slate-700" {...props} />,
                                td: ({node, ...props}) => <td className="px-4 py-2 text-sm text-slate-700 dark:text-slate-300 border-b border-slate-100 dark:border-slate-800" {...props} />,
                                tr: ({node, ...props}) => <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors" {...props} />,
                                // Horizontal rule
                                hr: ({node, ...props}) => <hr className="my-6 border-slate-200 dark:border-slate-700" {...props} />,
                                // Strong/Bold
                                strong: ({node, ...props}) => <strong className="font-semibold text-slate-900 dark:text-white" {...props} />,
                                // Emphasis/Italic
                                em: ({node, ...props}) => <em className="italic text-slate-700 dark:text-slate-300" {...props} />,
                            }}
                        >
                            {msg.content}
                        </ReactMarkdown>
                        {msg.attachment_url && (
                            <div className="mt-2 p-2 border border-slate-200 dark:border-slate-700 rounded bg-slate-50 dark:bg-slate-800 text-xs font-mono text-cyan-600 dark:text-cyan-400">
                                Attachment: {msg.attachment_url}
                            </div>
                        )}
                    </div>
                </div>
              </div>
            </div>
          ))}
          {loading && messages[messages.length - 1]?.content === "" && (
             <div className="flex justify-center">
                <div className="max-w-3xl w-full flex gap-4">
                    <div className="w-8 h-8 rounded-sm bg-cyan-500 flex items-center justify-center">
                        <div className="w-2 h-2 bg-white rounded-full animate-ping"></div>
                    </div>
                    <div className="flex-1 pt-1">
                        <div className="h-2 w-24 bg-slate-100 dark:bg-slate-800 rounded animate-pulse"></div>
                    </div>
                </div>
             </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-white dark:bg-[#0a0f1a] border-t border-slate-100 dark:border-slate-800">
          <div className="max-w-3xl mx-auto relative">
            <form onSubmit={handleSend} className="relative flex items-end gap-2 p-3 border border-slate-200 dark:border-slate-700 rounded-lg shadow-sm focus-within:border-cyan-400 focus-within:ring-1 focus-within:ring-cyan-100 dark:focus-within:ring-cyan-900 transition-all bg-white dark:bg-slate-900">
                
                {/* File Upload Button */}
                <button 
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="p-2 text-slate-400 hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" /></svg>
                </button>
                <input 
                    type="file" 
                    ref={fileInputRef} 
                    className="hidden" 
                    onChange={handleFileUpload}
                />

                <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleSend(e);
                        }
                    }}
                    placeholder="Send a message to Ultron..."
                    className="flex-1 max-h-32 bg-transparent border-none focus:ring-0 p-0 text-sm text-slate-800 dark:text-slate-200 placeholder:text-slate-400 dark:placeholder:text-slate-500 resize-none py-2"
                    rows={1}
                />

                <button
                    type="submit"
                    disabled={loading || !input.trim()}
                    className="p-2 bg-cyan-500 text-white rounded-md hover:bg-cyan-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" /></svg>
                </button>
            </form>
            <div className="text-center mt-2">
                <span className="text-[10px] text-slate-400 dark:text-slate-500">Ultron Mark II can make mistakes. Verify important info.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
