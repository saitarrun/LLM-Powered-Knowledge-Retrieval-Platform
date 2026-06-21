"use client";

import Link from "next/link";
import { useSidebar } from "@/components/NavigationWrapper";

const FAQ = [
  {
    q: "How do I upload a document?",
    a: "Go to the Knowledge Base page and click 'Upload New Document'. Supported formats are PDF, DOCX, TXT, and Markdown up to 50 MB.",
  },
  {
    q: "How does the RAG pipeline work?",
    a: "Uploaded documents are chunked, embedded into a FAISS vector index, and optionally mapped into a Neo4j knowledge graph. When you send a query, the system retrieves the most relevant chunks via hybrid (dense + sparse) search and feeds them as context to the LLM.",
  },
  {
    q: "What LLM is being used?",
    a: "By default the platform uses nvidia/nemotron-3-super-120b-a12b via OpenRouter. You can change the model by updating LLM_MODEL in the backend .env file.",
  },
  {
    q: "Why does my document show 'pending' status?",
    a: "The approval workflow is enabled. An administrator needs to approve the document via the Slack/n8n workflow before it is indexed.",
  },
  {
    q: "What is the Graph Topology view?",
    a: "It visualises document chunks and extracted entities as a force-directed graph powered by Neo4j. Requires Neo4j to be running.",
  },
  {
    q: "How do I reset the system?",
    a: "Stop all containers with 'docker-compose down', remove the data/ folder, then run 'docker-compose up -d' again.",
  },
];

export default function HelpPage() {
  const { toggle } = useSidebar();

  return (
    <main className="h-full flex flex-col relative overflow-hidden bg-surface-container-lowest">
      {/* Top Bar */}
      <header className="w-full h-16 sticky top-0 bg-surface/80 backdrop-blur-xl border-b border-outline-variant/30 flex items-center px-lg gap-sm z-40">
        <span
          className="material-symbols-outlined md:hidden cursor-pointer text-on-surface mr-2"
          onClick={toggle}
        >
          menu
        </span>
        <span className="material-symbols-outlined text-primary">help_outline</span>
        <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Help</h2>
      </header>

      <div className="flex-1 overflow-y-auto p-lg custom-scrollbar max-w-[800px] mx-auto w-full py-xl">
        <div className="mb-xl">
          <h1 className="font-headline-md text-headline-md text-on-surface mb-1">Help &amp; Documentation</h1>
          <p className="text-body-md text-outline">
            Frequently asked questions and quick-start guides for the Aether RAG platform.
          </p>
        </div>

        {/* Quick links */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-lg mb-xl">
          {[
            { icon: "upload_file", label: "Upload a document", href: "/documents" },
            { icon: "chat_bubble", label: "Start a chat", href: "/" },
            { icon: "settings", label: "Configure settings", href: "/settings" },
          ].map(({ icon, label, href }) => (
            <Link
              key={href}
              href={href}
              className="flex items-center gap-md p-md rounded-xl border border-outline-variant/20 bg-surface-container-lowest hover:bg-surface-container-low transition-colors shadow-sm"
            >
              <span className="material-symbols-outlined text-primary">{icon}</span>
              <span className="font-body-md text-body-md text-on-surface font-medium">{label}</span>
              <span className="material-symbols-outlined text-outline ml-auto text-sm">arrow_forward</span>
            </Link>
          ))}
        </div>

        {/* FAQ */}
        <h2 className="font-headline-sm text-headline-sm text-on-surface mb-lg">Frequently Asked Questions</h2>
        <div className="space-y-md">
          {FAQ.map(({ q, a }) => (
            <details
              key={q}
              className="group bg-surface-container-lowest rounded-xl border border-outline-variant/20 shadow-sm overflow-hidden"
            >
              <summary className="flex items-center justify-between px-lg py-md cursor-pointer list-none select-none hover:bg-surface-container-low transition-colors">
                <span className="font-body-md text-body-md font-semibold text-on-surface">{q}</span>
                <span className="material-symbols-outlined text-outline transition-transform group-open:rotate-180">
                  expand_more
                </span>
              </summary>
              <div className="px-lg pb-md pt-xs text-body-md text-on-surface-variant leading-relaxed border-t border-outline-variant/10">
                {a}
              </div>
            </details>
          ))}
        </div>

        <div className="mt-xl p-lg rounded-xl bg-primary/5 border border-primary/10 text-body-md text-on-surface-variant">
          Still stuck? Open an issue on{" "}
          <a
            href="https://github.com/saitarrun/LLM-Powered-Knowledge-Retrieval-Platform/issues"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary underline underline-offset-2"
          >
            GitHub
          </a>
          .
        </div>
      </div>
    </main>
  );
}
