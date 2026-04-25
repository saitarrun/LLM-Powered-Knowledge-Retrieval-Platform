export function isCitationAvailable(citation) {
  return Boolean(citation?.available && citation?.document_id && citation?.chunk_id);
}

export function getCitationLabel(citation, index = 0) {
  const documentName = citation?.document_name || "Source unavailable";
  const chunkId = citation?.chunk_id || citation?.id || index + 1;
  return `${documentName} - Chunk ${chunkId}`;
}

export function getCitationSnippet(citation, maxLength = 180) {
  const sourceText = citation?.snippet || citation?.chunk_text || "";
  if (!sourceText) return "Preview unavailable.";
  if (sourceText.length <= maxLength) return sourceText;
  return `${sourceText.slice(0, maxLength - 3).trimEnd()}...`;
}
