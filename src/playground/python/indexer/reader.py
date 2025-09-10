from pathlib import Path
from pypdf import PdfReader
from docx import Document as DocxDocument
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader, BSHTMLLoader

def loader_for_path(path: Path):
   ext = path.suffix.lower()

   if ext == ".pdf":
      return PyPDFLoader(str(path))
   
   if ext == ".docx":
      return Docx2txtLoader(str(path))
   
   if ext in (".html", ".htm"):
      return BSHTMLLoader(str(path), open_encoding="utf-8", bs_kwargs={"features": "html.parser"})
   
   if ext in (".txt", ".md"):
      return TextLoader(str(path), encoding="utf-8")
   
   return None 

def is_supported(path: Path):
   return ((path is not None) and (path.is_file()) and (loader_for_path(path) is not None))

def read(path: Path) -> str:
   """
   Use LangChain loaders to extract text. Many loaders return per-page/per-section Documents.
   Concatenate their page_content.
   """
   loader = loader_for_path(path)

   if not loader:
      return ""
   
   try:
      docs = loader.load()
   except Exception as e:
      print(f"[WARN] Failed to read {path}: {e}")
      return ""
   
   return "\n".join((d.page_content or "").strip() for d in docs if d.page_content).strip()