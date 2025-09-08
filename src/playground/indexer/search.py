import json, hashlib, uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Iterable, List, Any

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex

from reader import read, is_supported
from splitter import split
from vectorizer import vectorize_in_batch
from config_loader import load_config

config = load_config()

SEARCH_ENDPOINT, SEARCH_INDEX, SEARCH_API_KEY = config['AZURE_SEARCH_ENDPOINT'], config['AZURE_SEARCH_INDEX'], config['AZURE_SEARCH_API_KEY']

credential = AzureKeyCredential(SEARCH_API_KEY)
search_client = SearchClient(SEARCH_ENDPOINT, SEARCH_INDEX, credential)
index_client = SearchIndexClient(SEARCH_ENDPOINT, credential)

def ensure_index_has_metadata_field():
   try:
      idx: SearchIndex = index_client.get_index(SEARCH_INDEX)
   except Exception as e:
      raise RuntimeError(f"Index '{SEARCH_INDEX}' not found. Create it first. ({e})")
   
   field_names = {f.name for f in idx.fields}
   required = {"chunk_id", "parent_id", "chunk", "title", "text_vector"}
   missing = [f for f in required if f not in field_names]

   if missing:
      raise RuntimeError(f"Index '{SEARCH_INDEX}' is missing fields: {missing}")
   
   if "meta_data" not in field_names:
      raise RuntimeError("Index is missing 'meta_data' field. Add an Edm.String field named 'metadata' " "(searchable=false, retrievable=true, stored=true) and re-create the index." )
   
def file_parent_id(path: Path) -> str:
   stat = path.stat()
   h = hashlib.sha256()
   h.update(str(path.resolve()).encode("utf-8"))
   h.update(str(stat.st_size).encode("utf-8"))
   h.update(str(int(stat.st_mtime)).encode("utf-8"))
   return h.hexdigest()[:32]

def build_metadata(path: Path, extra: Optional[Dict] = None) -> str:
   data = {
      "path": str(path.resolve()),
      "name": path.name,
      "suffix": path.suffix.lower(),
      "size": path.stat().st_size,
      "modified_utc": datetime.utcfromtimestamp(path.stat().st_mtime).isoformat() + "Z",
   }

   if extra:
      data.update(extra)

   return json.dumps(data, ensure_ascii=False)


def yield_document(path: Path, max_chars: int = 1200, overlap: int = 200) -> Iterable[Dict[str, Any]]:
   text = read(path)

   if not text:
      yield from ()
      return

   chunks = split(text, max_chars, overlap)

   for idx, chunk in enumerate(chunks):
      yield {
         "chunk_id": str(uuid.uuid4()),
         "parent_id": file_parent_id(path),
         "title": path.name,
         "chunk": chunk,
         # 'text_vector' populated later
         "meta_data": build_metadata(path, {"chunk_index": idx, "total_chunks": len(chunks)}),
      }

def delete_docs_by_title(title: str, batch_size = 1000) -> int:
   """
   Finds all documents with an exact matching `title` and deletes them by `chunk_id`.
   Returns the number of deleted documents.

   Notes:
   - `title` is not filterable in your index, so we use a phrase full-text search on `title`
      and then exact-match the title client-side.
   - `chunk_id` is the key field and is required for deletion.
   """

   if (not title):
      return 0
   
   print(f"removing docs with title ({title}) ...")

   # Phrase-search the title field, then exact-match in Python
   # Using quotes forces a phrase query; we still verify equality client-side.
   query = f"\"{title}\""
   
   results = search_client.search(
      search_text=query,
      search_fields=["title"],
      select=["chunk_id", "title"],
      query_type="simple",
      top=batch_size
   )

   ids_to_delete: List[str] = []

   for r in results:
      doc: Dict = dict(r)  
      
      if doc.get("title") == title and "chunk_id" in doc:
         ids_to_delete.append(doc["chunk_id"])

   if not ids_to_delete:
      return 0

   total_deleted = 0

   for i in range(0, len(ids_to_delete), batch_size):
      batch_ids = ids_to_delete[i:i + batch_size]
      batch = [{"chunk_id": cid} for cid in batch_ids]
      result = search_client.delete_documents(documents=batch)
      total_deleted += sum(1 for r in result if r.succeeded)

   print(f"removed {total_deleted} docs with title ({title})!")
   return total_deleted

def batch(iterable: List[Dict], n: int) -> Iterable[List[Dict]]:
   for i in range(0, len(iterable), n):
      yield iterable[i:i+n]

def upload_docs(docs: List[Dict[str, Any]], upload_batch = 10):
   ensure_index_has_metadata_field()

   total = 0

   for title in set([doc.get("title", '') for doc in docs]):
      delete_docs_by_title(title)

   for docs_batch in batch(docs, upload_batch):
      result = search_client.upload_documents(docs_batch)
      failures = [r for r in result if not r.succeeded]

      if failures:
         print(f"[ERROR] {len(failures)} items failed in this batch:")

         for f in failures[:5]:
            print(f"   key={f.key} error={getattr(f, 'error_message', 'unknown')}")

      total += len(docs_batch)
      print(f"Uploaded {total}/{len(docs)} ...")

def collect_docs(root_dir) -> List[Path]:
   print(f'collecting files in root directory {root_dir} ...')
   paths = [path for path in list(Path(root_dir).rglob("*")) if (is_supported(path))]
   print(f'files ({len(paths)}) found to process in root directory {root_dir}!')

   return paths

def upload_directory(root_dir: str, max_chars: int = 1200, overlap: int = 200, upload_batch: int = 1000):
   paths = collect_docs(root_dir=root_dir)

   if (not paths):
      print("No documents to index!")
      return  
   
   docs: List[Dict[str, Any]] = []
   
   for path in paths:
      for doc in yield_document(path, max_chars, overlap):
         docs.append(doc)

   chunks = [d["chunk"] for d in docs]
   vectors = vectorize_in_batch(chunks)

   if len(vectors) != len(docs):
      raise RuntimeError("Embedding count mismatch")

   for d, v in zip(docs, vectors):
      d["text_vector"] = v

   upload_docs(docs, upload_batch=upload_batch)