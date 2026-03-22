"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Database, Shield, RefreshCw, Layers, LayoutGrid, Search, Network } from "lucide-react";
import { api } from "@/services/api";

export default function DocumentsPage() {
  const [docs, setDocs] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isCalibrating, setIsCalibrating] = useState(false);

  const loadData = useCallback(async () => {
    const [d, a] = await Promise.all([api.getDocuments(), api.getAnalytics()]);
    setDocs(d);
    setAnalytics(a);
    setLoading(false);
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleCalibrate = async () => {
    setIsCalibrating(true);
    await new Promise(r => setTimeout(r, 2000));
    await loadData();
    setIsCalibrating(false);
  };

  const getProgressWidth = (status: string) => {
    switch(status) {
      case 'processing': return '40%';
      case 'completed': return '100%';
      case 'failed': return '100%';
      default: return '0%';
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-20 pb-40">
      {/* Header Module: Aesthetic Precision */}
      <div className="flex items-center justify-between pb-12 border-b border-on-surface/5">
        <div className="space-y-4">
          <div className="flex items-center gap-4 text-primary">
            <Layers size={32} className="animate-pulse-slow" />
            <span className="label-md tracking-[0.8em] font-black uppercase">Knowledge Archive</span>
          </div>
          <h1 className="display-lg text-on-surface tracking-tighter">Document Catalogs</h1>
        </div>
        <div className="flex gap-6">
           <div className="flex flex-col items-end">
              <span className="label-sm opacity-30 tracking-[0.4em]">SYNC STATUS</span>
              <span className="text-xl font-bold font-display text-primary uppercase">Quantum Parity</span>
           </div>
           <div className="w-12 h-12 bg-secondary rounded-full flex items-center justify-center shadow-premium">
              <div className="w-2 h-2 bg-primary rounded-full animate-ping" />
           </div>
        </div>
      </div>

      <div className="space-y-24">
         {/* Analytics Dashboard Segment */}
         <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            <StatCard label="Total Intelligence Units" value={docs.length} metric="DOCUMENTS" icon={Database} accent />
            <StatCard label="Neural Latency" value={analytics?.queries?.avg_latency_ms || 240} metric="MILLISECONDS" icon={RefreshCw} />
            <StatCard label="Validation Integrity" value="99.8%" metric="CONFIDENCE" icon={Shield} />
         </div>

         {/* Document Registry Table */}
         <div className="grid grid-cols-1 md:grid-cols-12 gap-16">
            <div className="col-span-8 space-y-10">
               <div className="flex items-center justify-between pb-4 border-b border-on-surface/5">
                  <h2 className="label-md tracking-[0.4em] opacity-40 font-black uppercase">Ingestion Stream</h2>
                  <div className="flex items-center gap-4">
                     <LayoutGrid size={16} className="text-secondary" />
                     <div className="w-px h-4 bg-on-surface/5" />
                     <span className="label-sm opacity-20">GRID MODE</span>
                  </div>
               </div>
               
               <div className="space-y-6">
                  {docs.length > 0 ? docs.map((doc, i) => (
                    <motion.div 
                      key={doc.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className="p-8 bg-surface border border-transparent hover:border-secondary/20 hover:shadow-premium transition-all duration-700 flex items-center justify-between group"
                    >
                       <div className="flex items-center gap-8">
                          <div className={`p-5 rounded-2xl ${doc.status === 'completed' ? 'bg-emerald-50 text-emerald-500' : 'bg-secondary/10 text-primary'}`}>
                             {doc.status === 'completed' ? <Shield size={24} /> : <Database size={24} className="animate-pulse" />}
                          </div>
                          <div className="space-y-1.5">
                             <h4 className="text-xl font-bold tracking-tight text-on-surface group-hover:text-primary transition-colors">{doc.filename}</h4>
                             <div className="flex items-center gap-4">
                                <span className={`label-sm ${doc.status === 'completed' ? 'text-emerald-500' : 'text-primary'}`}>{doc.status}</span>
                                <div className="w-1 h-1 rounded-full bg-on-surface/10" />
                                <span className="label-sm opacity-30 tracking-widest uppercase font-bold text-[9px]">ID: {doc.id?.slice(0, 8)}</span>
                             </div>
                          </div>
                       </div>
                       
                       <div className="flex items-center gap-6">
                          <div className="flex flex-col items-end gap-1.5 pr-5 border-r border-outline-variant">
                             <span className="label-sm text-on-surface/40 tracking-[0.3em] text-[9px] font-bold">INTEGRITY</span>
                             <div className="w-20 h-[2px] bg-surface-container-high overflow-hidden">
                                <motion.div animate={{ width: getProgressWidth(doc.status) }} className={`h-full ${doc.status === 'failed' ? 'bg-red-500' : 'bg-secondary'}`} />
                             </div>
                          </div>
                          <button onClick={() => loadData()} className="w-8 h-8 flex items-center justify-center text-on-surface/40 hover:text-secondary hover:rotate-180 transition-all duration-700 active:scale-95">
                             <RefreshCw size={15} strokeWidth={1.5} />
                          </button>
                       </div>
                    </motion.div>
                  )) : (
                    <div className="h-48 bg-background border border-dashed border-outline-variant flex flex-col items-center justify-center gap-4 opacity-60">
                       <Database size={28} className="text-on-surface/30" strokeWidth={1} />
                       <p className="label-sm opacity-50 tracking-[0.3em] font-bold uppercase">Awaiting Catalogs</p>
                    </div>
                  )}
               </div>
            </div>

            {/* Sidebar Module: Precision Baseline Alignment */}
            <div className="col-span-4 flex flex-col gap-8">
               <div className="bg-surface p-12 shadow-[0_4px_20px_rgba(18,18,18,0.04),_0_20px_50px_rgba(18,18,18,0.08)] relative overflow-hidden group min-h-[400px]">
                  <div className="absolute -top-10 -right-10 p-6 opacity-[0.02] transition-transform duration-1000">
                     <Shield size={320} strokeWidth={0.5} />
                  </div>
                  <div className="relative z-10 flex flex-col h-full justify-between">
                     <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                           <div className="w-px h-8 bg-secondary" />
                           <Shield size={22} className="text-primary" strokeWidth={1} />
                        </div>
                        <div className="w-2 h-2 bg-secondary animate-pulse" />
                     </div>
                     <div className="space-y-6 mt-12">
                        <h3 className="display-md !text-3xl text-on-surface font-normal">Data Parity</h3>
                        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-outline-variant">
                           <div>
                              <p className="label-sm tracking-widest text-on-surface/40 uppercase text-[9px] font-bold">Total Chunks</p>
                              <p className="text-2xl font-display font-medium text-on-surface">{analytics?.chunks?.total || 0}</p>
                           </div>
                           <div>
                              <p className="label-sm tracking-widest text-on-surface/40 uppercase text-[9px] font-bold">Avg Tokens/Chunk</p>
                              <p className="text-2xl font-display font-medium text-on-surface">{analytics?.chunks?.avg_tokens || 0}</p>
                           </div>
                        </div>
                     </div>
                     <button onClick={handleCalibrate} className="mt-12 h-14 bg-surface-container-low text-on-surface hover:bg-secondary hover:text-primary transition-all font-bold tracking-[0.2em] text-[10px] uppercase w-full flex items-center justify-between px-8 group overflow-hidden relative">
                        <span className="relative z-10">{isCalibrating ? "SYNCHRONIZING..." : "Calibrate Protocols"}</span>
                        <Network size={14} className={`relative z-10 ${isCalibrating ? "animate-spin" : "group-hover:rotate-180 transition-transform duration-700"}`} />
                     </button>
                  </div>
               </div>

            </div>
         </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, metric, icon: Icon, accent }: any) {
  return (
    <div className="p-10 transition-all duration-700 bg-surface shadow-[0_4px_20px_rgba(18,18,18,0.04),_0_20px_50px_rgba(18,18,18,0.08)] flex flex-col gap-8 border-t border-secondary/20 hover:-translate-y-2 overflow-hidden">
       <div className="flex justify-between items-start">
          <Icon size={24} className="text-primary opacity-80" strokeWidth={1} />
          {accent && <div className="w-2 h-2 bg-secondary" />}
       </div>
       <div className="space-y-3">
          <p className="label-sm tracking-[0.2em] font-bold text-[10px] text-on-surface opacity-40 uppercase">{label}</p>
          <div className="flex flex-col gap-1">
             <span className="text-[2.4rem] font-display tracking-tight leading-none text-on-surface truncate">{value}</span>
             <span className="label-sm font-bold tracking-[0.2em] text-secondary text-[9px]">{metric}</span>
          </div>
       </div>
    </div>
  );
}
