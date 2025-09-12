import { AzureKeyCredential } from "@azure/core-auth";
import { DefaultAzureCredential } from "@azure/identity";
import { SearchClient } from "@azure/search-documents";
import OpenAI from "openai";
import { config, Config } from "./config.js";
import { SecretStoreFactory } from "./secret-store.js";

const AZURE_KEY_VAULT_NAME = 'kv-hoisington-docchat';

// const credential = new DefaultAzureCredential();
// const credential = new AzureKeyCredential(config.AZURE_OPENAI_API_KEY)

let searchClient: any;
let openaiClient: any;
let storeClient: any;

const getConfig = async (): Promise<Config> => {
  if (storeClient) {
    return config;
  }

  storeClient = SecretStoreFactory.get("azure-key-vault", AZURE_KEY_VAULT_NAME);

  // Map: "DB_HOST" -> "DB-HOST"
  const keyPairs: Record<string, string> = Object.fromEntries(
    Object.keys(config).map((k) => [k, k.toUpperCase().replace(/_/g, "-")])
  );

  const values: Record<string, string | undefined> = (await storeClient.getMany(Object.values(keyPairs)));

  for (const [cfgKey, secretKey] of Object.entries(keyPairs)) {
    const val = values[secretKey];

    if (val !== undefined) {
      (config as any)[cfgKey] = val;
    }
  }

  return config;
};


const getSearchClient = async (): Promise<any> => {
   if (searchClient) {
      return searchClient
   }

   const cfg = (await getConfig());

   return (searchClient = new SearchClient(
      cfg.AZURE_SEARCH_ENDPOINT,
      cfg.AZURE_SEARCH_INDEX,
      new AzureKeyCredential(cfg.AZURE_SEARCH_API_KEY)
   ));
};

const getOpenAIClient = async (): Promise<any> => {
   if (openaiClient) {
      return openaiClient
   }

   const cfg = (await getConfig());
   const endpoint = cfg.AZURE_OPENAI_ENDPOINT;
   
   const baseURL = endpoint.endsWith('/') 
      ? `${endpoint}openai/v1/`
      : `${endpoint}/openai/v1/`;

   return (openaiClient = new OpenAI({
      apiKey: cfg.AZURE_OPENAI_API_KEY,
      baseURL: baseURL,
   }));
};

type SearchDoc = {
   rerankerScore: number
   title: string;
   chunk: string;
   meta_data: string;
};

async function getEmbedding(text: string): Promise<number[]> {
   const client = (await getOpenAIClient());
   const cfg = (await getConfig());

   const resp = (await client.embeddings.create({
      input: text,
      model: cfg.AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT,
   }));

   return resp.data[0].embedding;
}

export async function run(searchQuery: string, titlesOnly = false, topN = 100): Promise<string> {
   const embeddingVector = (await getEmbedding(searchQuery));
   const cfg = (await getConfig());

   const searchOptions: any = {
      searchText: searchQuery,
      queryType: "semantic",
      semanticSearchOptions: {
         configurationName: cfg.AZURE_SEARCH_SEMANTIC_SEARCH_CONFIGURATION,
         queryLanguage: "en-us"
      },
      scoringStatistics: "global",
      top: Math.min(topN, 100),
      queries: [{
         kind: "vector" as const,
         vector: embeddingVector,
         // kNearestNeighborsCount: 10,
         fields: "text_vector",
         exhaustive: true
      }]
   };

   const resultsIter = (await (await getSearchClient()).search(searchQuery, searchOptions));
   const filtered: SearchDoc[] = [];

   for await (const doc of resultsIter.results) {
      const document = doc.document as any;
      const rerank = doc["rerankerScore"];

      if (typeof rerank !== "number" || rerank < 1) {
         continue
      }

      filtered.push({
         rerankerScore: rerank,
         title: document.title,
         chunk: document.chunk,
         meta_data: document.meta_data
      } as SearchDoc);
   }

   const results = filtered.map((doc) => {
      const title = (doc.title || "").replace(/\n/g, " ");

      if (titlesOnly) {
         return { title };
      }

      return {
         title,
         rerankerScore: doc.rerankerScore,
         content: (doc.chunk || "").replace(/\n/g, " "),
         metadata: (doc.meta_data || "").replace(/\n/g, " "),
      };
   });

   return JSON.stringify(results, null, 2);
}
