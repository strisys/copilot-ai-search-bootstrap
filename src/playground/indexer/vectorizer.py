import os, time
from typing import List
from langchain_openai import AzureOpenAIEmbeddings
from openai import RateLimitError
from config_loader import load_config

config = load_config()

AOAI_ENDPOINT, AOAI_API_KEY, AOAI_EMBED_DEPLOYMENT, AOAI_API_VERSION = config['AZURE_OPENAI_ENDPOINT'], config['AZURE_OPENAI_API_KEY'], config['AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT'], config['AZURE_OPENAI_API_VERSION']

def get_embedder() -> AzureOpenAIEmbeddings:
    os.environ.setdefault("AZURE_OPENAI_API_KEY", AOAI_API_KEY)
    os.environ.setdefault("AZURE_OPENAI_ENDPOINT", AOAI_ENDPOINT)
    os.environ.setdefault("AZURE_OPENAI_API_VERSION", AOAI_API_VERSION)
    return AzureOpenAIEmbeddings(model=AOAI_EMBED_DEPLOYMENT)

embedder = get_embedder()
max_retries = 3

def vectorize_in_batch(chunks: List[str], batch_size: int = 30) -> List[List[float]]:
   print(f'creating vectors for chunks {len(chunks)} ...')

   vectors: List[List[float]] = []
   pause, error_pause = 1.0, 0.5

   for i in range(0, len(chunks), batch_size): 
      batch = chunks[i: (i + batch_size)] 
      
      for _ in range(max_retries):
         try:
            print(f'vectorizing batch (#{i}). {len(chunks)} total ...')
            vectors.extend(embedder.embed_documents(batch)) 

            print(f'{len(chunks)} vector arrays created of dimension {len(vectors[-1])})')
            print('pausing ({pause} seconds) to avoid rate limit ...')
            
            time.sleep(pause) 

            break
         except RateLimitError as e:
            print(e)
            time.sleep(error_pause) 
            error_pause += 0.5
            

   print(f'vectors created for chunks ({len(chunks)})!')
   return vectors
