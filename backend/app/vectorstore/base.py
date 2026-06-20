from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class VectorStore(Protocol):
    """Shared interface for dense and sparse vector stores."""

    def add(
        self,
        texts: list[str],
        ids: list[str],
        embeddings: list[list[float]] | None = None,
        metadatas: list[dict] | None = None,
    ) -> None: ...

    def search(
        self,
        query_text: str = "",
        query_embedding: list[float] | None = None,
        top_k: int = 5,
    ) -> list[dict]: ...

    def remove(self, ids: list[str]) -> None: ...
