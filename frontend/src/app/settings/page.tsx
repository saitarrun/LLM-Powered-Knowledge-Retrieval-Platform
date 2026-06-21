"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/services/api";
import { useSidebar } from "@/components/NavigationWrapper";

export default function SettingsPage() {
  const [settings, setSettings] = useState<{
    reranking_model?: string;
    default_top_k?: number;
    chunk_size?: number;
    [key: string]: string | number | undefined;
  }>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const { toggle } = useSidebar();

  useEffect(() => {
    api.getSettings().then((data) => {
      setSettings(data || {});
      setLoading(false);
    });
  }, []);

  const handleUpdate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.updateSettings(settings as Record<string, unknown>);
      alert("System architecture synchronized successfully.");
    } catch (err) {
      console.error(err);
      alert("Failed to synchronize settings.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <main className="h-full flex flex-col relative overflow-hidden bg-surface-container-lowest">
      {/* Top Bar */}
      <header className="w-full h-16 sticky top-0 bg-surface/80 backdrop-blur-xl border-b border-outline-variant/30 flex justify-between items-center px-lg z-40">
        <div className="flex items-center gap-sm">
          <span 
            className="material-symbols-outlined md:hidden cursor-pointer text-on-surface mr-2" 
            onClick={toggle}
          >
            menu
          </span>
          <span className="material-symbols-outlined text-primary">settings</span>
          <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Settings</h2>
        </div>
      </header>

      {/* Page Content */}
      <div className="flex-1 overflow-y-auto p-lg custom-scrollbar max-w-[800px] mx-auto w-full py-xl">
        <div className="mb-xl">
          <h3 className="font-headline-md text-headline-md text-on-surface mb-1">Architecture Tuning</h3>
          <p className="text-body-md text-outline">Configure your RAG engine properties, chunk bounds, and rerank parameters.</p>
        </div>

        {loading ? (
          <div className="text-center py-20 opacity-50">
            <span className="animate-pulse-soft">Loading system parameters...</span>
          </div>
        ) : (
          <form onSubmit={handleUpdate} className="space-y-xl">
            <div className="space-y-lg">
              {/* Reranking Model */}
              <div className="flex flex-col gap-sm">
                <label className="font-label-md text-label-md text-outline uppercase tracking-wider">NEURAL RERANKER</label>
                <input
                  type="text"
                  className="w-full bg-surface-container border border-outline-variant/20 rounded-xl px-md py-3 text-body-lg text-on-surface focus:ring-2 focus:ring-secondary-container transition-all"
                  value={settings.reranking_model || ""}
                  onChange={(e) => setSettings({ ...settings, reranking_model: e.target.value })}
                  placeholder="Enter Reranking Model..."
                />
                <span className="text-xs text-outline italic">CROSS-ENCODING MODEL OPTIMIZATION</span>
              </div>

              {/* Top-K Retrieval */}
              <div className="flex flex-col gap-sm">
                <label className="font-label-md text-label-md text-outline uppercase tracking-wider">TOP-K RETRIEVAL</label>
                <input
                  type="number"
                  className="w-full bg-surface-container border border-outline-variant/20 rounded-xl px-md py-3 text-body-lg text-on-surface focus:ring-2 focus:ring-secondary-container transition-all"
                  value={settings.default_top_k || 5}
                  onChange={(e) => setSettings({ ...settings, default_top_k: Number(e.target.value) })}
                />
                <span className="text-xs text-outline italic">NUMBER OF SEMANTIC CLUSTERS RETRIEVED PER PROMPT</span>
              </div>

              {/* Chunk Size */}
              <div className="flex flex-col gap-sm">
                <label className="font-label-md text-label-md text-outline uppercase tracking-wider">NEURAL CHUNK SIZE</label>
                <input
                  type="number"
                  className="w-full bg-surface-container border border-outline-variant/20 rounded-xl px-md py-3 text-body-lg text-on-surface focus:ring-2 focus:ring-secondary-container transition-all"
                  value={settings.chunk_size || 1000}
                  onChange={(e) => setSettings({ ...settings, chunk_size: Number(e.target.value) })}
                />
                <span className="text-xs text-outline italic">CHARACTER BOUNDS PER EMBEDDING INDEX</span>
              </div>
            </div>

            <div className="pt-lg border-t border-outline-variant/20 flex justify-end">
              <button
                type="submit"
                disabled={saving}
                className="bg-primary text-on-primary py-md px-xl rounded-full font-semibold hover:bg-primary/90 transition-all shadow-lg shadow-primary/10 active:scale-95 disabled:opacity-50 disabled:scale-100"
              >
                {saving ? "Synchronizing..." : "Sync System Architecture"}
              </button>
            </div>
          </form>
        )}
      </div>
    </main>
  );
}
