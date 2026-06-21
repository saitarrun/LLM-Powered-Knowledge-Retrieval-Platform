export interface GraphNode {
  id: string;
  label?: string;
  type?: string;
  x?: number;
  y?: number;
}

export interface GraphLink {
  source: string;
  target: string;
  type?: string;
}

export interface GraphHealth {
  status?: string;
  neo4j_available?: boolean;
  node_count?: number;
  relationship_count?: number;
  document_count?: number;
  chunk_count?: number;
  entity_count?: number;
  disconnected_document_count?: number;
  partial_extraction?: boolean;
}

export interface GraphPayload {
  nodes: GraphNode[];
  links: GraphLink[];
  health: GraphHealth;
}

export interface HealthState {
  status: "unavailable" | "partial" | "empty" | "healthy";
  title: string;
  message: string;
}

export function normalizeGraphPayload(payload: Partial<GraphPayload> | null | undefined): GraphPayload {
  return {
    nodes: Array.isArray(payload?.nodes) ? payload.nodes : [],
    links: Array.isArray(payload?.links) ? payload.links : [],
    health: payload?.health || {},
  };
}

export function getGraphHealthState(graph: GraphPayload): HealthState {
  const normalized = normalizeGraphPayload(graph);
  const health = normalized.health;

  if (health.status === "unavailable" || health.neo4j_available === false) {
    return {
      status: "unavailable",
      title: "Neo4j unavailable",
      message: "Graph topology cannot be loaded right now.",
    };
  }

  if (health.status === "partial" || health.partial_extraction) {
    return {
      status: "partial",
      title: "Partial extraction",
      message: "Some documents or entities are missing from the graph.",
    };
  }

  if (normalized.nodes.length === 0) {
    return {
      status: "empty",
      title: "Graph is empty",
      message: "No graph nodes or relationships have been extracted yet.",
    };
  }

  return {
    status: "healthy",
    title: "Graph healthy",
    message: "Knowledge graph topology is available.",
  };
}

export function getGraphNodeColor(node: GraphNode): string {
  switch (node?.type) {
    case "document":
      return "#2563eb";
    case "chunk":
      return "#059669";
    case "entity":
      return "#f0c419";
    case "relationship":
      return "#7c3aed";
    default:
      return "#121212";
  }
}

export function getGraphLinkColor(link: GraphLink): string {
  if (link?.type === "HAS_CHUNK") return "#93c5fd";
  if (link?.type === "MENTIONS") return "#86efac";
  return "#d6d3d1";
}
