
import json, sys
from pathlib import Path
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents.models import VectorizedQuery
from .config_loader import load_config

config = load_config()

SEARCH_ENDPOINT, SEARCH_INDEX, SEARCH_API_KEY = config['AZURE_SEARCH_ENDPOINT'], config['AZURE_SEARCH_INDEX'], config['AZURE_SEARCH_API_KEY']
AOAI_ENDPOINT, AOAI_API_KEY, AOAI_EMBED_DEPLOYMENT, AOAI_API_VERSION = config['AZURE_OPENAI_ENDPOINT'], config['AZURE_OPENAI_API_KEY'], config['AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT'], config['AZURE_OPENAI_API_VERSION']
SEMANTIC_CONFIG = f"{SEARCH_INDEX}-semantic-configuration"

credential = AzureKeyCredential(SEARCH_API_KEY)
search_client = SearchClient(SEARCH_ENDPOINT, SEARCH_INDEX, credential)
index_client = SearchIndexClient(SEARCH_ENDPOINT, credential)

token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
key_credential = AzureKeyCredential(AOAI_API_KEY)

# client = AzureOpenAI(azure_endpoint=AOAI_ENDPOINT, azure_ad_token_provider=token_provider, api_version=AOAI_API_VERSION)
client = AzureOpenAI(azure_endpoint=AOAI_ENDPOINT, api_key=AOAI_API_KEY, api_version=AOAI_API_VERSION)

def get_embedding(text):
    return client.embeddings.create(input=text, model=AOAI_EMBED_DEPLOYMENT).data[0].embedding

def run(search_query: str, titles_only = False) -> str:
   search_vector = get_embedding(search_query)
   v = VectorizedQuery(vector=search_vector, k_nearest_neighbors=50, fields="text_vector")

   r = search_client.search(
      search_query,
      top=50, 
      vector_queries=[v],
      query_type="semantic",
      semantic_configuration_name=SEMANTIC_CONFIG)

   fr = [doc for doc in r if doc['@search.reranker_score'] > 1]

   for doc in fr:
      content = doc["chunk"].replace("\n", " ")
      print(f"score: {doc['@search.score']}, reranker: {doc['@search.reranker_score']}. {content}")

   results = []

   for doc in fr:
      if titles_only:
         results.append({
            "title": doc['title'].replace("\n", " ")
         })

         continue

      results.append({
         "title": doc['title'].replace("\n", " "),
         "reranker_score": doc['@search.reranker_score'],
         "content": doc["chunk"].replace("\n", " "),
         "metadata": doc["meta_data"].replace("\n", " "),
      })

   return json.dumps(results, indent=2)