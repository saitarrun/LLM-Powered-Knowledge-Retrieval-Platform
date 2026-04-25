"use client";

import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { Activity, AlertTriangle, Cpu, FileText, Layers, Network, Shield, Zap } from "lucide-react";
import {
  getGraphHealthState,
  getGraphLinkColor,
  getGraphNodeColor,
  normalizeGraphPayload,
} from "./graphHealth";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

type GraphNode = {
  id: string;
  label?: string;
  type?: string;
  x?: number;
  y?: number;
};

type GraphLink = {
  source: string;
  target: string;
  type?: string;
};

type GraphHealth = {
  status?: string;
  neo4j_available?: boolean;
  node_count?: number;
  relationship_count?: number;
  document_count?: number;
  chunk_count?: number;
  entity_count?: number;
  disconnected_document_count?: number;
  partial_extraction?: boolean;
};

type GraphPayload = {
  nodes: GraphNode[];
  links: GraphLink[];
  health: GraphHealth;
};

export default function GraphPage() {
  const [graphData, setGraphData] = useState<GraphPayload>({ nodes: [], links: [], health: {} });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fgRef = useRef<{ zoomToFit?: (duration?: number, padding?: number) => void } | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadGraph() {
      try {
        const res = await fetch("/nexus-proxy/v1/documents/graph");
        const data = await res.json();
        if (cancelled) return;
        setGraphData(normalizeGraphPayload(data));
        setError(res.ok ? null : "Graph endpoint returned an error.");
      } catch {
        if (cancelled) return;
        setGraphData(normalizeGraphPayload({
          health: { status: "unavailable", neo4j_available: false },
        }));
        setError("Graph endpoint could not be reached.");
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadGraph();
    return () => {
      cancelled = true;
    };
  }, []);

  const healthState = getGraphHealthState(graphData);
  const metrics = graphData.health || {};
  const isGraphVisible = !loading && graphData.nodes.length > 0 && healthState.status !== "unavailable";

  const focusLayout = () => {
    fgRef.current?.zoomToFit?.(500, 60);
  };

  const drawNode = (node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const label = node.label || node.id;
    const fontSize = Math.max(10 / globalScale, 3);
    const radius = node.type === "document" ? 7 : node.type === "chunk" ? 5 : 6;

    ctx.beginPath();
    ctx.arc(node.x ?? 0, node.y ?? 0, radius, 0, 2 * Math.PI, false);
    ctx.fillStyle = getGraphNodeColor(node);
    ctx.fill();
    ctx.font = `${fontSize}px Inter, sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillStyle = "rgba(18,18,18,0.72)";
    ctx.fillText(label, node.x ?? 0, (node.y ?? 0) + radius + 2);
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
          <div className={`px-6 py-3 rounded-full border flex items-center gap-3 ${
            healthState.status === "healthy"
              ? "bg-primary-container text-secondary border-secondary/20"
              : healthState.status === "partial"
                ? "bg-yellow-50 text-yellow-700 border-yellow-200"
                : "bg-red-50 text-red-600 border-red-100"
          }`}>
            <Zap size={14} />
            <span className="label-sm tracking-[0.1em] uppercase">{healthState.title}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <MetricCard label="Documents" value={metrics.document_count ?? 0} icon={FileText} />
        <MetricCard label="Chunks" value={metrics.chunk_count ?? 0} icon={Layers} />
        <MetricCard label="Entities" value={metrics.entity_count ?? graphData.nodes.length} icon={Cpu} />
        <MetricCard label="Relationships" value={metrics.relationship_count ?? graphData.links.length} icon={Network} />
      </div>

      <div className="flex-1 bg-surface-container-lowest border border-on-surface/5 relative overflow-hidden group shadow-premium ring-1 ring-secondary/5">
        <div className="absolute inset-0 z-0 opacity-[0.03] pointer-events-none">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_#fdd029_0%,_transparent_70%)]" />
        </div>

        <div className="relative z-10 w-full h-full">
          {isGraphVisible && (
            <ForceGraph2D
              ref={fgRef}
              graphData={graphData}
              nodeLabel={(node: GraphNode) => `${node.label || node.id} (${node.type || "node"})`}
              nodeColor={getGraphNodeColor}
              linkColor={getGraphLinkColor}
              linkWidth={1.5}
              nodeRelSize={8}
              backgroundColor="#ffffff"
              d3VelocityDecay={0.3}
              nodeCanvasObject={drawNode}
              linkDirectionalArrowLength={4}
              linkDirectionalArrowRelPos={1}
            />
          )}

          {!isGraphVisible && (
            <div className="h-full flex flex-col items-center justify-center text-center gap-6 p-12">
              {loading ? (
                <>
                  <Activity size={44} className="text-secondary animate-pulse" />
                  <div>
                    <p className="label-md tracking-[0.4em] uppercase opacity-40">Loading topology</p>
                    <p className="text-sm opacity-40 mt-2">Reading graph health and relationships.</p>
                  </div>
                </>
              ) : (
                <>
                  <AlertTriangle size={44} className={healthState.status === "unavailable" ? "text-red-500" : "text-secondary"} />
                  <div className="max-w-md">
                    <p className="text-2xl font-display text-on-surface">{healthState.title}</p>
                    <p className="text-sm opacity-50 mt-3 leading-relaxed">
                      {error || healthState.message}
                    </p>
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        <div className="absolute bottom-10 left-10 right-10 flex justify-between items-end pointer-events-none">
          <div className="p-8 bg-surface/80 backdrop-blur-xl border border-outline-variant shadow-lg max-w-xs space-y-4 pointer-events-auto">
            <div className="flex items-center gap-3 text-primary">
              <Shield size={18} />
              <span className="label-md tracking-widest font-black uppercase text-[11px]">Graph Health</span>
            </div>
            <p className="text-secondary font-display text-4xl font-bold tracking-tight">
              {metrics.node_count ?? graphData.nodes.length} <span className="text-on-surface/20 text-xl font-normal">Nodes</span>
            </p>
            <div className="w-full h-px bg-on-surface/5" />
            <div className="space-y-2 text-[9px] font-black tracking-[0.25em] uppercase opacity-50">
              <div className="flex justify-between items-center">
                <span>Disconnected Docs</span>
                <span>{metrics.disconnected_document_count ?? 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Partial Extraction</span>
                <span>{metrics.partial_extraction ? "YES" : "NO"}</span>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-4 items-end">
            <div className="flex flex-wrap gap-4 mb-4 justify-end">
              <LegendItem color="#2563eb" label="Documents" />
              <LegendItem color="#059669" label="Chunks" />
              <LegendItem color="#f0c419" label="Entities" />
              <LegendItem color="#7c3aed" label="Relationships" />
            </div>
            <button
              type="button"
              onClick={focusLayout}
              className="px-8 py-4 bg-primary text-secondary rounded-full shadow-2xl flex items-center gap-4 border border-secondary/20 font-black tracking-widest uppercase text-[10px] pointer-events-auto cursor-pointer hover:scale-105 active:scale-95 transition-all"
            >
              <Activity size={14} />
              Optimize Layout
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value, icon: Icon }: { label: string; value: number; icon: typeof Network }) {
  return (
    <div className="bg-surface border border-on-surface/5 shadow-premium p-5 flex items-center justify-between">
      <div>
        <p className="label-sm text-[9px] tracking-[0.3em] opacity-35 uppercase">{label}</p>
        <p className="text-2xl font-display text-on-surface mt-1">{value}</p>
      </div>
      <Icon size={18} className="text-secondary" />
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-3 bg-surface/60 backdrop-blur-md px-5 py-2.5 rounded-full border border-outline-variant">
      <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
      <span className="label-sm opacity-60 text-[9px] tracking-widest">{label}</span>
    </div>
  );
}
