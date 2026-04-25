export function normalizeGraphPayload(payload) {
  return {
    nodes: Array.isArray(payload?.nodes) ? payload.nodes : [],
    links: Array.isArray(payload?.links) ? payload.links : [],
    health: payload?.health || {},
  };
}

export function getGraphHealthState(graph) {
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

export function getGraphNodeColor(node) {
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

export function getGraphLinkColor(link) {
  if (link?.type === "HAS_CHUNK") return "#93c5fd";
  if (link?.type === "MENTIONS") return "#86efac";
  return "#d6d3d1";
}
