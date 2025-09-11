import { AzureKeyCredential } from "@azure/core-auth";
import { SearchClient } from "@azure/search-documents";
import OpenAI from "openai";
import { DefaultAzureCredential } from "@azure/identity";
import { config } from "./config.js";

const SEMANTIC_CONFIG = `${config.AZURE_SEARCH_INDEX}-semantic-configuration`;
// const credential = new DefaultAzureCredential();
const credential = new AzureKeyCredential(config.AZURE_OPENAI_API_KEY)
let searchClient: any;
let openaiClient: any;

const getSearchClient = () => {
   if (searchClient) {
      return searchClient
   }

   return (searchClient = new SearchClient(
      config.AZURE_SEARCH_ENDPOINT,
      config.AZURE_SEARCH_INDEX,
      new AzureKeyCredential(config.AZURE_SEARCH_API_KEY)
   ));
};

const getOpenAIClient = () => {
   if (openaiClient) {
      return openaiClient
   }

   const endpoint = config.AZURE_OPENAI_ENDPOINT;

   const baseURL = endpoint.endsWith('/') 
      ? `${endpoint}openai/v1/`
      : `${endpoint}/openai/v1/`;

   return (openaiClient = new OpenAI({
      apiKey: config.AZURE_OPENAI_API_KEY,
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
   const client = getOpenAIClient();

   const resp = (await client.embeddings.create({
      input: text,
      model: config.AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT,
   }));

   return resp.data[0].embedding;
}

export async function run(searchQuery: string, titlesOnly = false, topN = 100): Promise<string> {
   const embeddingVector = (await getEmbedding(searchQuery));

   const searchOptions: any = {
      searchText: searchQuery,
      queryType: "semantic",
      semanticSearchOptions: {
         configurationName: SEMANTIC_CONFIG,
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

   const resultsIter = (await getSearchClient().search(searchQuery, searchOptions));
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
