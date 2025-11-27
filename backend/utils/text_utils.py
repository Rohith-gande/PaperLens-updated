"""Text processing utilities"""
import re
from typing import List


def clean_text(text: str) -> str:
    """Clean text by removing citations and special characters"""
    if not text:
        return ""
    # Remove citations like [1], [2,3], etc.
    text = re.sub(r'\[.*?\]', '', text)
    return text.strip()


def split_text_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks"""
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk.strip())

        start += (chunk_size - overlap)

    return chunks

