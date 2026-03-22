import os
import fitz
import docx

class DocumentParser:
    @staticmethod
    def parse(file_path: str, filename: str) -> list:
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            doc = fitz.open(file_path)
            return [{"text": p.get_text(), "page": i+1} for i, p in enumerate(doc)]
        elif ext == ".docx":
            d = docx.Document(file_path)
            return [{"text": "\n".join([p.text for p in d.paragraphs]), "page": 1}]
        return [{"text": open(file_path).read(), "page": 1}]
