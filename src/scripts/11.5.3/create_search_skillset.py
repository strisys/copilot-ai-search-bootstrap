import sys
from azure.search.documents.indexes.models import SearchIndexerSkillset, SplitSkill, InputFieldMappingEntry, OutputFieldMappingEntry, TextSplitMode
from azure.search.documents.indexes.models import AzureOpenAIEmbeddingSkill  # NEEDED - this is in the JSON
from azure.search.documents.indexes.models import SearchIndexerIndexProjection, SearchIndexerIndexProjectionSelector, SearchIndexerIndexProjectionsParameters, IndexProjectionMode
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
from shared import get_search_indexer_client, set_search_config, print_header, STANDARD_KEYS

keys = STANDARD_KEYS + [
   "SKILLSET_NAME",
   "INDEX_NAME",
   "AZURE_OPENAI_ENDPOINT",
   "AZURE_OPENAI_API_KEY",
   "EMBEDDING_DEPLOYMENT_ID",
   "EMBEDDING_MODEL_NAME"
]   

print_header("Search Skillset")
config = set_search_config(keys)

def create_skillset():
   if config.get('OPERATION', 'create') == 'delete':
      delete_skillset() 
      return

   try:
      result = get_search_indexer_client(config).create_or_update_skillset(create_skillset_definition())
      print(f"SUCCESS: Skillset '{result.name}' created/updated successfully with {len(result.skills)} skills")
   except HttpResponseError as e:
      print(f"ERROR: Failed to create/update skillset: {e.message}")

      if e.error:
         print(f"Error details: {e.error}")

      sys.exit(1)  
   except Exception as e:
      print(f"ERROR: {str(e)}")
      sys.exit(1)  
    
def create_skillset_definition() -> SearchIndexerSkillset:   
   def create_split_skill() -> SplitSkill:
      return SplitSkill(
         name="#1",  
         description="Split skill to chunk documents",
         context="/document",
         default_language_code="en",
         text_split_mode=TextSplitMode.PAGES,  
         maximum_page_length=2000,
         page_overlap_length=500,
         maximum_pages_to_take=0,
         inputs=[
            InputFieldMappingEntry(name="text", source="/document/content"),
         ],
         outputs=[
            OutputFieldMappingEntry(name="textItems", target_name="pages"),
         ]
      ) 

   def create_embedding_skill() -> AzureOpenAIEmbeddingSkill:  
      endpoint = config.get("AZURE_OPENAI_ENDPOINT", "").rstrip('/')
      
      skill = AzureOpenAIEmbeddingSkill(
         name="#2",  
         description="",  
         context="/document/pages/*",
         inputs=[InputFieldMappingEntry(name="text", source="/document/pages/*")],
         outputs=[OutputFieldMappingEntry(name="embedding", target_name="text_vector")],  
         resource_url=endpoint,  
         deployment_name=config.get("EMBEDDING_DEPLOYMENT_ID"),  
         model_name=config.get("EMBEDDING_MODEL_NAME"),
         dimensions=1536
      )
      
      return skill

   def create_search_indexer_index_projection():
      return SearchIndexerIndexProjection(
         selectors=[
            SearchIndexerIndexProjectionSelector(
               target_index_name=config.get('INDEX_NAME', ''),
               parent_key_field_name="parent_id",
               source_context="/document/pages/*",
               mappings=[
                  InputFieldMappingEntry(name="text_vector", source="/document/pages/*/text_vector"),  # Matches JSON exactly
                  InputFieldMappingEntry(name="chunk", source="/document/pages/*"),
                  InputFieldMappingEntry(name="title", source="/document/title")
               ]
            )
         ],
         parameters=SearchIndexerIndexProjectionsParameters(
            projection_mode=IndexProjectionMode.SKIP_INDEXING_PARENT_DOCUMENTS
         )
      )

   skillset_name = config.get("SKILLSET_NAME", "")
    
   return SearchIndexerSkillset(
      name=skillset_name,
      description="Skillset to chunk documents and generate embeddings",  
      skills=[create_split_skill(), create_embedding_skill()],  
      index_projection=create_search_indexer_index_projection()
   )

def delete_skillset():
    try:       
        skillset_name = config.get("SKILLSET_NAME", "")
        indexer_client = get_search_indexer_client(config)
        
        try:
            indexer_client.delete_skillset(skillset_name)
            print(f"SUCCESS: Skillset '{skillset_name}' deleted successfully")
        except ResourceNotFoundError:
            print(f"INFO: Skillset '{skillset_name}' was already deleted or didn't exist")
        except HttpResponseError as e:
            print(f"WARNING: Failed to delete skillset: {e.message}")
            
    except Exception as e:
        print(f"WARNING: Error deleting skillset: {str(e)}")

def list_skillsets():
    try:        
        skillsets = get_search_indexer_client(config).get_skillsets()
        print("Existing skillsets:")

        for skillset in skillsets:
            print(f"  - {skillset.name} with {len(skillset.skills)} skills")
            
    except Exception as e:
        print(f"Error listing skillsets: {str(e)}")

if __name__ == "__main__":
    create_skillset()
    list_skillsets()