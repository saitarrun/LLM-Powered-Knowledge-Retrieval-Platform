from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings

class TextChunker:
    def __init__(self, chunk_size: int = settings.CHUNK_SIZE, chunk_overlap: int = settings.CHUNK_OVERLAP):
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def chunk_document(self, pages: list) -> list:
        chunks = []
        idx = 0
        for p in pages:
            for t in self.splitter.split_text(p["text"]):
                chunks.append({"text": t, "page_number": p["page"], "chunk_index": idx})
                idx += 1
        return chunks
