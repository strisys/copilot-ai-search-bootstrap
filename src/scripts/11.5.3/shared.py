import os
from tabulate import tabulate
from azure.identity import DefaultAzureCredential
from azure.mgmt.search import SearchManagementClient
from azure.search.documents.indexes import SearchIndexerClient, SearchIndexClient
from azure.core.credentials import AzureKeyCredential

STANDARD_KEYS = [
   "OPERATION",
   "AZURE_SUBSCRIPTION_ID",
   "SEARCH_SERVICE_NAME",
   "RESOURCE_GROUP_NAME"
]

def print_header(title: str):
   print()
   print(50 * "=")
   print(title)
   print(50 * "=")
   print()

def set_search_config(keys: list[str]) -> dict[str, str]:
   def truncate(text, max_len=35):
      if len(text) <= max_len:
         return text
      
      mid = max_len // 2 - 2
      return f"{text[:mid]}...{text[-mid:]}"
   
   config: dict[str, str] = {key: os.getenv(key, "").strip() for key in keys}
   print(tabulate([(k, truncate(v)) for k, v in config.items()], headers=["Variable", "Value"], tablefmt="github"))

   return config

def get_search_endpoint(config: dict[str, str]) -> str:
    return f"https://{config.get('SEARCH_SERVICE_NAME')}.search.windows.net"

def get_search_admin_key(config: dict[str, str]) -> str:
    search_service_name, subscription_id, resource_group_name = (
      config[k] for k in ("SEARCH_SERVICE_NAME", "AZURE_SUBSCRIPTION_ID", "RESOURCE_GROUP_NAME")
   )
        
    try:
        search_mgmt_client = SearchManagementClient(DefaultAzureCredential(), subscription_id)
        admin_keys = search_mgmt_client.admin_keys.get(resource_group_name, search_service_name)

        if not admin_keys or not admin_keys.primary_key:
         raise Exception("Failed to retrieve admin key for search service")
        
        return admin_keys.primary_key
    except Exception as e:
        raise Exception(f"Failed to get search service admin keys: {str(e)}")
    
def get_search_indexer_client(config: dict[str, str]):   
   return SearchIndexerClient(endpoint=get_search_endpoint(config), credential=AzureKeyCredential(get_search_admin_key(config)))

def get_search_index_client(config: dict[str, str]):
   return SearchIndexClient(endpoint=get_search_endpoint(config), credential=AzureKeyCredential(get_search_admin_key(config)))