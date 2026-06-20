from __future__ import annotations

import os
import unstructured.partition.auto
from app.ingestion.loaders.pii_masker import PIIMasker

class DocumentParser:
    @staticmethod
    def parse(file_path: str, filename: str) -> list:
        elements = unstructured.partition.auto.partition(filename=file_path)
        # Unstructured returns elements which can be text, title, table, etc.
        # We'll join them to form text and mask PII
        
        parsed_data = []
        for element in elements:
            # Mask PII from each element's text
            masked_text = PIIMasker.mask_text(str(element))
            page_num = element.metadata.page_number if hasattr(element, "metadata") and element.metadata and hasattr(element.metadata, "page_number") else 1
            if masked_text.strip():
                parsed_data.append({"text": masked_text, "page": page_num})
        
        # If unstructured fails to extract or it's empty, fallback
        if not parsed_data:
            text = open(file_path, "r", encoding="utf-8", errors="ignore").read()
            masked_text = PIIMasker.mask_text(text)
            return [{"text": masked_text, "page": 1}]
            
        return parsed_data
