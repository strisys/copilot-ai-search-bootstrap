import sys
from azure.search.documents.indexes.models import SearchIndexer, IndexingParameters, FieldMapping, IndexingParametersConfiguration
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
from shared import get_search_indexer_client, set_search_config, print_header, STANDARD_KEYS

keys = STANDARD_KEYS + [
   "DATASOURCE_NAME",
   "INDEXER_NAME",
   "SKILLSET_NAME",
   "INDEX_NAME"
]

print_header("Search Indexer") 
config = set_search_config(keys)

def create_indexer():
   try:     
      if config.get('OPERATION', 'create') == 'delete':
         delete_indexer()
         return
    
      try:
         result = get_search_indexer_client(config).create_or_update_indexer(create_indexer_definition())
         print(f"SUCCESS: Indexer '{result.target_index_name}' created/updated successfully")
         print(f"Indexer details: {result.name} -> DataSource: {result.data_source_name}, Index: {result.target_index_name}")
         
      except HttpResponseError as e:
         print(f"ERROR: Failed to create/update indexer: {e.message}")
         print(f"Error details: {e.error}")
         sys.exit(1)
         
   except Exception as e:
      print(f"ERROR: {str(e)}")
      sys.exit(1)  

def create_indexer_definition():
   indexer_name = config.get('INDEXER_NAME', '')
   datasource_name = config.get('DATASOURCE_NAME', '')
   skillset_name = config.get('SKILLSET_NAME', '')
   index_name = config.get('INDEX_NAME', '')

   configuration = IndexingParametersConfiguration(
      data_to_extract="contentAndMetadata",  
      parsing_mode="default", 
      query_timeout=None,
      disabled=None
   )

   parameters = IndexingParameters(
      batch_size=None,
      max_failed_items=None,
      max_failed_items_per_batch=None,
      configuration=configuration
   )

   field_mappings = [
      FieldMapping(
         source_field_name="metadata_storage_name",
         target_field_name="title",
         mapping_function=None
      )
   ]

   return SearchIndexer(
      name=indexer_name,
      data_source_name=datasource_name,
      target_index_name=index_name,
      skillset_name=skillset_name,
      parameters=parameters,
      field_mappings=field_mappings,
      output_field_mappings=[], 
      schedule=None,  
      description=None,
      encryption_key=None,
      cache=None
   )
   
def delete_indexer():
   try:        
      try:
         indexer_name = config.get('INDEXER_NAME', '')
         get_search_indexer_client(config).delete_indexer(indexer_name)
         print(f"SUCCESS: Indexer '{indexer_name}' deleted successfully")
      except ResourceNotFoundError:
         print(f"INFO: Indexer '{indexer_name}' was already deleted or didn't exist")
      except HttpResponseError as e:
         print(f"WARNING: Failed to delete indexer: {e.message}")
         
   except Exception as e:
      print(f"WARNING: Error deleting indexer: {str(e)}")
      raise e

def run_indexer():
   try:        
      try:
         indexer_name = config.get('INDEXER_NAME', '')
         get_search_indexer_client(config).run_indexer(indexer_name)
         print(f"SUCCESS: Indexer '{indexer_name}' started successfully")
      except HttpResponseError as e:
         print(f"WARNING: Failed to run indexer: {e.message}")
         
   except Exception as e:
      print(f"WARNING: Error running indexer: {str(e)}")

def get_indexer_status():
   try:
      indexer_name = config.get('INDEXER_NAME', '')
      status = get_search_indexer_client(config).get_indexer_status(indexer_name)
      print(f"Indexer '{indexer_name}' status: {status.status}")

      if status.last_result:
         print(f"  Last run: {status.last_result.start_time}")
         print(f"  Status: {status.last_result.status}")
         print(f"  Items processed: {status.last_result.item_count}")
         
         if status.last_result.error_message:
            print(f"  Error: {status.last_result.error_message}")
   except Exception as e:
      print(f"Error getting indexer status: {str(e)}")

def list_indexers():
   try:        
      indexers = get_search_indexer_client(config).get_indexers()
      print("Existing indexers:")

      for indexer in indexers:
         print(f"  - {indexer.name}: {indexer.data_source_name} -> {indexer.target_index_name}")
   except Exception as e:
      print(f"Error listing indexers: {str(e)}")


if __name__ == "__main__":
    create_indexer()
    list_indexers()