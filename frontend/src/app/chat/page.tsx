"use client";

import { useState, useRef, useEffect, FormEvent } from "react";
import { motion } from "framer-motion";
import { 
  Send, User, Bot, Loader2, 
  Terminal, ShieldCheck, Search, Database, Fingerprint, Cpu, FileText, AlertCircle, X
} from "lucide-react";
import { getCitationLabel, getCitationSnippet, isCitationAvailable } from "./citationHelpers";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
};

type Citation = {
  id?: string | number;
  chunk_id?: string;
  document_id?: string;
  document_name?: string;
  chunk_text?: string;
  snippet?: string;
  page?: string | number;
  available?: boolean;
};

type SourceContext = {
  available: boolean;
  message?: string;
  document?: {
    id: string;
    filename: string;
    status?: string;
    created_at?: string | null;
    indexed_at?: string | null;
  };
  chunk?: {
    id: string;
    document_id: string;
    text?: string;
    preview?: string;
    page_number?: number | null;
    chunk_index?: number | null;
    token_count?: number | null;
  };
};

type TraceEvent = {
  agent?: string;
  action?: string;
  result?: string;
};

type StreamEvent =
  | { type: "token"; token?: string; data?: string }
  | { type: "trace"; agent?: string; action?: string; result?: string }
  | { type: "citations"; citations?: Citation[]; data?: Citation[] }
  | { type: "error"; message?: string }
  | { type: "done" };

function parseSseEvents(buffer: string) {
  const frames = buffer.split("\n\n");
  const remainder = frames.pop() ?? "";

  const events = frames
    .map((frame) => {
      const data = frame
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.replace(/^data:\s?/, ""))
        .join("\n");

      if (!data) return null;
      return JSON.parse(data) as StreamEvent;
    })
    .filter(Boolean) as StreamEvent[];

  return { events, remainder };
}

