import React, { useState, useEffect, useMemo, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send,
  Bot,
  User,
  Settings,
  Trash2,
  Loader2,
  Cpu,
  Activity,
  Info,
  ChevronRight,
  Maximize2,
  RefreshCw,
  X,
  Sun,
  Moon,
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
  'Who is currently present?',
  'Show me security events from today',
  'Any crowd density alerts?',
  'Summarize vehicle counts for this morning',
];

/* ── Closes modal on Escape key ── */
const ModalKeyHandler: React.FC<{ onClose: () => void; children: React.ReactNode }> = ({ onClose, children }) => {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);
  return <>{children}</>;
};

/* ─────────────────────────────────────────────────────────
   CCTVImage — displays CCTV stills with loading / error states
   Uses native <img> so CORS is never an issue.
───────────────────────────────────────────────────────── */
const CCTVImage: React.FC<{ src: string; onOpen: (s: string) => void }> = ({ src, onOpen }) => {
  const [loaded,  setLoaded]  = useState(false);
  const [errored, setErrored] = useState(false);

  useEffect(() => {
    console.log(`[CCTVImage] Mounting for src: ${src}`);
    setLoaded(false);
    setErrored(false);
  }, [src]);

  if (errored) {
    return (
      <div className="cctv-img-error">
        <button className="cctv-view-btn" onClick={() => onOpen(src)}>
          🖼 View Image
        </button>
        <span className="cctv-img-caption">Preview unavailable (Error loading URL)</span>
      </div>
    );
  }

  return (
    <div
      className="cctv-img-wrapper"
      onClick={() => {
        console.log(`[CCTVImage] Wrapper clicked for: ${src}`);
        onOpen(src);
      }}
      title="Click to view full size"
    >
      {/* Spinner shown until the browser fires onLoad */}
      {!loaded && (
        <div className="cctv-img-loading">
          <Loader2 size={15} className="animate-spin" />
          <span>Loading image…</span>
        </div>
      )}

      {/* Native img — never CORS-blocked */}
      <img
        key={src}
        src={src}
        alt="CCTV Capture"
        loading="lazy"
        style={{ display: loaded ? 'block' : 'none' }}
        onLoad={() => {
          console.log(`[CCTVImage] Successfully loaded: ${src}`);
          setLoaded(true);
        }}
        onError={(e) => {
          console.error(`[CCTVImage] Failed to load: ${src}`, e);
          setErrored(true);
        }}
      />

      {/* Hover overlay (only visible after load) */}
      {loaded && (
        <div className="cctv-img-overlay">
          <span>🔍 View Full Size</span>
        </div>
      )}
    </div>
  );
};

/* ── Detect image URLs (extension OR /Images/ path) ── */
function isImageUrl(href?: string): boolean {
  if (!href) return false;
  return (
    /\.(webp|jpg|jpeg|gif|png)(\?.*)?$/i.test(href) ||
    /\/(images?|screenshots?|captures?|snapshots?)\//i.test(href)
  );
}

/* ── Markdown component map ── */
function makeMarkdownComponents(onImageClick: (src: string) => void) {
  const ImagePreview = ({ src, alt }: { src: string; alt?: string }) => (
    <div style={{ marginTop: '0.6rem', marginBottom: '0.25rem' }}>
      <CCTVImage src={src} onOpen={onImageClick} />
      <div className="cctv-img-footer">
        <p className="cctv-img-caption">Click image to open preview</p>
        <a 
          href={src} 
          target="_blank" 
          rel="noreferrer" 
          className="cctv-direct-link"
          onClick={(e) => e.stopPropagation()}
        >
          ↗ Direct Link
        </a>
      </div>
    </div>
  );

  return {
    a: ({ node, ...props }: any) => {
      if (isImageUrl(props.href)) {
        return <ImagePreview src={props.href} alt={props.children} />;
      }
      return <a {...props} target="_blank" rel="noreferrer" />;
    },
    img: ({ node, ...props }: any) => {
      return <ImagePreview src={props.src} alt={props.alt} />;
    }
  };
}

