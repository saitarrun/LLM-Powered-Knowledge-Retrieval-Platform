"use client";

import { useState, useRef, useEffect, Suspense } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Send, User, Bot, Sparkles, Loader2, ArrowRight, 
  Terminal, ShieldCheck, Search, Database, Fingerprint, RefreshCw, Cpu
} from "lucide-react";
import { api } from "@/services/api";

export default function ChatPage() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [traces, setTraces] = useState<any[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, traces]);

  const handleSubmit = async (e: any) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const userMsg = { role: "user", content: query };
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

      if (!response.body) return;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      let assistantMsg = { role: "assistant", content: "", citations: [] };
      setMessages(prev => [...prev, assistantMsg]);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split("\n\n");
        
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const data = JSON.parse(line.replace("data: ", ""));
          const event = line.match(/event: (.*)/)?.[1] || "token";

          if (event === "token") {
            assistantMsg.content += data;
            setMessages(prev => {
              const newMsgs = [...prev];
              newMsgs[newMsgs.length - 1] = { ...assistantMsg };
              return newMsgs;
            });
          } else if (event === "trace") {
            setTraces(prev => [...prev, data]);
          } else if (event === "citations") {
            assistantMsg.citations = data;
            setMessages(prev => {
              const newMsgs = [...prev];
              newMsgs[newMsgs.length - 1] = { ...assistantMsg };
              return newMsgs;
            });
          }
        }
      }
    } catch (err) {
      console.error("Chat error:", err);
    } finally {
      setLoading(false);
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
                  {m.citations?.length > 0 && (
                    <div className="flex flex-wrap gap-3 ml-2">
                       {m.citations.map((c: any, ci: number) => (
                         <div key={ci} className="px-4 py-1.5 bg-surface-container-highest rounded-full border border-outline-variant flex items-center gap-2">
                            <Database size={12} className="text-primary/40" />
                            <span className="text-[10px] font-black tracking-widest text-on-surface/60 uppercase">{c.document_name} • P.{c.page}</span>
                         </div>
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