export default function ChatPage() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [traces, setTraces] = useState<TraceEvent[]>([]);
  const [sourceContext, setSourceContext] = useState<SourceContext | null>(null);
  const [sourceLoading, setSourceLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, traces]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const userMsg: ChatMessage = { role: "user", content: query };
    setMessages(prev => [...prev, userMsg]);
    setQuery("");
    setLoading(true);
    setTraces([]);

    try {
      // Real streaming implementation via SSE
      const url = `${process.env.NEXT_PUBLIC_API_URL || "/nexus-proxy"}/chat/query/stream`;
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMsg.content, top_k: 5 }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Chat stream failed with status ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      const assistantMsg: ChatMessage = { role: "assistant", content: "", citations: [] };
      let pendingBuffer = "";
      setMessages(prev => [...prev, assistantMsg]);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        pendingBuffer += decoder.decode(value, { stream: true });
        const { events, remainder } = parseSseEvents(pendingBuffer);
        pendingBuffer = remainder;
        
        for (const event of events) {
          if (event.type === "token") {
            assistantMsg.content += event.token ?? event.data ?? "";
            setMessages(prev => {
              const newMsgs = [...prev];
              newMsgs[newMsgs.length - 1] = { ...assistantMsg };
              return newMsgs;
            });
          } else if (event.type === "trace") {
            setTraces(prev => [...prev, event]);
          } else if (event.type === "citations") {
            assistantMsg.citations = event.citations ?? event.data ?? [];
            setMessages(prev => {
              const newMsgs = [...prev];
              newMsgs[newMsgs.length - 1] = { ...assistantMsg };
              return newMsgs;
            });
          } else if (event.type === "error") {
            throw new Error(event.message || "Chat stream failed");
          }
        }
      }
    } catch (err) {
      console.error("Chat error:", err);
      const message = err instanceof Error ? err.message : "Unable to complete the chat request.";
      setMessages(prev => [
        ...prev,
        { role: "assistant", content: `Stream error: ${message}`, citations: [] }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleCitationClick = async (citation: Citation, index: number) => {
    if (!isCitationAvailable(citation)) {
      setSourceContext({
        available: false,
        message: getCitationSnippet(citation),
        document: {
          id: String(citation.document_id || ""),
          filename: citation.document_name || "Source unavailable",
        },
        chunk: {
          id: String(citation.chunk_id || citation.id || index + 1),
          document_id: String(citation.document_id || ""),
          preview: getCitationSnippet(citation),
        },
      });
      return;
    }

    setSourceLoading(true);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "/nexus-proxy/v1";
      const response = await fetch(`${apiBase}/documents/${citation.document_id}/chunks/${citation.chunk_id}`);
      const data = await response.json();

      if (!response.ok) {
        const detail = typeof data?.detail === "object" ? data.detail : null;
        setSourceContext({
          available: false,
          message: detail?.message || "Source document or chunk is unavailable.",
          document: {
            id: String(citation.document_id || ""),
            filename: citation.document_name || "Source unavailable",
          },
          chunk: {
            id: String(citation.chunk_id || citation.id || index + 1),
            document_id: String(citation.document_id || ""),
            preview: getCitationSnippet(citation),
          },
        });
        return;
      }

      setSourceContext(data);
    } catch {
      setSourceContext({
        available: false,
        message: "Source context could not be loaded.",
        document: {
          id: String(citation.document_id || ""),
          filename: citation.document_name || "Source unavailable",
        },
        chunk: {
          id: String(citation.chunk_id || citation.id || index + 1),
          document_id: String(citation.document_id || ""),
          preview: getCitationSnippet(citation),
        },
      });
    } finally {
      setSourceLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto h-[calc(100vh-160px)] flex flex-col gap-12">
      {/* Header Module */}
      <div className="flex items-center justify-between pb-8 border-b border-on-surface/5">
        <div className="space-y-3">
          <div className="flex items-center gap-3 text-secondary">
             <Fingerprint size={24} className="animate-pulse-slow" />
             <span className="label-sm tracking-[0.6em] font-black uppercase">Neural Uplink Active</span>
          </div>
          <h1 className="display-md text-on-surface tracking-tighter">Nexus Swarm</h1>
        </div>
        <div className="flex gap-4">
           <div className="px-6 py-3 bg-surface-container-high/40 rounded-full border border-outline-variant flex items-center gap-3">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="label-sm opacity-50 tracking-[0.2em]">RRF PARITY: 100%</span>
           </div>
        </div>
      </div>

      <div className="flex-1 flex gap-12 overflow-hidden">
        {/* Main Interaction Module */}
        <div className="flex-1 flex flex-col bg-surface shadow-[0_4px_30px_rgba(18,18,18,0.03)] border border-on-surface/5 relative overflow-hidden group">
          <div className="flex-1 overflow-y-auto p-12 space-y-12 scrollbar-hide">
            {messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-center space-y-8 opacity-20">
                <Cpu size={80} strokeWidth={0.5} className="animate-pulse-slow" />
                <div className="space-y-2">
                  <p className="display-md !text-2xl font-normal">Awaiting Neural Stimulus</p>
                  <p className="label-sm tracking-widest">ENTER QUERY TO INITIALIZE RETRIEVAL</p>
                </div>
              </div>
            )}
            
            {messages.map((m, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex gap-8 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {m.role === 'assistant' && (
                  <div className="w-12 h-12 bg-primary-container rounded-full flex items-center justify-center shrink-0 shadow-lg mt-2">
                    <Bot size={22} className="text-secondary" />
                  </div>
                )}
                <div className={`max-w-[80%] space-y-4`}>
                  <div className={`p-8 rounded-[2rem] ${
                    m.role === 'user' 
                      ? 'bg-primary-container text-on-primary-fixed shadow-premium-dark rounded-tr-none' 
                      : 'bg-surface-container-low text-on-surface border border-outline-variant rounded-tl-none font-medium text-lg leading-relaxed'
                  }`}>
                    {m.content}
                    {m.role === 'assistant' && m.content === "" && (
                       <Loader2 className="animate-spin opacity-20" size={24} />
                    )}
                  </div>
	                  {!!m.citations?.length && (
	                    <div className="flex flex-wrap gap-3 ml-2">
	                       {m.citations.map((c, ci) => (
	                         <button
                              key={ci}
                              type="button"
                              onClick={() => handleCitationClick(c, ci)}
                              className="px-4 py-1.5 bg-surface-container-highest rounded-full border border-outline-variant flex items-center gap-2 hover:border-secondary/60 hover:bg-secondary/10 transition-colors text-left"
                            >
	                            <Database size={12} className={isCitationAvailable(c) ? "text-primary/60" : "text-red-500/60"} />
	                            <span className="text-[10px] font-black tracking-widest text-on-surface/60 uppercase">{getCitationLabel(c, ci)}</span>
	                         </button>
	                       ))}
	                    </div>
	                  )}
                </div>
                {m.role === 'user' && (
                  <div className="w-12 h-12 bg-secondary rounded-full flex items-center justify-center shrink-0 shadow-lg mt-2">
                    <User size={22} className="text-primary" />
                  </div>
                )}
              </motion.div>
            ))}
            <div ref={scrollRef} />
          </div>

          {/* Input Module */}
          <div className="p-8 bg-surface-container-lowest border-t border-on-surface/5">
            <form onSubmit={handleSubmit} className="relative group">
              <input 
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Synchronize with global intelligence..."
                className="w-full bg-surface-container-low border-2 border-transparent rounded-[2rem] px-10 py-7 text-xl font-medium text-on-surface placeholder-on-surface/20 focus:bg-white focus:border-secondary/40 focus:shadow-[0_0_80px_rgba(240,196,25,0.08)] outline-none transition-all duration-700 shadow-inner"
              />
              <button 
                type="submit"
                disabled={loading || !query.trim()}
                className="absolute right-4 top-1/2 -translate-y-1/2 w-16 h-16 bg-primary-container text-secondary rounded-full flex items-center justify-center transition-all hover:scale-110 active:scale-90 shadow-xl disabled:opacity-20 disabled:scale-100"
              >
                {loading ? <Loader2 size={24} className="animate-spin" /> : <Send size={24} />}
              </button>
            </form>
          </div>
        </div>

	        {/* Intelligence Trace Module */}
	        <div className="w-96 flex flex-col gap-8">
            <div className="bg-surface p-8 border border-on-surface/5 shadow-premium min-h-[260px] flex flex-col gap-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <FileText size={18} className="text-secondary" />
                  <span className="label-sm tracking-[0.35em] font-black opacity-40">Source Context</span>
                </div>
                {sourceContext && (
                  <button
                    type="button"
                    onClick={() => setSourceContext(null)}
                    className="w-8 h-8 flex items-center justify-center text-on-surface/30 hover:text-on-surface transition-colors"
                    aria-label="Close source context"
                  >
                    <X size={16} />
                  </button>
                )}
              </div>

              {sourceLoading ? (
                <div className="flex-1 flex items-center justify-center">
                  <Loader2 size={22} className="animate-spin text-on-surface/20" />
                </div>
              ) : sourceContext ? (
                <div className="space-y-5">
                  <div className="flex items-start gap-3">
                    {sourceContext.available ? (
                      <ShieldCheck size={18} className="text-emerald-500 mt-1" />
                    ) : (
                      <AlertCircle size={18} className="text-red-500 mt-1" />
                    )}
                    <div className="min-w-0">
                      <p className="text-sm font-black tracking-wide text-on-surface truncate">
                        {sourceContext.document?.filename || "Source unavailable"}
                      </p>
                      <p className="label-sm opacity-40 text-[9px] tracking-[0.2em] uppercase">
                        {sourceContext.available ? `Chunk ${sourceContext.chunk?.id}` : "Unavailable reference"}
                      </p>
                    </div>
                  </div>

                  <div className="p-5 bg-surface-container-low border-l-2 border-secondary/40 rounded-r-2xl">
                    <p className="text-xs leading-relaxed text-on-surface/70">
                      {sourceContext.chunk?.preview || sourceContext.message || "Preview unavailable."}
                    </p>
                  </div>

                  {sourceContext.available && (
                    <div className="grid grid-cols-2 gap-4 pt-2">
                      <div>
                        <p className="label-sm text-[9px] opacity-30 tracking-widest">PAGE</p>
                        <p className="text-sm font-bold">{sourceContext.chunk?.page_number ?? "N/A"}</p>
                      </div>
                      <div>
                        <p className="label-sm text-[9px] opacity-30 tracking-widest">INDEX</p>
                        <p className="text-sm font-bold">{sourceContext.chunk?.chunk_index ?? "N/A"}</p>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center gap-3 opacity-20">
                  <FileText size={34} strokeWidth={1} />
                  <p className="label-sm tracking-[0.3em] font-bold uppercase">Select a citation</p>
                </div>
              )}
            </div>

	          <div className="bg-surface p-10 border border-on-surface/5 shadow-premium flex-1 overflow-hidden flex flex-col relative group">
             <div className="absolute top-0 right-0 w-32 h-32 bg-secondary/5 blur-[80px] rounded-full" />
             <div className="flex items-center gap-4 mb-10 relative z-10">
                <Terminal size={18} className="text-secondary" />
                <span className="label-sm tracking-[0.4em] font-black opacity-30">Agent Trace Log</span>
             </div>
             
             <div className="flex-1 overflow-y-auto space-y-8 scrollbar-hide relative z-10">
                {traces.length === 0 && (
                   <div className="h-full flex flex-col items-center justify-center opacity-10 text-center gap-3">
                      <Search size={40} strokeWidth={1} />
                      <p className="label-sm">Idle</p>
                   </div>
                )}
                {traces.map((t, i) => (
                  <motion.div 
                    key={i}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="space-y-3"
                  >
                    <div className="flex items-center justify-between">
                       <span className="label-sm text-secondary font-black tracking-widest">{t.agent}</span>
                       <div className="w-1.5 h-1.5 rounded-full bg-secondary" />
                    </div>
                    <div className="p-5 bg-surface-container-low border-l-2 border-secondary/40 rounded-r-2xl">
                       <p className="text-[11px] font-bold text-on-surface/70 leading-relaxed tracking-tight">{t.result}</p>
                    </div>
                  </motion.div>
                ))}
             </div>
             
             <div className="mt-8 pt-8 border-t border-on-surface/5">
                <div className="flex items-center gap-3 mb-4">
                   <ShieldCheck size={14} className="text-emerald-500" />
                   <span className="label-sm text-emerald-500 opacity-60">Neural Integrity: OK</span>
                </div>
                <div className="w-full h-1.5 bg-surface-container-low rounded-full overflow-hidden">
                   <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: messages.length > 0 ? "100%" : "0%" }}
                    className="h-full bg-emerald-500" 
                   />
                </div>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
