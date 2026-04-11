import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, 
  Bot, 
  User, 
  History, 
  Settings, 
  Trash2, 
  Loader2, 
  Cpu, 
  Activity, 
  Info,
  ChevronRight,
  Maximize2,
  RefreshCw,
  ExternalLink,
  X
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './App.css';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: {
    status?: string;
    task?: string;
    tool?: string;
  };
}

interface UpdateChunk {
  type: 'status' | 'task' | 'tool' | 'answer';
  content: string;
}

const SUGGESTIONS = [
  "Who is currently present?",
  "Show me security events from today",
  "Any crowd density alerts?",
  "Summarize vehicle counts for this morning"
];

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isAnimatingText, setIsAnimatingText] = useState(false);
  const [activeProgress, setActiveProgress] = useState<{ type: string; content: string } | null>(null);
  const [typingText, setTypingText] = useState('');
  const [sessionId, setSessionId] = useState<string>(() => {
    const saved = localStorage.getItem('vf_session_id');
    if (saved) return saved;
    const newId = `sess_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('vf_session_id', newId);
    return newId;
  });

  const chatEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const [userHasScrolledUp, setUserHasScrolledUp] = useState(false);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const apiHost = 'http://localhost:9000'; // Target Manager API

  // Auto-scroll logic: Only scroll if user is already at bottom or just starting
  useEffect(() => {
    if (!userHasScrolledUp) {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, activeProgress, typingText]);

  const handleScroll = () => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 100;
    setUserHasScrolledUp(!isAtBottom);
  };

  const clearHistory = () => {
    setMessages([]);
    setActiveProgress(null);
    const newId = `sess_${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newId);
    localStorage.setItem('vf_session_id', newId);
  };

  const handleSubmit = async (e?: React.FormEvent, customQuery?: string) => {
    e?.preventDefault();
    const query = customQuery || input;
    if (!query.trim() || isTyping) return;

    // Add user message
    const userMsg: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: query,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);
    setActiveProgress({ type: 'status', content: '🤖 Initializing...' });

    try {
      const response = await fetch(`${apiHost}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, session_id: sessionId })
      });

      if (!response.body) throw new Error('No response body');
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantMsgContent = '';
      
      // Create early assistant message placeholder if we want to stream text
      // but the current server yields the full answer at once at the end.
      // However, we handle tools/status chunks here.

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const data: UpdateChunk = JSON.parse(line);
            
            if (data.type === 'status') {
              setActiveProgress({ type: 'status', content: data.content });
            } else if (data.type === 'task') {
              setActiveProgress({ type: 'task', content: data.content });
            } else if (data.type === 'tool') {
              setActiveProgress({ type: 'tool', content: data.content });
            } else if (data.type === 'answer') {
              assistantMsgContent = data.content;
              setIsAnimatingText(true);
              
              // Simulate typewriter effect
              let currentIdx = 0;
              const text = data.content;
              const interval = setInterval(() => {
                if (currentIdx <= text.length) {
                  setTypingText(text.slice(0, currentIdx));
                  currentIdx++;
                } else {
                  clearInterval(interval);
                  const assistantMsg: Message = {
                    id: (Date.now() + 1).toString(),
                    type: 'assistant',
                    content: text,
                    timestamp: new Date()
                  };
                  setMessages(prev => [...prev, assistantMsg]);
                  setTypingText('');
                  setIsAnimatingText(false);
                  setActiveProgress(null);
                  setIsTyping(false);
                }
              }, 15); // Adjust speed here (ms per char)
            }
          } catch (err) {
            console.error('Error parsing SSE chunk:', err, line);
          }
        }
      }
    } catch (err) {
      console.error('Fetch error:', err);
      const errorMsg: Message = {
        id: 'error-' + Date.now(),
        type: 'assistant',
        content: "❌ Sorry, I encountered an error connecting to the VisionFacts API. Please ensure the server is running on port 9000.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMsg]);
      setIsTyping(false);
    } finally {
      // We don't set setIsTyping(false) here because the typewriter effect is still running
      // it will be set to false inside the interval completion.
      setActiveProgress(null);
    }
  };

  return (
    <div className="flex h-screen w-full bg-slate-950 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-80 glass flex flex-col border-r border-slate-800">
        <div className="p-8 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Activity className="text-white" size={20} />
          </div>
          <div>
            <h1 className="text-xl font-bold font-outfit bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
              VisionFacts
            </h1>
            <p className="text-[10px] text-blue-400 tracking-widest uppercase font-bold">Analytical Assistant</p>
          </div>
        </div>

        <div className="p-4 flex flex-col gap-4">
           <button 
            onClick={clearHistory} 
            className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-blue-600 text-white hover:bg-blue-700 shadow-lg shadow-blue-500/20 transition-all font-semibold"
          >
            <RefreshCw size={16} />
            New Chat
          </button>
        </div>

        <nav className="flex-1 px-4 py-2 space-y-6">
          <section>
            <h3 className="px-4 text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">Current Session</h3>
            <div className="px-4 py-3 rounded-lg bg-slate-900/50 border border-slate-800 flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400">{sessionId}</span>
            </div>
          </section>

          <section>
            <h3 className="px-4 text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-4">Quick Analysis</h3>
            <div className="space-y-2">
              {SUGGESTIONS.map((s, idx) => (
                <button 
                  key={idx}
                  onClick={() => handleSubmit(undefined, s)}
                  className="w-full text-left px-4 py-3 rounded-xl text-xs text-slate-400 hover:text-white hover:bg-white/5 border border-transparent hover:border-slate-800 transition-all flex items-center group"
                >
                  <ChevronRight size={14} className="mr-2 opacity-0 group-hover:opacity-100 transition-opacity text-blue-500" />
                  {s}
                </button>
              ))}
            </div>
          </section>
        </nav>

        <div className="p-6 border-t border-slate-800">
          <button onClick={clearHistory} className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-slate-900 text-slate-400 hover:bg-red-500/10 hover:text-red-400 border border-slate-800 transition-all text-xs font-medium">
            <Trash2 size={14} />
            Clear Current Chat
          </button>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col relative overflow-hidden bg-slate-950">
        {/* Header */}
        <header className="h-20 shrink-0 flex items-center justify-between px-8 border-b border-slate-900 bg-slate-950 z-20">
          <div className="flex items-center gap-3">
            <div className="flex -space-x-2">
              <div className="w-8 h-8 rounded-full border-2 border-slate-950 bg-blue-600 flex items-center justify-center">
                <Bot size={16} />
              </div>
            </div>
            <div>
              <h2 className="text-sm font-semibold">CCTV Manager Agent</h2>
              <p className="text-[10px] text-emerald-500 flex items-center gap-1 font-bold">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                SYSTEM ONLINE
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-slate-500">
             <Settings size={18} className="cursor-pointer hover:text-white transition-colors" />
             <Maximize2 size={17} className="cursor-pointer hover:text-white transition-colors" />
          </div>
        </header>

        {/* Messages */}
        <div 
          ref={chatContainerRef}
          onScroll={handleScroll}
          className="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar scroll-smooth"
        >
          <AnimatePresence initial={false}>
            {messages.length === 0 && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="h-full flex flex-col items-center justify-center text-center space-y-4 opacity-40"
              >
                <Bot size={48} className="text-blue-500 mb-2" />
                <h3 className="text-xl font-medium">How can I help you today?</h3>
                <p className="text-sm max-w-sm">Ask about staff attendance, vehicle counts, or security events detected on CCTV.</p>
              </motion.div>
            )}
            
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex gap-4 max-w-[80%] ${msg.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                  <div className={`w-10 h-10 shrink-0 rounded-2xl flex items-center justify-center shadow-lg ${
                    msg.type === 'user' ? 'bg-slate-800' : 'bg-blue-600'
                  }`}>
                    {msg.type === 'user' ? <User size={18} /> : <Bot size={18} />}
                  </div>
                  <div className={`space-y-1 ${msg.type === 'user' ? 'items-end' : 'items-start'}`}>
                    <div className={`p-5 rounded-3xl text-sm leading-relaxed ${
                      msg.type === 'user' 
                        ? 'bg-blue-600 text-white rounded-tr-none' 
                        : 'bg-slate-900 border border-slate-800 rounded-tl-none'
                    }`}>
                      {msg.type === 'user' ? (
                        <div className="whitespace-pre-wrap">{msg.content}</div>
                      ) : (
                        <div className="prose prose-invert max-w-none">
                          <ReactMarkdown 
                            remarkPlugins={[remarkGfm]}
                            components={{
                              a: ({ node, ...props }) => {
                                const isImage = props.href?.match(/\.(webp|jpg|jpeg|gif|png|Images)/i);
                                if (isImage) {
                                  return (
                                    <div className="mt-4 mb-4 relative group">
                                      <div className="rounded-xl border border-slate-800 bg-black/40 overflow-hidden transition-all duration-300 hover:border-blue-500 relative">
                                        <img 
                                          src={props.href} 
                                          alt="CCTV Capture" 
                                          className="w-full max-h-[300px] object-contain block cursor-zoom-in rounded-lg"
                                          loading="lazy"
                                          onClick={(e) => {
                                            e.preventDefault();
                                            setPreviewImage(props.href || null);
                                          }}
                                        />
                                      </div>
                                      <p className="text-[10px] text-slate-500 mt-2 px-1 italic">
                                        Click to preview
                                      </p>
                                    </div>
                                  );
                                }
                                return <a {...props} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline" />;
                              }
                            }}
                          >
                            {msg.content}
                          </ReactMarkdown>
                        </div>
                      )}
                    </div>
                    <span className="text-[10px] text-slate-600 block px-1">
                      {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}

            {isAnimatingText && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-start"
              >
                <div className="flex gap-4 max-w-[80%] flex-row">
                  <div className="w-10 h-10 shrink-0 rounded-2xl flex items-center justify-center shadow-lg bg-blue-600">
                    <Bot size={18} />
                  </div>
                  <div className="space-y-1 items-start">
                    <div className="p-5 rounded-3xl text-sm leading-relaxed bg-slate-900 border border-slate-800 rounded-tl-none">
                      <div className="prose prose-invert max-w-none">
                        <ReactMarkdown 
                          remarkPlugins={[remarkGfm]}
                          components={{
                            a: ({ node, ...props }) => {
                              const isImage = props.href?.match(/\.(webp|jpg|jpeg|gif|png|Images)/i);
                              if (isImage) {
                                return (
                                  <div className="mt-4 mb-4 relative group">
                                    <div className="rounded-xl border border-slate-800 bg-black/40 overflow-hidden transition-all duration-300 hover:border-blue-500 relative">
                                      <img 
                                        src={props.href} 
                                        alt="CCTV Capture" 
                                        className="w-full max-h-[300px] object-contain block cursor-zoom-in rounded-lg"
                                        loading="lazy"
                                        onClick={(e) => {
                                          e.preventDefault();
                                          setPreviewImage(props.href || null);
                                        }}
                                      />
                                    </div>
                                  </div>
                                );
                              }
                              return <a {...props} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline" />;
                            }
                          }}
                        >
                          {typingText}
                        </ReactMarkdown>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {isTyping && !isAnimatingText && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex justify-start"
              >
                <div className="flex gap-4 w-full">
                  <div className="w-10 h-10 shrink-0 rounded-2xl bg-blue-600 flex items-center justify-center shadow-lg overflow-hidden relative">
                    <Bot size={18} className="z-10" />
                  </div>
                  <div className="flex-1 space-y-3 pt-2">
                    <div className="space-y-2 max-w-xl">
                      {activeProgress && (
                        <motion.div 
                          key={activeProgress.content}
                          initial={{ x: -10, opacity: 0 }}
                          animate={{ x: 0, opacity: 1 }}
                          className={`flex items-start gap-3 text-xs font-semibold px-4 py-6 rounded-2xl border leading-relaxed overflow-visible animate-pulse ${
                            activeProgress.type === 'task' 
                            ? 'text-cyan-400 bg-cyan-500/10 border-cyan-500/40' 
                            : 'text-blue-400 bg-blue-500/10 border-blue-500/40'
                          }`}
                        >
                          {activeProgress.type === 'task' ? <Cpu size={16} className="mt-1 shrink-0 z-10" /> : <Loader2 size={16} className="mt-1 shrink-0 animate-spin z-10" />}
                          <div className="z-10 flex-1 py-0.5">
                            {activeProgress.content}
                          </div>
                        </motion.div>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={chatEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-8 bg-gradient-to-t from-slate-950 via-slate-950 to-transparent">
          <form 
            onSubmit={handleSubmit}
            className="max-w-4xl mx-auto glass rounded-2xl p-2 flex items-center gap-2 border border-slate-800 shadow-2xl"
          >
            <div className="pl-4 text-slate-500">
              <Info size={18} className="cursor-help hover:text-blue-500 transition-colors" />
            </div>
            <input 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask for cctv analytics summary..."
              className="flex-1 bg-transparent border-none outline-none py-3 text-sm placeholder:text-slate-600"
              disabled={isTyping}
            />
            <button 
              type="submit"
              disabled={!input.trim() || isTyping}
              className={`p-3 rounded-xl transition-all ${
                input.trim() && !isTyping 
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/40 hover:scale-105 active:scale-95' 
                : 'bg-slate-800 text-slate-600 cursor-not-allowed'
              }`}
            >
              <Send size={18} />
            </button>
          </form>
          <p className="text-[10px] text-center text-slate-700 mt-4 tracking-wider font-medium">
             POWERED BY <span className="text-slate-500">MODEL CONTEXT PROTOCOL</span> & DEEP AGENTS
          </p>
        </div>
      </main>
      {/* Image Preview Modal */}
      <AnimatePresence>
        {previewImage && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center p-6 md:p-20 lg:p-40"
          >
            <div 
              className="absolute inset-0 bg-slate-950/95 backdrop-blur-xl cursor-pointer" 
              onClick={() => setPreviewImage(null)}
            />
            
            <button 
              onClick={() => setPreviewImage(null)}
              className="absolute top-10 right-10 z-[120] p-4 bg-white/10 hover:bg-red-600 text-white rounded-full transition-all duration-300 shadow-2xl backdrop-blur-xl border border-white/20 group hover:scale-110"
            >
              <X size={32} className="group-hover:rotate-90 transition-transform duration-300" />
            </button>

            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="relative pointer-events-auto flex items-center justify-center max-w-[90vw] max-h-[85vh]"
            >
              <img 
                src={previewImage} 
                alt="Preview" 
                className="block w-auto h-auto max-w-full max-h-full object-contain rounded-2xl shadow-[0_0_80px_rgba(0,0,0,0.8)] border border-white/10"
              />
              <div className="absolute -top-12 left-0 bg-blue-600/90 backdrop-blur-md text-white px-5 py-2 rounded-full text-[10px] font-bold tracking-widest uppercase shadow-2xl border border-white/10">
                Full-Field Visual Evidence
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
