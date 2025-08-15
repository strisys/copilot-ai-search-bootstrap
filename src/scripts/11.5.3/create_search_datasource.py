import sys
from azure.search.documents.indexes.models import SearchIndexerDataSourceConnection, SearchIndexerDataContainer, SearchIndexerDataSourceType
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
from shared import get_search_indexer_client, set_search_config, print_header, STANDARD_KEYS

keys = STANDARD_KEYS + [
   "DATASOURCE_NAME",
   "CONTAINER_NAME",
   "STORAGE_ACCOUNT_ID",
]
 
print_header("Datasource")
config = set_search_config(keys)

def create_datasource(): 
   datasource_name, container_name, storage_account_id = (
      config[k] for k in ("DATASOURCE_NAME", "CONTAINER_NAME", "STORAGE_ACCOUNT_ID")
   )

   try:        
      if config.get('OPERATION', 'create') == 'delete':
         delete_datasource(datasource_name)
         return
      
      indexer_client = get_search_indexer_client(config)
      
      datasource = SearchIndexerDataSourceConnection(name=datasource_name,
         type=SearchIndexerDataSourceType.AZURE_BLOB,
         connection_string=f"ResourceId={storage_account_id};",
         container=SearchIndexerDataContainer(name=container_name)
      )
      
      try:
         result = indexer_client.create_or_update_data_source_connection(datasource)
         print(f"SUCCESS: Datasource '{datasource_name}' created/updated successfully")
         print(f"Datasource details: {result.name} -> {result.container.name}")
         
      except HttpResponseError as e:
         print(f"ERROR: Failed to create/update datasource: {e.message}")
         print(f"Error details: {e.error}")
         sys.exit(1)
         
   except Exception as e:
      print(f"ERROR: {str(e)}")
      sys.exit(1)

def delete_datasource(datasource_name):
    try:           
        try:
            get_search_indexer_client(config).delete_data_source_connection(datasource_name)
            print(f"SUCCESS: Datasource '{datasource_name}' deleted successfully")
        except ResourceNotFoundError:
            print(f"INFO: Datasource '{datasource_name}' was already deleted or didn't exist")
        except HttpResponseError as e:
            print(f"WARNING: Failed to delete datasource: {e.message}")
            
    except Exception as e:
        print(f"WARNING: Error deleting datasource: {str(e)}")


if __name__ == "__main__":
   create_datasource()