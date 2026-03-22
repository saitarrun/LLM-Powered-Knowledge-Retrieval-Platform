import type { Metadata } from "next";
import { Inter, Newsreader, Manrope } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { 
  BarChart3, 
  MessageSquare, 
  Database, 
  Network, 
  Settings, 
  Zap,
  Globe,
  Cpu
} from "lucide-react";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const newsreader = Newsreader({ subsets: ["latin"], weight: ["400", "700"], style: ["italic", "normal"], variable: "--font-newsreader" });
const manrope = Manrope({ subsets: ["latin"], variable: "--font-manrope" });

export const metadata: Metadata = {
  title: "Nexus | RAG Multi-Agent Orchestrator",
  description: "Enterprise-grade knowledge retrieval and swarm intelligence",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="bg-primary-surface">
      <body className={`${inter.variable} ${newsreader.variable} ${manrope.variable} font-body antialiased text-primary selection:bg-secondary/20`}>
        <div className="flex min-h-screen">
          {/* Vertical Command Interface (Sidebar) */}
          <aside className="w-96 flex-shrink-0 border-r border-on-surface/5 flex flex-col h-screen fixed">
            <div className="px-10 h-36 flex items-center flex-shrink-0 relative overflow-hidden">
               <div className="absolute -top-10 -left-10 w-32 h-32 bg-secondary/10 blur-3xl rounded-full" />
               <Link href="/" className="flex items-center gap-5 group relative z-10">
                  <div className="w-14 h-14 bg-primary-container flex items-center justify-center rounded-[1.2rem] shadow-premium group-hover:rotate-90 transition-transform duration-700">
                     <Zap size={22} className="text-secondary" />
                  </div>
                  <div className="flex flex-col">
                     <span className="text-3xl font-display font-black tracking-tighter leading-none">NEXUS</span>
                     <span className="label-sm text-on-surface/30 tracking-[0.4em] font-black uppercase text-[10px]">Multi-Agent OS</span>
                  </div>
               </Link>
            </div>

            <nav className="flex-1 px-8 py-10 space-y-4">
               <NavItem href="/" icon={BarChart3} label="Dashboard" />
               <NavItem href="/chat" icon={MessageSquare} label="Neural Swarm" />
               <NavItem href="/documents" icon={Database} label="Knowledge Archive" />
               <NavItem href="/graph" icon={Network} label="Neural Topology" />
            </nav>

            <div className="p-8 border-t border-on-surface/5 space-y-6">
               <Link href="/settings" className="flex items-center gap-4 px-6 py-4 rounded-3xl hover:bg-surface-container transition-all group">
                  <Settings size={18} className="text-on-surface/30 group-hover:text-primary group-hover:rotate-90 transition-all duration-700" />
                  <span className="label-md text-on-surface/50 group-hover:text-primary transition-colors tracking-widest font-black">System Protocols</span>
               </Link>
               
               <div className="px-8 py-8 bg-surface shadow-premium-dark rounded-[2.5rem] space-y-6 relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-24 h-24 bg-secondary/5 blur-2xl flex-shrink-0" />
                  <div className="flex items-center gap-3 relative z-10">
                     <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                     <span className="label-sm text-emerald-500 opacity-80 tracking-widest">Local Node Active</span>
                  </div>
                  <div className="space-y-2 relative z-10">
                    <p className="label-sm text-on-surface/30 uppercase text-[9px] font-black tracking-[0.2em]">Current Latency</p>
                    <p className="text-2xl font-display font-bold text-on-surface tracking-tight">4.2ms</p>
                  </div>
               </div>
            </div>
          </aside>

          {/* Main Viewport Interface */}
          <main className="flex-1 ml-96 min-h-screen bg-surface p-12 relative overflow-hidden">
             <div className="absolute top-0 right-0 w-full h-full opacity-[0.03] pointer-events-none">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_100%_0%,_#fdd029_0%,_transparent_50%)]" />
             </div>
             <div className="relative z-10 h-full">
               {children}
             </div>
          </main>
        </div>
      </body>
    </html>
  );
}

function NavItem({ href, icon: Icon, label }: { href: string, icon: any, label: string }) {
  return (
    <Link href={href} className="flex items-center gap-5 px-6 py-5 rounded-[2rem] hover:bg-surface-container transition-all group">
      <div className="w-10 h-10 flex items-center justify-center rounded-2xl group-hover:bg-primary transition-colors duration-700">
         <Icon size={18} className="text-on-surface/40 group-hover:text-secondary transition-colors" strokeWidth={1.5} />
      </div>
      <span className="label-md group-hover:text-primary transition-colors tracking-[0.2em] font-black uppercase text-[11px]">{label}</span>
      <div className="flex-1" />
      <div className="w-1.5 h-1.5 rounded-full bg-secondary opacity-0 group-hover:opacity-100 transition-opacity" />
    </Link>
  );
}
