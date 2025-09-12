import { AzureKeyCredential } from "@azure/core-auth";
import { SearchClient } from "@azure/search-documents";
import OpenAI from "openai";
import { config } from "./config.js";
import { SecretStoreFactory } from "./secret-store.js";
const AZURE_KEY_VAULT_NAME = 'kv-hoisington-docchat';
// const credential = new DefaultAzureCredential();
// const credential = new AzureKeyCredential(config.AZURE_OPENAI_API_KEY)
let searchClient;
let openaiClient;
let storeClient;
const getConfig = async () => {
    if (storeClient) {
        return config;
    }
    storeClient = SecretStoreFactory.get("azure-key-vault", AZURE_KEY_VAULT_NAME);
    // Map: "DB_HOST" -> "DB-HOST"
    const keyPairs = Object.fromEntries(Object.keys(config).map((k) => [k, k.toUpperCase().replace(/_/g, "-")]));
    const values = (await storeClient.getMany(Object.values(keyPairs)));
    for (const [cfgKey, secretKey] of Object.entries(keyPairs)) {
        const val = values[secretKey];
        if (val !== undefined) {
            config[cfgKey] = val;
        }
    }
    return config;
};
const getSearchClient = async () => {
    if (searchClient) {
        return searchClient;
    }
    const cfg = (await getConfig());
    return (searchClient = new SearchClient(cfg.AZURE_SEARCH_ENDPOINT, cfg.AZURE_SEARCH_INDEX, new AzureKeyCredential(cfg.AZURE_SEARCH_API_KEY)));
};
const getOpenAIClient = async () => {
    if (openaiClient) {
        return openaiClient;
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
async function getEmbedding(text) {
    const client = (await getOpenAIClient());
    const cfg = (await getConfig());
    const resp = (await client.embeddings.create({
        input: text,
        model: cfg.AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT,
    }));
    return resp.data[0].embedding;
}
export async function run(searchQuery, titlesOnly = false, topN = 100) {
    const embeddingVector = (await getEmbedding(searchQuery));
    const cfg = (await getConfig());
    const searchOptions = {
        searchText: searchQuery,
        queryType: "semantic",
        semanticSearchOptions: {
            configurationName: cfg.AZURE_SEARCH_SEMANTIC_SEARCH_CONFIGURATION,
            queryLanguage: "en-us"
        },
        scoringStatistics: "global",
        top: Math.min(topN, 100),
        queries: [{
                kind: "vector",
                vector: embeddingVector,
                // kNearestNeighborsCount: 10,
                fields: "text_vector",
                exhaustive: true
            }]
    };
    const resultsIter = (await (await getSearchClient()).search(searchQuery, searchOptions));
    const filtered = [];
    for await (const doc of resultsIter.results) {
        const document = doc.document;
        const rerank = doc["rerankerScore"];
        if (typeof rerank !== "number" || rerank < 1) {
            continue;
        }
        filtered.push({
            rerankerScore: rerank,
            title: document.title,
            chunk: document.chunk,
            meta_data: document.meta_data
        });
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
//# sourceMappingURL=search.js.map