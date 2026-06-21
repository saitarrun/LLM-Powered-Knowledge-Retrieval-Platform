"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { useSidebar } from "@/components/NavigationWrapper";
import { removeToken } from "@/services/auth";

export default function Sidebar({ className = "hidden md:flex fixed left-0 top-0" }: { className?: string }) {
  const pathname = usePathname();
  const router = useRouter();
  const { close } = useSidebar();
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch("/api/health", { cache: "no-store" });
        setBackendOnline(res.ok);
      } catch {
        setBackendOnline(false);
      }
    };
    check();
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, []);

  const isChatActive = pathname === "/" || pathname.startsWith("/chat");
  const isDocsActive = pathname.startsWith("/documents");
  const isGraphActive = pathname.startsWith("/graph");
  const isSettingsActive = pathname.startsWith("/settings");

  const startNewChat = () => {
    router.push("/");
    close();
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("new-chat"));
    }
  };

  const handleLogout = () => {
    removeToken();
    router.push("/login");
    close();
  };

  return (
    <aside className={`flex flex-col h-full py-lg px-md w-[280px] bg-surface dark:bg-surface-dim/90 backdrop-blur-xl border-r border-outline-variant/20 z-40 ${className}`}>
      <div className="flex flex-col gap-sm mb-[20px]">
        <div className="flex justify-between items-center px-sm">
          <div className="flex items-center gap-sm">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-fixed">
              <span className="material-symbols-outlined text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                auto_awesome
              </span>
            </div>
            <div>
              <h1 className="font-headline-md text-headline-md font-bold tracking-tight text-primary leading-tight">Aether AI</h1>
              <p className="text-[10px] font-label-md uppercase tracking-widest text-outline">Enterprise RAG</p>
            </div>
          </div>
          <button 
            className="md:hidden p-1 text-on-surface-variant hover:text-on-surface"
            onClick={close}
            aria-label="Close sidebar"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>
        
        <button 
          onClick={startNewChat}
          className="mt-lg flex items-center justify-center gap-sm w-full py-[10px] px-lg bg-primary text-on-primary rounded-full font-semibold transition-all duration-200 active:scale-95 hover:bg-primary/90 shadow-lg shadow-primary/10"
        >
          <span className="material-symbols-outlined text-[20px]">add</span>
          New Chat
        </button>
      </div>

      <nav className="flex-1 flex flex-col gap-xs">
        {/* Chat Tab */}
        <Link 
          href="/" 
          onClick={close}
          className={`flex items-center gap-[12px] py-[10px] px-md transition-all duration-200 ease-in-out group ${
            isChatActive 
              ? "text-primary dark:text-primary-fixed bg-surface-variant/50 dark:bg-primary-container/20 border-r-2 border-primary font-semibold" 
              : "text-on-surface-variant dark:text-outline hover:text-on-surface hover:bg-surface-container-low"
          }`}
        >
          <span className="material-symbols-outlined text-[20px]" style={isChatActive ? { fontVariationSettings: "'FILL' 1" } : {}}>
            chat_bubble
          </span>
          <span className="font-label-md text-label-md">Chat</span>
        </Link>

        {/* Knowledge Base */}
        <Link 
          href="/documents" 
          onClick={close}
          className={`flex items-center gap-[12px] py-[10px] px-md transition-all duration-200 ease-in-out group ${
            isDocsActive 
              ? "text-primary dark:text-primary-fixed bg-surface-variant/50 dark:bg-primary-container/20 border-r-2 border-primary font-semibold" 
              : "text-on-surface-variant dark:text-outline hover:text-on-surface hover:bg-surface-container-low"
          }`}
        >
          <span className="material-symbols-outlined text-[20px]" style={isDocsActive ? { fontVariationSettings: "'FILL' 1" } : {}}>
            database
          </span>
          <span className="font-label-md text-label-md">Knowledge Base</span>
        </Link>

        {/* Graph Topology */}
        <Link 
          href="/graph" 
          onClick={close}
          className={`flex items-center gap-[12px] py-[10px] px-md transition-all duration-200 ease-in-out group ${
            isGraphActive 
              ? "text-primary dark:text-primary-fixed bg-surface-variant/50 dark:bg-primary-container/20 border-r-2 border-primary font-semibold" 
              : "text-on-surface-variant dark:text-outline hover:text-on-surface hover:bg-surface-container-low"
          }`}
        >
          <span className="material-symbols-outlined text-[20px]" style={isGraphActive ? { fontVariationSettings: "'FILL' 1" } : {}}>
            hub
          </span>
          <span className="font-label-md text-label-md">Graph Topology</span>
        </Link>

        {/* Settings */}
        <Link 
          href="/settings" 
          onClick={close}
          className={`flex items-center gap-[12px] py-[10px] px-md transition-all duration-200 ease-in-out group ${
            isSettingsActive 
              ? "text-primary dark:text-primary-fixed bg-surface-variant/50 dark:bg-primary-container/20 border-r-2 border-primary font-semibold" 
              : "text-on-surface-variant dark:text-outline hover:text-on-surface hover:bg-surface-container-low"
          }`}
        >
          <span className="material-symbols-outlined text-[20px]" style={isSettingsActive ? { fontVariationSettings: "'FILL' 1" } : {}}>
            settings
          </span>
          <span className="font-label-md text-label-md">Settings</span>
        </Link>
      </nav>

      <div className="mt-auto flex flex-col gap-xs border-t border-outline-variant/10 pt-lg">
        <Link href="/help" onClick={close} className="flex items-center gap-[12px] py-sm px-md text-on-surface-variant hover:text-on-surface hover:bg-surface-container-low transition-colors group">
          <span className="material-symbols-outlined text-[20px]">help_outline</span>
          <span className="font-label-md text-label-md">Help</span>
        </Link>
        <div className="flex items-center gap-[12px] py-sm px-md text-on-surface-variant group">
          <span className="material-symbols-outlined text-[20px]">sensors</span>
          <div className="flex items-center gap-xs">
            <span className="font-label-md text-label-md">Status</span>
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                backendOnline === null
                  ? "bg-outline animate-pulse"
                  : backendOnline
                  ? "bg-secondary-fixed-dim animate-pulse"
                  : "bg-error"
              }`}
            />
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-[12px] py-sm px-md text-on-surface-variant hover:text-error hover:bg-error-container/20 transition-colors w-full text-left"
        >
          <span className="material-symbols-outlined text-[20px]">logout</span>
          <span className="font-label-md text-label-md">Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
