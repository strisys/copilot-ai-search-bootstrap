import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

REQUIRED_VARS = [
   "AZURE_SEARCH_ENDPOINT",
   "AZURE_SEARCH_API_KEY",
   "AZURE_OPENAI_ENDPOINT",
   "AZURE_OPENAI_API_KEY",
   "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT",
]

BASE_DIR = Path(__file__).resolve().parent
dotenv_path = BASE_DIR / ".env"

config = {}

def load_config(env_file: str | None = None) -> dict:
   global config

   if (len(config)):
      return config

   if env_file:
      env_path = Path(env_file)

      if not env_path.exists():
         raise FileNotFoundError(f".env file not found at {env_path}")
      
      load_dotenv(dotenv_path=env_path, override=False)
   
   if (not env_file):
      print(f"Loading .env from current working directory {dotenv_path}")
      load_dotenv(dotenv_path, override=False)

   # Validate required variables
   missing = [k for k in REQUIRED_VARS if not os.getenv(k)]

   if missing:
      raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

   config = {
      "AZURE_SEARCH_ENDPOINT": os.getenv("AZURE_SEARCH_ENDPOINT"),
      "AZURE_SEARCH_API_KEY": os.getenv("AZURE_SEARCH_API_KEY"),
      "AZURE_SEARCH_INDEX": os.getenv("AZURE_SEARCH_INDEX", "hoisington-index"),
      "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
      "AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY"),
      "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT": os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT"),
      "AZURE_OPENAI_API_VERSION": os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01"),
      "MAX_CHARS": int(os.getenv("MAX_CHARS", "1200")),
      "OVERLAP": int(os.getenv("OVERLAP", "200"))
   }

   return config