function App() {
  /* ── State ── */
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isAnimatingText, setIsAnimatingText] = useState(false);
  const [activeProgress, setActiveProgress] = useState<{ type: string; content: string } | null>(null);
  const [typingText, setTypingText] = useState('');
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [darkMode, setDarkMode] = useState(true); // default to dark

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
  const apiHost = 'http://localhost:9000';

  /* ── Persist theme preference ── */
  useEffect(() => {
    const saved = localStorage.getItem('vf_dark_mode');
    if (saved !== null) setDarkMode(saved === 'true');
  }, []);

  const toggleDarkMode = () => {
    setDarkMode((prev) => {
      localStorage.setItem('vf_dark_mode', String(!prev));
      return !prev;
    });
  };

  /* ── Auto-scroll ── */
  useEffect(() => {
    if (!userHasScrolledUp) {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, activeProgress, typingText]);

  const handleScroll = () => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    setUserHasScrolledUp(scrollHeight - scrollTop - clientHeight > 100);
  };

  /* ── Session management ── */
  const clearHistory = () => {
    setMessages([]);
    setActiveProgress(null);
    const newId = `sess_${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newId);
    localStorage.setItem('vf_session_id', newId);
  };

  /* ── Submit / streaming ── */
  const handleSubmit = async (e?: React.FormEvent, customQuery?: string) => {
    e?.preventDefault();
    const query = customQuery || input;
    if (!query.trim() || isTyping) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: query,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);
    setActiveProgress({ type: 'status', content: '🤖 Initializing...' });

    try {
      const response = await fetch(`${apiHost}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, session_id: sessionId }),
      });

      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantMsgContent = '';

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
                    timestamp: new Date(),
                  };
                  setMessages((prev) => [...prev, assistantMsg]);
                  setTypingText('');
                  setIsAnimatingText(false);
                  setActiveProgress(null);
                  setIsTyping(false);
                }
              }, 15);
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
        content:
          '❌ Sorry, I encountered an error connecting to the VisionFacts API. Please ensure the server is running on port 9000.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
      setIsTyping(false);
    } finally {
      setActiveProgress(null);
    }
  };

  const mdComponents = useMemo(() => makeMarkdownComponents((src) => setPreviewImage(src)), []);

  /* ── Render ── */
  return (
    <div className={`app-root${darkMode ? ' dark' : ''}`}>

      {/* ═══ SIDEBAR ═══ */}
      <aside className="app-sidebar">

        {/* Brand */}
        <div className="app-sidebar-brand">
          <div className="brand-icon">
            <Activity size={17} />
          </div>
          <div>
            <div className="brand-name">VisionFacts</div>
            <div className="brand-sub">Analytical Assistant</div>
          </div>
        </div>

        {/* New Chat */}
        <div className="sidebar-actions">
          <button onClick={clearHistory} className="btn-new-chat">
            <RefreshCw size={13} />
            New Chat
          </button>
        </div>

        {/* Nav */}
        <nav className="sidebar-nav">
          <section>
            <div className="sidebar-section-title">Current Session</div>
            <div className="session-badge">{sessionId}</div>
          </section>

          <section>
            <div className="sidebar-section-title">Quick Analysis</div>
            <div className="suggestion-list">
              {SUGGESTIONS.map((s, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSubmit(undefined, s)}
                  className="btn-suggestion"
                >
                  <ChevronRight size={11} className="chevron-icon" />
                  {s}
                </button>
              ))}
            </div>
          </section>
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          <button onClick={clearHistory} className="btn-clear">
            <Trash2 size={12} />
            Clear Current Chat
          </button>
        </div>
      </aside>

      {/* ═══ MAIN CHAT AREA ═══ */}
      <main className="app-main">

        {/* Header */}
        <header className="app-header">
          <div className="header-agent-info">
            <div className="agent-avatar">
              <Bot size={15} />
            </div>
            <div>
              <div className="agent-name">CCTV Manager Agent</div>
              <div className="agent-status">
                <span className="status-dot" />
                System Online
              </div>
            </div>
          </div>

          <div className="header-actions">
            {/* Theme Toggle */}
            <button
              className="icon-btn theme-toggle"
              onClick={toggleDarkMode}
              title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {darkMode ? <Sun size={15} /> : <Moon size={15} />}
            </button>
            <button className="icon-btn" title="Settings">
              <Settings size={15} />
            </button>
            <button className="icon-btn" title="Expand">
              <Maximize2 size={14} />
            </button>
          </div>
        </header>

        {/* ── Messages ── */}
        <div
          ref={chatContainerRef}
          onScroll={handleScroll}
          className="chat-area"
        >
          <AnimatePresence initial={false}>

            {/* Empty state */}
            {messages.length === 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="empty-state"
              >
                <div className="empty-state-icon">
                  <Bot size={28} />
                </div>
                <h3>How can I help you today?</h3>
                <p>
                  Ask about staff attendance, vehicle counts, or security events
                  detected on CCTV.
                </p>
              </motion.div>
            )}

            {/* Rendered messages */}
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.22 }}
                className={`msg-row ${msg.type === 'user' ? 'user' : 'bot'}`}
              >
                <div className={`msg-avatar ${msg.type === 'user' ? 'user-avatar' : 'bot-avatar'}`}>
                  {msg.type === 'user' ? <User size={14} /> : <Bot size={14} />}
                </div>
                <div className="msg-content">
                  <div className={`msg-bubble ${msg.type === 'user' ? 'user-bubble' : 'bot-bubble'}`}>
                    {msg.type === 'user' ? (
                      <div className="whitespace-pre-wrap">{msg.content}</div>
                    ) : (
                      <div className="prose max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    )}
                  </div>
                  <span className="msg-time">
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </motion.div>
            ))}

            {/* Typewriter streaming message */}
            {isAnimatingText && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="msg-row bot"
              >
                <div className="msg-avatar bot-avatar">
                  <Bot size={14} />
                </div>
                <div className="msg-content">
                  <div className="msg-bubble bot-bubble">
                    <div className="prose max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
                        {typingText}
                      </ReactMarkdown>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Thinking / progress indicator */}
            {isTyping && !isAnimatingText && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="thinking-row"
              >
                <div className="msg-avatar bot-avatar">
                  <Bot size={14} />
                </div>
                <div style={{ flex: 1, paddingTop: '0.2rem' }}>
                  {activeProgress && (
                    <motion.div
                      key={activeProgress.content}
                      initial={{ x: -8, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      className={`progress-card ${activeProgress.type === 'task' ? 'task' : 'status'}`}
                    >
                      {activeProgress.type === 'task' ? (
                        <Cpu size={13} className="shrink-0" />
                      ) : (
                        <Loader2 size={13} className="animate-spin shrink-0" />
                      )}
                      <span>{activeProgress.content}</span>
                    </motion.div>
                  )}
                </div>
              </motion.div>
            )}

          </AnimatePresence>
          <div ref={chatEndRef} />
        </div>

        {/* ── Input Area ── */}
        <div className="chat-input-area">
          <form onSubmit={handleSubmit} className="chat-input-form">
            <div className="chat-input-icon">
              <Info size={15} />
            </div>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask for cctv analytics summary…"
              className="chat-input"
              disabled={isTyping}
            />
            <button
              type="submit"
              disabled={!input.trim() || isTyping}
              className={`btn-send ${input.trim() && !isTyping ? 'active' : 'disabled'}`}
            >
              <Send size={14} />
            </button>
          </form>
          <p className="powered-by">
            Powered by <span>Model Context Protocol</span> &amp; Deep Agents
          </p>
        </div>
      </main>

      {/* ═══ IMAGE PREVIEW MODAL ═══ */}
      <AnimatePresence>
        {previewImage && (
          <ModalKeyHandler onClose={() => setPreviewImage(null)}>
            {/* Backdrop — click outside = close */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.18 }}
              className="img-preview-overlay"
              role="dialog"
              aria-modal="true"
              aria-label="Image preview"
            >
              <div
                className="img-preview-backdrop"
                onClick={() => setPreviewImage(null)}
              />

              {/* ── Centered modal card ── */}
              <motion.div
                initial={{ scale: 0.93, opacity: 0, y: 16 }}
                animate={{ scale: 1,    opacity: 1, y: 0  }}
                exit={{ scale: 0.93,   opacity: 0, y: 8  }}
                transition={{ type: 'spring', stiffness: 340, damping: 28 }}
                className="img-preview-modal"
              >
                {/* Top bar */}
                <div className="img-preview-topbar">
                  <span className="img-preview-topbar-title">
                    📷 CCTV Evidence
                  </span>
                  <div className="img-preview-topbar-actions">
                    <a
                      href={previewImage}
                      target="_blank"
                      rel="noreferrer"
                      className="img-preview-open-link"
                    >
                      ↗ Full Size
                    </a>
                    <button
                      onClick={() => setPreviewImage(null)}
                      className="img-preview-close-btn"
                      autoFocus
                    >
                      <X size={14} />
                      Close
                    </button>
                  </div>
                </div>

                {/* Image */}
                <div className="img-preview-content">
                  <img
                    src={previewImage}
                    alt="Preview"
                    onLoad={() => console.log(`[Modal] Large image loaded: ${previewImage}`)}
                    onError={(e) => {
                      console.error(`[Modal] Large image failed: ${previewImage}`, e);
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                </div>

                {/* Bottom hint */}
                <p className="img-preview-hint">
                  Click outside or press <kbd>Esc</kbd> to close
                </p>
              </motion.div>
            </motion.div>
          </ModalKeyHandler>
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
