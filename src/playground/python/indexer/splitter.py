from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import Iterable, List, Dict, Optional, Any

splitters: dict[str, Any] = {}

def get_splitter(max_chars: int = 1200, overlap: int = 200) -> RecursiveCharacterTextSplitter:
   key = f"{max_chars}:{overlap}"

   if (splitters.get(key, None) is None):
      splitters[key] = RecursiveCharacterTextSplitter(chunk_size=max_chars, chunk_overlap=overlap, separators=["\n\n", "\n", ". ", "? ", "! ", "; ", ": ", ", ", " ", ""])

   return splitters[key]


def split(text: str, max_chars: int = 1200, overlap: int = 200) -> list[str]:
   return get_splitter(max_chars, overlap).split_text(text)