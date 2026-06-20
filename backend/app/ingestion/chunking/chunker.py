from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings


class TextChunker:
    def __init__(
        self, parent_chunk_size: int = 2000, child_chunk_size: int = 400, overlap: int = 50
    ):
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=parent_chunk_size, chunk_overlap=overlap * 2
        )
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=child_chunk_size, chunk_overlap=overlap
        )

    def chunk_document(self, pages: list) -> list:
        chunks = []
        idx = 0
        for p in pages:
            # 1. Split into large parent chunks
            parent_texts = self.parent_splitter.split_text(p["text"])
            
            # 2. Split each parent into smaller child chunks
            for parent_text in parent_texts:
                child_texts = self.child_splitter.split_text(parent_text)
                for child_text in child_texts:
                    chunks.append({
                        "text": child_text, 
                        "parent_text": parent_text,
                        "page_number": p["page"], 
                        "chunk_index": idx
                    })
                    idx += 1
        return chunks
