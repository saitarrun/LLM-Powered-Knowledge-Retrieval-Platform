import assert from "node:assert/strict";
import test from "node:test";

import {
  getCitationLabel,
  getCitationSnippet,
  isCitationAvailable,
} from "../src/app/chat/citationHelpers.js";

test("citation helpers mark complete citations as available", () => {
  const citation = {
    available: true,
    document_id: "doc1",
    chunk_id: "chunk1",
    document_name: "Source.pdf",
    snippet: "A short source preview.",
  };

  assert.equal(isCitationAvailable(citation), true);
  assert.equal(getCitationLabel(citation), "Source.pdf - Chunk chunk1");
  assert.equal(getCitationSnippet(citation), "A short source preview.");
});

test("citation helpers render graceful unavailable state", () => {
  const citation = {
    available: false,
    chunk_id: "missing",
  };

  assert.equal(isCitationAvailable(citation), false);
  assert.equal(getCitationLabel(citation), "Source unavailable - Chunk missing");
  assert.equal(getCitationSnippet(citation), "Preview unavailable.");
});
