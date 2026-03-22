"use client";

import { motion } from "framer-motion";
import { Settings, Cpu, Shield, Layers, Save } from "lucide-react";
import { useState, useEffect } from "react";

export default function SettingsPage() {
  const [settings, setSettings] = useState<any>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/nexus-proxy/settings")
      .then(res => res.json())
      .then(data => {
        setSettings(data);
        setLoading(false);
      });
  }, []);

  const handleUpdate = async (e: any) => {
    e.preventDefault();
    await fetch("/nexus-proxy/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings)
    });
    alert("System architecture synchronized.");
  };

  if (loading) return null;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-6xl mx-auto space-y-20 pb-40"
    >
      <div className="flex items-center justify-between pb-12 border-b border-on-surface/5">
        <div className="space-y-4">
          <div className="flex items-center gap-4 text-primary">
            <Settings size={32} className="animate-pulse-slow" />
            <span className="label-md tracking-[0.8em] font-black uppercase">System Protocols</span>
          </div>
          <h1 className="display-lg text-on-surface tracking-tighter">Architecture Tuning</h1>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-20">
        <form onSubmit={handleUpdate} className="lg:col-span-8 space-y-24">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-16">
            <div className="space-y-8">
              <label className="label-sm text-on-surface tracking-[0.5em] ml-4 block opacity-30 font-black">NEURAL RERANKER</label>
              <div className="relative group">
                <input 
                  type="text" 
                  className="w-full bg-surface-container-high/40 border-2 border-transparent rounded-[2rem] px-12 py-8 text-2xl font-bold text-on-surface placeholder-on-surface/10 focus:bg-surface-container-lowest focus:border-primary/40 focus:shadow-[0_0_80px_rgba(235,0,0,0.06)] outline-none transition-all duration-700 shadow-inner"
                  value={settings.reranking_model || ""}
                  onChange={(e) => setSettings({...settings, reranking_model: e.target.value})}
                  placeholder="Configure Reranking Engine..."
                />
              </div>
              <p className="label-sm text-primary-surface opacity-40 ml-6 italic tracking-[0.3em]">CROSS-ENCODING OPTIMIZED</p>
            </div>

            <div className="space-y-8">
              <label className="label-sm text-on-surface tracking-[0.5em] ml-4 block opacity-30 font-black">TOP-K RETRIEVAL</label>
              <div className="relative group">
                <input 
                  type="number" 
                  className="w-full bg-surface-container-high/40 border-2 border-transparent rounded-[2rem] px-12 py-8 text-2xl font-bold text-on-surface focus:bg-surface-container-lowest focus:border-primary/40 outline-none transition-all duration-700 shadow-inner"
                  value={settings.default_top_k || 5}
                  onChange={(e) => setSettings({...settings, default_top_k: Number(e.target.value)})}
                />
              </div>
              <p className="label-sm text-on-surface-variant opacity-30 ml-6 tracking-[0.4em]">SEMANTIC CLUSTERS PER QUERY</p>
            </div>

            <div className="space-y-8">
              <label className="label-sm text-on-surface tracking-[0.5em] ml-4 block opacity-30 font-black">NEURAL CHUNK SIZE</label>
              <div className="relative group">
                <input 
                  type="number" 
                  className="w-full bg-surface-container-high/40 border-2 border-transparent rounded-[2rem] px-12 py-8 text-2xl font-bold text-on-surface focus:bg-surface-container-lowest focus:border-primary/40 outline-none transition-all duration-700 shadow-inner"
                  value={settings.chunk_size || 1000}
                  onChange={(e) => setSettings({...settings, chunk_size: Number(e.target.value)})}
                />
              </div>
              <p className="label-sm text-on-surface-variant opacity-30 ml-6 tracking-[0.4em]">CHARACTER COUNT PER SEGMENT</p>
            </div>
          </div>

          <div className="flex justify-end pt-20 border-t border-on-surface/5">
            <button type="submit" className="btn-primary min-w-[360px] shadow-[0_0_60px_rgba(235,0,0,0.3)] hover:shadow-[0_0_100px_rgba(235,0,0,0.5)] h-16">
              SYNC SYSTEM ARCHITECTURE
            </button>
          </div>
        </form>
      </div>
    </motion.div>
  );
}
