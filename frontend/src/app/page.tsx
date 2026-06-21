"use client";

import React, { useState, useRef, useEffect, FormEvent } from "react";
import { useSidebar } from "@/components/NavigationWrapper";
import { authHeader } from "@/services/auth";

type Citation = {
  id?: string | number;
  chunk_id?: string;
  document_id?: string;
  document_name?: string;
  chunk_text?: string;
  snippet?: string;
  page?: string | number;
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
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
      try {
        return JSON.parse(data) as StreamEvent;
      } catch {
        return null;
      }
    })
    .filter(Boolean) as StreamEvent[];

  return { events, remainder };
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [modelName, setModelName] = useState<string>("Loading...");

  const { toggle } = useSidebar();
  const sectionRef = useRef<HTMLElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    fetch("/api/health", { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => {
        if (d.llm_model) {
          // Show just the model slug, e.g. "nemotron-3-ultra-550b-a55b"
          const slug = d.llm_model.split("/").pop()?.replace(/:.*$/, "") ?? d.llm_model;
          setModelName(slug);
        }
      })
      .catch(() => setModelName("Unknown"));
  }, []);

  useEffect(() => {
    const el = sectionRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, isIndexing]);

  useEffect(() => {
    const handleNewChat = () => {
      setMessages([]);
      setQuery("");
      setIsIndexing(false);
    };
    window.addEventListener("new-chat", handleNewChat);
    return () => window.removeEventListener("new-chat", handleNewChat);
  }, []);

  const handleInput = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const form = e.currentTarget.form;
      if (form) form.requestSubmit();
    }
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const userMsg: ChatMessage = { role: "user", content: query };
    setMessages((prev) => [...prev, userMsg]);
    setQuery("");
    setLoading(true);
    setIsIndexing(true);

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    try {
      const response = await fetch("/nexus-proxy/chat/query/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeader() },
        body: JSON.stringify({ query: userMsg.content, top_k: 5 }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Chat failed with status ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      const assistantMsg: ChatMessage = { role: "assistant", content: "", citations: [] };
      setMessages((prev) => [...prev, assistantMsg]);

      let pendingBuffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        pendingBuffer += decoder.decode(value, { stream: true });
        const { events, remainder } = parseSseEvents(pendingBuffer);
        pendingBuffer = remainder;

        for (const event of events) {
          if (event.type === "token") {
            assistantMsg.content += event.token ?? event.data ?? "";
            setMessages((prev) => {
              const newMsgs = [...prev];
              newMsgs[newMsgs.length - 1] = { ...assistantMsg };
              return newMsgs;
            });
            setIsIndexing(false);
          } else if (event.type === "citations") {
            assistantMsg.citations = event.citations ?? event.data ?? [];
            setMessages((prev) => {
              const newMsgs = [...prev];
              newMsgs[newMsgs.length - 1] = { ...assistantMsg };
              return newMsgs;
            });
          } else if (event.type === "error") {
            throw new Error(event.message || "Streaming failed");
          }
        }
      }
    } catch (err) {
      console.error("Chat error:", err);
      const message = err instanceof Error ? err.message : "Connection failed";
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${message}` },
      ]);
    } finally {
      setLoading(false);
      setIsIndexing(false);
    }
  };

  return (
    <main className="flex-1 min-h-0 flex flex-col relative bg-surface-container-lowest">
      {/* Top Header */}
      <header className="w-full h-16 sticky top-0 bg-surface/80 dark:bg-surface-dim/80 backdrop-blur-xl border-b border-outline-variant/30 flex justify-between items-center px-lg z-50">
        <div className="flex items-center gap-md">
          <span
            className="material-symbols-outlined md:hidden cursor-pointer text-on-surface"
            onClick={toggle}
          >
            menu
          </span>
          <div className="flex flex-col">
            <span className="font-label-sm text-label-sm text-outline uppercase tracking-tighter">Current Model</span>
            <span className="font-headline-sm text-headline-sm font-semibold text-primary">{modelName}</span>
          </div>
        </div>
        <button className="w-10 h-10 rounded-full flex items-center justify-center hover:bg-surface-variant/50 transition-colors text-on-surface-variant">
          <span className="material-symbols-outlined">account_circle</span>
        </button>
      </header>

      {/* Chat Messages Canvas */}
      <section ref={sectionRef} className="flex-1 min-h-0 overflow-y-auto message-scroll">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center px-md text-center space-y-6 opacity-60">
            <span className="material-symbols-outlined text-6xl text-primary animate-pulse-subtle">
              auto_awesome
            </span>
            <div>
              <h3 className="font-headline-md text-headline-md font-bold text-on-surface">
                Synchronize with Aether
              </h3>
              <p className="text-body-lg text-outline mt-2">
                Enter your query below to retrieve context from the Knowledge Base.
              </p>
            </div>
          </div>
        ) : (
          <div className="max-w-[800px] mx-auto flex flex-col gap-xl px-md py-xl">
            <div className="flex items-center justify-center gap-md opacity-40 py-md">
              <div className="h-[1px] flex-1 bg-outline-variant" />
              <span className="font-label-sm text-label-sm uppercase tracking-widest">Today</span>
              <div className="h-[1px] flex-1 bg-outline-variant" />
            </div>

            {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`flex flex-col gap-sm group ${
                    msg.role === "user" ? "items-end" : "items-start"
                  }`}
                >
                  {msg.role === "assistant" && (
                    <div className="flex items-center gap-sm mb-xs">
                      <div className="w-6 h-6 rounded bg-primary-container flex items-center justify-center">
                        <span
                          className="material-symbols-outlined text-[14px] text-on-primary-container"
                          style={{ fontVariationSettings: "'FILL' 1" }}
                        >
                          smart_toy
                        </span>
                      </div>
                      <span className="font-label-md text-label-md font-semibold text-primary">
                        Aether Assistant
                      </span>
                    </div>
                  )}

                  <div
                    className={`p-md rounded-xl max-w-[85%] shadow-sm border border-outline-variant/10 ${
                      msg.role === "user"
                        ? "bg-surface-container-low rounded-tr-xs"
                        : "bg-white ai-border-accent rounded-tl-xs"
                    }`}
                  >
                    <p className="text-body-lg text-on-surface leading-relaxed whitespace-pre-wrap">
                      {msg.content}
                    </p>

                    {msg.role === "assistant" && !!msg.citations?.length && (
                      <div className="mt-xl pt-md border-t border-outline-variant/20">
                        <span className="text-label-sm font-label-sm text-outline uppercase tracking-wider block mb-sm">
                          Sources Found
                        </span>
                        <div className="flex flex-wrap gap-sm">
                          {msg.citations.map((cit, ci) => (
                            <a
                              key={ci}
                              className="flex items-center gap-xs px-md py-xs bg-surface-container-low hover:bg-surface-container text-primary rounded-full border border-outline-variant/30 transition-colors"
                              href="#"
                              onClick={(e) => e.preventDefault()}
                            >
                              <span className="material-symbols-outlined text-[14px]">description</span>
                              <span className="font-label-sm truncate max-w-[150px]">
                                {cit.document_name || "Reference"}
                              </span>
                              <span className="text-[10px] font-label-md bg-secondary-fixed text-on-secondary-fixed px-1.5 rounded">
                                {cit.page ? `Page ${cit.page}` : "Doc"}
                              </span>
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}

            {isIndexing && (
              <div className="flex items-center gap-md p-md bg-surface-variant/20 rounded-xl border border-dashed border-primary/20 max-w-fit animate-pulse-subtle">
                <div className="relative flex items-center justify-center">
                  <span className="absolute inline-flex h-full w-full rounded-full bg-secondary-fixed-dim opacity-75 animate-ping" />
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-secondary-fixed-dim" />
                </div>
                <span className="font-label-md text-label-md text-on-surface-variant italic">
                  Retrieving and indexing knowledge base...
                </span>
              </div>
            )}

          </div>
        )}
      </section>

      {/* Bottom Chat Input Form */}
      <footer className="p-md md:pb-lg">
        <div className="max-w-[800px] mx-auto relative">
          <form
            onSubmit={handleSubmit}
            className="bg-white rounded-3xl shadow-lg border border-outline-variant/30 p-sm pl-md flex items-end gap-sm focus-within:ring-2 focus-within:ring-secondary-fixed-dim/50 transition-all"
          >
            <textarea
              ref={textareaRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onInput={handleInput}
              onKeyDown={handleKeyPress}
              className="flex-1 bg-transparent border-none focus:ring-0 text-body-lg py-2 max-h-48 overflow-y-auto resize-none p-0 outline-none placeholder-outline-variant"
              placeholder="Ask Aether anything..."
              rows={1}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="w-10 h-10 mb-0.5 rounded-full bg-primary text-white flex items-center justify-center hover:bg-primary/90 transition-all active:scale-95 shadow-md shadow-primary/20 disabled:opacity-30 disabled:scale-100"
            >
              <span
                className="material-symbols-outlined"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                send
              </span>
            </button>
          </form>
          <div className="mt-xs text-center">
            <p className="text-label-sm text-outline opacity-60 text-[11px]">
              Aether AI can make mistakes. Verify important information.
            </p>
          </div>
        </div>
      </footer>

      <div className="absolute -right-64 -top-64 w-[500px] h-[500px] bg-secondary-fixed/10 blur-[120px] rounded-full pointer-events-none -z-10" />
      <div className="absolute -left-64 -bottom-64 w-[500px] h-[500px] bg-primary-fixed/20 blur-[120px] rounded-full pointer-events-none -z-10" />
    </main>
  );
}
