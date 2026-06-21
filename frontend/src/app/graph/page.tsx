"use client";

import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import type { ForceGraphMethods, NodeObject } from "react-force-graph-2d";
import { Activity, AlertTriangle, Cpu, FileText, Layers, Network, Shield, Zap, type LucideIcon } from "lucide-react";
import { useSidebar } from "@/components/NavigationWrapper";
import {
  getGraphHealthState,
  getGraphLinkColor,
  getGraphNodeColor,
  normalizeGraphPayload,
  GraphPayload,
} from "./graphHealth";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

type ForceGraphNode = NodeObject<{
  label?: string;
  type?: string;
}>;

export default function GraphPage() {
  const [graphData, setGraphData] = useState<GraphPayload>({ nodes: [], links: [], health: {} });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fgRef = useRef<ForceGraphMethods | undefined>(undefined);
  const { toggle } = useSidebar();

  useEffect(() => {
    let cancelled = false;

    async function loadGraph() {
      try {
        const res = await fetch("/nexus-proxy/documents/graph");
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

  const drawNode = (node: ForceGraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const label = node.label || String(node.id ?? "");
    const fontSize = Math.max(10 / globalScale, 3);
    const radius = node.type === "document" ? 7 : node.type === "chunk" ? 5 : 6;

    ctx.beginPath();
    ctx.arc(node.x ?? 0, node.y ?? 0, radius, 0, 2 * Math.PI, false);
    ctx.fillStyle = getGraphNodeColor({ id: String(node.id ?? ""), label: node.label, type: node.type });
    ctx.fill();
    ctx.font = `${fontSize}px Inter, sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillStyle = "rgba(18,18,18,0.72)";
    ctx.fillText(label, node.x ?? 0, (node.y ?? 0) + radius + 2);
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
          <span className="material-symbols-outlined text-primary">hub</span>
          <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Graph Topology</h2>
        </div>
      </header>

      {/* Page Canvas */}
      <div className="flex-1 overflow-y-auto p-lg custom-scrollbar flex flex-col gap-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-outline-variant/20 gap-4">
          <div className="space-y-1">
            <h1 className="text-2xl font-bold text-on-surface tracking-tight">Neural Connectivity</h1>
            <p className="text-body-md text-outline">Visualize document chunks and entity linkages in the vector space.</p>
          </div>
          <div className="flex gap-4">
            <div className={`px-4 py-2 rounded-full border flex items-center gap-2 ${
              healthState.status === "healthy"
                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                : healthState.status === "partial"
                  ? "bg-yellow-50 text-yellow-700 border-yellow-200"
                  : "bg-red-50 text-red-600 border-red-100"
            }`}>
              <Zap size={14} />
              <span className="text-xs font-bold uppercase tracking-wider">{healthState.title}</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="Documents" value={metrics.document_count ?? 0} icon={FileText} />
          <MetricCard label="Chunks" value={metrics.chunk_count ?? 0} icon={Layers} />
          <MetricCard label="Entities" value={metrics.entity_count ?? graphData.nodes.length} icon={Cpu} />
          <MetricCard label="Relationships" value={metrics.relationship_count ?? graphData.links.length} icon={Network} />
        </div>

        <div className="flex-1 min-h-[450px] bg-white rounded-xl border border-outline-variant/20 relative overflow-hidden group shadow-sm flex flex-col">
          <div className="absolute inset-0 z-0 opacity-[0.03] pointer-events-none">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_#2563eb_0%,_transparent_70%)]" />
          </div>

          <div className="relative z-10 w-full flex-grow h-[450px]">
            {isGraphVisible && (
              <ForceGraph2D
                ref={fgRef}
                graphData={graphData}
                nodeLabel={(node: ForceGraphNode) => `${node.label || node.id} (${node.type || "node"})`}
                nodeColor={(node: ForceGraphNode) =>
                  getGraphNodeColor({ id: String(node.id ?? ""), label: node.label, type: node.type })
                }
                linkColor={(link) =>
                  getGraphLinkColor({ source: String((link as { source: unknown }).source ?? ""), target: String((link as { target: unknown }).target ?? ""), type: (link as { type?: string }).type })
                }
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
                    <Activity size={44} className="text-primary animate-pulse" />
                    <div>
                      <p className="text-xs font-bold tracking-widest uppercase opacity-40">Loading topology</p>
                      <p className="text-sm opacity-40 mt-2">Reading graph health and relationships.</p>
                    </div>
                  </>
                ) : (
                  <>
                    <AlertTriangle size={44} className={healthState.status === "unavailable" ? "text-red-500" : "text-amber-500"} />
                    <div className="max-w-md">
                      <p className="text-xl font-bold text-on-surface">{healthState.title}</p>
                      <p className="text-sm opacity-50 mt-3 leading-relaxed">
                        {error || healthState.message}
                      </p>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>

          <div className="absolute bottom-4 left-4 right-4 flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 pointer-events-none">
            <div className="p-4 bg-white/90 backdrop-blur-md border border-outline-variant/30 rounded-xl shadow-md max-w-xs w-full space-y-2 pointer-events-auto">
              <div className="flex items-center gap-2 text-primary">
                <Shield size={14} />
                <span className="text-[10px] font-bold tracking-wider uppercase">Graph Status</span>
              </div>
              <p className="font-semibold text-on-surface text-2xl tracking-tight">
                {metrics.node_count ?? graphData.nodes.length} <span className="text-outline text-sm font-normal">Nodes</span>
              </p>
              <div className="w-full h-px bg-outline-variant/30" />
              <div className="space-y-1 text-[9px] font-bold tracking-wide uppercase opacity-60">
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

            <div className="flex flex-col gap-3 items-end w-full sm:w-auto pointer-events-auto">
              <div className="flex flex-wrap gap-2 justify-end">
                <LegendItem color="#2563eb" label="Documents" />
                <LegendItem color="#059669" label="Chunks" />
                <LegendItem color="#f0c419" label="Entities" />
                <LegendItem color="#7c3aed" label="Relationships" />
              </div>
              {isGraphVisible && (
                <button
                  type="button"
                  onClick={focusLayout}
                  className="px-4 py-2 bg-primary text-on-primary rounded-xl shadow-md flex items-center gap-2 text-xs font-semibold hover:bg-primary/95 active:scale-95 transition-all pointer-events-auto cursor-pointer"
                >
                  <Activity size={12} />
                  Optimize Layout
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

function MetricCard({ label, value, icon: Icon }: { label: string; value: number; icon: LucideIcon }) {
  return (
    <div className="bg-white border border-outline-variant/20 rounded-xl p-4 flex items-center justify-between shadow-sm">
      <div>
        <p className="text-[10px] tracking-wider opacity-60 uppercase font-bold">{label}</p>
        <p className="text-xl font-bold text-on-surface mt-1">{value}</p>
      </div>
      <div className="bg-primary/5 p-2 rounded-lg text-primary">
        <Icon size={16} />
      </div>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-2 bg-white/80 backdrop-blur-sm px-3 py-1 rounded-full border border-outline-variant/30 text-[10px] font-medium text-on-surface-variant shadow-sm">
      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
      <span>{label}</span>
    </div>
  );
}
