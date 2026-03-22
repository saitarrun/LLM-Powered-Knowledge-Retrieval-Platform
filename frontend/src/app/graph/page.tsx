"use client";

import { useEffect, useState, useRef, useMemo } from "react";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { Network, Zap, Cpu, Activity, Shield, Box } from "lucide-react";

// Use dynamic import for ForceGraph2D to avoid SSR issues
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

export default function GraphPage() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const fgRef = useRef<any>();

  useEffect(() => {
    fetch("/nexus-proxy/documents/graph")
      .then(res => res.json())
      .then(data => {
        setGraphData(data);
        setLoading(false);
      });
  }, []);

  const nodeColor = (node: any) => {
    if (node.type === "Entity") return "#fdd029"; // Secondary/Gold
    return "#121212"; // Primary/Dark
  };

  return (
    <div className="max-w-6xl mx-auto h-[calc(100vh-160px)] flex flex-col gap-10">
      <div className="flex items-center justify-between pb-8 border-b border-on-surface/5">
        <div className="space-y-3">
          <div className="flex items-center gap-3 text-secondary">
             <Network size={24} className="animate-pulse-slow" />
             <span className="label-sm tracking-[0.6em] font-black uppercase">GraphRAG Topology</span>
          </div>
          <h1 className="display-md text-on-surface tracking-tighter">Neural Connectivity</h1>
        </div>
        <div className="flex gap-4">
           <div className="px-6 py-3 bg-primary-container text-secondary rounded-full border border-secondary/20 flex items-center gap-3">
              <Zap size={14} />
              <span className="label-sm tracking-[0.1em]">REAL-TIME MAPPING</span>
           </div>
        </div>
      </div>

      <div className="flex-1 bg-surface-container-lowest border border-on-surface/5 relative overflow-hidden group shadow-premium ring-1 ring-secondary/5">
         <div className="absolute inset-0 z-0 opacity-[0.03] pointer-events-none">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_#fdd029_0%,_transparent_70%)]" />
         </div>
         
         <div className="relative z-10 w-full h-full">
            {!loading && (
              <ForceGraph2D
                ref={fgRef}
                graphData={graphData}
                nodeLabel="id"
                nodeColor={nodeColor}
                linkColor={() => "#efeeeb"}
                linkWidth={1.5}
                nodeRelSize={8}
                backgroundColor="#ffffff"
                d3VelocityDecay={0.3}
              />
            )}
         </div>

         {/* Overlay Module */}
         <div className="absolute bottom-10 left-10 right-10 flex justify-between items-end pointer-events-none">
            <div className="p-8 bg-surface/80 backdrop-blur-xl border border-outline-variant shadow-lg max-w-xs space-y-4 pointer-events-auto">
               <div className="flex items-center gap-3 text-primary">
                  <Cpu size={18} />
                  <span className="label-md tracking-widest font-black uppercase text-[11px]">System Analytics</span>
               </div>
               <p className="text-secondary font-display text-4xl font-bold tracking-tight">
                  {graphData.nodes.length} <span className="text-on-surface/20 text-xl font-normal">Entities</span>
               </p>
               <div className="w-full h-px bg-on-surface/5" />
               <div className="flex justify-between items-center text-[9px] font-black tracking-[0.4em] uppercase opacity-40">
                  <span>Knowledge Triples</span>
                  <span>{graphData.links.length}</span>
               </div>
            </div>

            <div className="flex flex-col gap-4 items-end">
               <div className="flex gap-4 mb-4">
                  <LegendItem color="#fdd029" label="Entities" />
                  <LegendItem color="#121212" label="Relations" />
               </div>
               <div className="px-8 py-4 bg-primary text-secondary rounded-full shadow-2xl flex items-center gap-4 border border-secondary/20 font-black tracking-widest uppercase text-[10px] pointer-events-auto cursor-pointer hover:scale-105 active:scale-95 transition-all">
                  <Activity size={14} />
                  Optimize Layout
               </div>
            </div>
         </div>
      </div>
    </div>
  );
}

function LegendItem({ color, label }: any) {
  return (
    <div className="flex items-center gap-3 bg-surface/60 backdrop-blur-md px-5 py-2.5 rounded-full border border-outline-variant">
       <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
       <span className="label-sm opacity-60 text-[9px] tracking-widest">{label}</span>
    </div>
  );
}
