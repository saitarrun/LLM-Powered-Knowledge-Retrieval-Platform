"use client";

import { motion } from "framer-motion";
import { 
  Cpu, 
  Zap, 
  Database, 
  Network, 
  ArrowRight, 
  Terminal, 
  ShieldCheck, 
  Activity,
  ChevronRight,
  Globe,
  Fingerprint
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/services/api";

export default function Home() {
  const [stats, setStats] = useState({ documents: 0, indexed_chunks: 0 });

  useEffect(() => {
    api.getStatus().then(setStats);
  }, []);

  return (
    <div className="max-w-7xl mx-auto space-y-32 pb-40">
      {/* Hero Module: The Nexus Core */}
      <section className="relative pt-20">
        <div className="grid grid-cols-12 gap-12 items-center">
          <div className="col-span-8 space-y-16">
            <div className="space-y-6">
              <motion.div 
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-center gap-4 text-secondary"
              >
                <Fingerprint size={28} className="animate-pulse-slow" />
                <span className="label-md tracking-[0.8em] font-black uppercase">Multi-Agent RAG Platform v4.0</span>
              </motion.div>
              
              <motion.h1 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="display-lg text-[6.5rem] leading-[0.9] text-on-surface tracking-tighter"
              >
                Orchestrate <br /> <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">Intelligence.</span>
              </motion.h1>
              
              <motion.p 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="text-2xl text-on-surface-variant max-w-2xl font-medium leading-relaxed opacity-60"
              >
                Enterprise-grade knowledge retrieval platform powered by a dynamic swarm of specialized agents, GraphRAG topology, and deterministic validation.
              </motion.p>
            </div>

            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.4 }}
              className="flex gap-8"
            >
              <Link href="/chat" className="btn-primary min-w-[320px] h-16 flex items-center justify-center gap-4 shadow-[0_20px_60px_rgba(27,28,26,0.15)] group">
                Initialize Swarm
                <ArrowRight size={20} className="group-hover:translate-x-2 transition-transform" />
              </Link>
              <Link href="/documents" className="px-12 py-5 border-2 border-on-surface/5 rounded-full font-display font-black tracking-widest uppercase hover:bg-surface-container transition-all flex items-center gap-4 group h-16">
                Knowledge Base
                <Database size={18} className="text-secondary group-hover:scale-110 transition-transform" />
              </Link>
            </motion.div>
          </div>

          <div className="col-span-4 relative h-[600px] flex items-center justify-center">
             <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_#fdd029_0%,_transparent_70%)] opacity-[0.04]" />
             <div className="relative group">
                <motion.div 
                  animate={{ rotate: 360 }}
                  transition={{ duration: 60, repeat: Infinity, ease: "linear" }}
                  className="w-96 h-96 border border-dashed border-on-surface/10 rounded-full flex items-center justify-center"
                >
                   <div className="w-80 h-80 border border-secondary/20 rounded-full flex items-center justify-center animate-pulse-slow">
                      <div className="w-64 h-64 bg-primary rounded-full flex items-center justify-center shadow-premium-dark">
                         <Zap size={64} className="text-secondary animate-pulse" />
                      </div>
                   </div>
                </motion.div>
                {/* Orbital Sensors */}
                <OrbitalSensor icon={Search} label="RETRIEVAL" position="top-0 left-0" />
                <OrbitalSensor icon={Network} label="GRAPH" position="top-0 right-0" />
                <OrbitalSensor icon={ShieldCheck} label="VALIDATION" position="bottom-0 left-0" />
                <OrbitalSensor icon={Globe} label="WEB SEARCH" position="bottom-0 right-0" />
             </div>
          </div>
        </div>
      </section>

      {/* Stats Module: The Data Horizon */}
      <section className="bg-primary text-secondary p-1 relative overflow-hidden shadow-premium-dark">
         <div className="grid grid-cols-1 md:grid-cols-4 gap-1">
            <StatModule label="Vector Space" value={stats.indexed_chunks.toLocaleString()} metric="TOTAL CHUNKS" />
            <StatModule label="Knowledge Assets" value={stats.documents} metric="CATALOGED FILES" />
            <StatModule label="Neural Links" value="14.2k" metric="GRAPH TRIPLES" />
            <StatModule label="System Uptime" value="99.9%" metric="STABILITY" />
         </div>
      </section>

      {/* Feature Architecture: The Swarm Principles */}
      <section className="space-y-20">
         <div className="flex items-center gap-6">
            <div className="w-20 h-px bg-secondary" />
            <h2 className="label-md tracking-[0.6em] text-on-surface font-black uppercase text-xl">Core Architecture</h2>
         </div>

         <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            <FeatureCard 
               icon={Cpu}
               title="Multi-Agent Swarm"
               desc="Coordinated task decomposition across specialized agents: Orion (Planning), Critic (Verification), and Synthesis."
            />
            <FeatureCard 
               icon={Network}
               title="GraphRAG Topology"
               desc="Implicit knowledge mapping via Neo4j, enabling higher-order reasoning across disconnected document segments."
            />
            <FeatureCard 
               icon={ShieldCheck}
               title="Trusted Validation"
               desc="Deterministic verification layer that cross-references all LLM outputs with retrieved source citations."
            />
         </div>
      </section>
    </div>
  );
}

function OrbitalSensor({ icon: Icon, label, position }: any) {
  return (
    <div className={`absolute ${position} group-hover:scale-110 transition-transform duration-700 pointer-events-none`}>
       <div className="p-4 bg-surface shadow-premium border border-on-surface/5 rounded-2xl flex items-center gap-3">
          <Icon size={16} className="text-secondary" />
          <span className="label-sm tracking-widest text-on-surface/40 uppercase text-[9px] font-bold">{label}</span>
       </div>
    </div>
  );
}

function StatModule({ label, value, metric }: any) {
  return (
    <div className="bg-primary p-12 flex flex-col gap-6 group hover:bg-neutral-900 transition-colors">
       <span className="label-sm opacity-40 tracking-[0.4em] font-black group-hover:text-secondary transition-colors">{label}</span>
       <div className="space-y-1">
          <h4 className="text-6xl font-display font-medium text-on-primary-fixed">{value}</h4>
          <p className="label-sm text-secondary font-black tracking-widest text-[10px]">{metric}</p>
       </div>
    </div>
  );
}

function FeatureCard({ icon: Icon, title, desc }: any) {
  return (
    <div className="p-12 bg-surface shadow-[0_4px_30px_rgba(18,18,18,0.03)] border-t-2 border-primary-container group hover:-translate-y-4 transition-all duration-700 min-h-[360px] flex flex-col justify-between">
       <div className="space-y-8">
          <div className="w-16 h-16 bg-surface-container-low flex items-center justify-center rounded-3xl group-hover:bg-secondary transition-colors duration-700">
             <Icon size={28} className="text-primary group-hover:text-primary transition-colors" strokeWidth={1} />
          </div>
          <div className="space-y-4">
             <h3 className="headline-md tracking-tight group-hover:text-primary transition-colors">{title}</h3>
             <p className="body-lg opacity-40 leading-relaxed font-medium">{desc}</p>
          </div>
       </div>
       <div className="pt-8 border-t border-on-surface/5 flex items-center gap-3 text-secondary opacity-0 group-hover:opacity-100 transition-opacity">
          <span className="label-sm font-black tracking-widest">Explore Protocol</span>
          <ChevronRight size={14} />
       </div>
    </div>
  );
}
