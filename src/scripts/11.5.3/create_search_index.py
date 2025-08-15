import sys
from azure.search.documents.indexes.models import SearchIndex, SearchField, SearchFieldDataType, SearchableField, SimpleField, LexicalAnalyzerName
from azure.search.documents.indexes.models import SemanticConfiguration, SemanticPrioritizedFields, SemanticField, SemanticSearch
from azure.search.documents.indexes.models import VectorSearch, HnswAlgorithmConfiguration, HnswParameters, VectorSearchProfile, AzureOpenAIVectorizer, AzureOpenAIVectorizerParameters
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
from shared import get_search_index_client, set_search_config, print_header, STANDARD_KEYS

keys = STANDARD_KEYS + [
   "INDEX_NAME",
   "AZURE_OPENAI_ENDPOINT",
   "EMBEDDING_DEPLOYMENT_ID",
   "EMBEDDING_MODEL_NAME"
]

print_header("Search Index")
config = set_search_config(keys) 

def create_index():
   try:        
      if config.get('OPERATION', 'create') == 'delete':
         delete_index()
         return
            
      result = get_search_index_client(config).create_or_update_index(create_search_index_definition())
      print(f"SUCCESS: Index '{result.name}' created/updated successfully with {len(result.fields)} fields")
         
   except Exception as e:
      print(f"ERROR: {str(e)}")
      sys.exit(1)  

def create_search_index_definition():    
   index_name, azure_openai_endpoint, embedding_deployment_id, embedding_model_name = (
      config.get(k) for k in ['INDEX_NAME', 'AZURE_OPENAI_ENDPOINT', 'EMBEDDING_DEPLOYMENT_ID', 'EMBEDDING_MODEL_NAME']
   )

   azure_openai_endpoint = (azure_openai_endpoint or '').rstrip('/')

   algorithm_name = f"{index_name}-algorithm"
   vectorizer_name = f"{index_name}-azureOpenAi-text-vectorizer"
   profile_name = f"{index_name}-azureOpenAi-text-profile"
   semantic_config_name = f"{index_name}-semantic-configuration"  
     
   def create_fields():
      chunk_id_field = SearchField(
         name="chunk_id",
         type=SearchFieldDataType.String,
         key=True,
         searchable=True,
         filterable=False,
         sortable=True,
         facetable=False,
         analyzer_name=LexicalAnalyzerName.KEYWORD
      )

      parent_id = SearchField(
         name="parent_id",
         type=SearchFieldDataType.String,
         searchable=False,       
         filterable=True,
         sortable=False,
         facetable=False,
         key=False
      )

      chunk = SearchField(
         name="chunk",
         type=SearchFieldDataType.String,
         searchable=True,
         filterable=False,
         sortable=False,
         facetable=False,
         key=False
      )

      title = SearchField(
         name="title",
         type=SearchFieldDataType.String,
         searchable=True,
         filterable=False,
         sortable=False,
         facetable=False,
         key=False
      )

      text_vector = SearchField(
         name="text_vector",
         type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
         searchable=True,
         retrievable=True,
         filterable=False,
         sortable=False, 
         facetable=False,
         key=False,
         vector_search_dimensions=1536,
         vector_search_profile_name=profile_name
      )

      return [chunk_id_field, parent_id, chunk, title, text_vector]
     
   try:
      algorithm_config = HnswAlgorithmConfiguration(
         name=algorithm_name,
         parameters=HnswParameters(
               m=4,
               ef_construction=400,
               ef_search=500, 
               metric="cosine"
         )
      )
 
      vectorizer_params = AzureOpenAIVectorizerParameters(
         resource_url=azure_openai_endpoint,  
         deployment_name=embedding_deployment_id,  
         model_name=embedding_model_name 
      )
      
      vectorizer_config = AzureOpenAIVectorizer(
         vectorizer_name=vectorizer_name, 
         parameters=vectorizer_params
      )
      
      profile_config = VectorSearchProfile(
         name=profile_name, 
         algorithm_configuration_name=algorithm_name,
         vectorizer_name=vectorizer_name
      )
      
      vector_search = VectorSearch(
         algorithms=[algorithm_config], 
         profiles=[profile_config], 
         vectorizers=[vectorizer_config]
      )
        
   except Exception as e:
      raise Exception(f"Vector search configuration failed: {e}")
   
   semantic_search = SemanticSearch(
      default_configuration_name=semantic_config_name,
      configurations=[
            SemanticConfiguration(
               name=semantic_config_name,
               prioritized_fields=SemanticPrioritizedFields(
                  title_field=SemanticField(field_name="title"),
                  content_fields=[
                        SemanticField(field_name="chunk")
                  ]
               )
            )
      ]
   )
         
   return SearchIndex(name=index_name, fields=create_fields(), vector_search=vector_search, semantic_search=semantic_search)

def delete_index():
    index_name = config.get("INDEX_NAME", "")

    try:        
        try:
            get_search_index_client(config).delete_index(index_name)
            print(f"SUCCESS: Index '{index_name}' deleted successfully")
        except ResourceNotFoundError:
            print(f"INFO: Index '{index_name}' was already deleted or didn't exist")
        except HttpResponseError as e:
            print(f"WARNING: Failed to delete index: {e.message}")
            
    except Exception as e:
        print(f"WARNING: Error deleting index: {str(e)}")

def list_indexes():
    try:
        for idx in get_search_index_client(config).list_indexes():
            print(f"  - {idx.name} with {len(idx.fields)} fields")
            
    except Exception as e:
        print(f"Error listing indexes: {str(e)}")

if __name__ == "__main__":
    create_index()
    list_indexes()