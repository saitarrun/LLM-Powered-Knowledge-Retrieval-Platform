import assert from "node:assert/strict";
import test from "node:test";

import {
  getGraphHealthState,
  getGraphNodeColor,
  normalizeGraphPayload,
} from "../src/app/graph/graphHealth.js";

test("normalizes missing graph payload into empty state", () => {
  const graph = normalizeGraphPayload(null);

  assert.deepEqual(graph.nodes, []);
  assert.deepEqual(graph.links, []);
  assert.equal(getGraphHealthState(graph).status, "empty");
});

test("classifies unavailable and partial graph health", () => {
  assert.equal(
    getGraphHealthState({
      nodes: [],
      links: [],
      health: { status: "unavailable", neo4j_available: false },
    }).status,
    "unavailable",
  );

  assert.equal(
    getGraphHealthState({
      nodes: [{ id: "doc-1", type: "document" }],
      links: [],
      health: { status: "partial", partial_extraction: true },
    }).status,
    "partial",
  );
});

test("maps graph node types to distinct colors", () => {
  assert.equal(getGraphNodeColor({ type: "document" }), "#2563eb");
  assert.equal(getGraphNodeColor({ type: "chunk" }), "#059669");
  assert.equal(getGraphNodeColor({ type: "entity" }), "#f0c419");
  assert.equal(getGraphNodeColor({ type: "relationship" }), "#7c3aed");
});
