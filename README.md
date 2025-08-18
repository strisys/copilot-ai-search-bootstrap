# Document Chat with Copilot Studio backed by Azure AI Search
### Background

While Copilot Studio can use a OneDrive folder as a knowledge source, the timing of data refreshes is unpredictable. This project replicates — and improves on — the Azure resources that Copilot Studio likely uses behind the scenes in that scenario.  The goal is to give you full control over both **when** indexing happens (chunking and vectorization) and **how well** it’s performed.

**Approach**

The project uses VS Code Dev Containers to provide a ready-to-use environment where Terraform provisions:

- **Azure AI Search** resources with indexes and indexers to chunk and vectorize files
- A **storage account** for document storage
- **Azure OpenAI** is used for embeddings.

Unlike the default OneDrive setup, the mentioned indexers can be triggered on demand whenever files change, ensuring timely and consistent updates to your search index.

### Part 1 - Azure Setup 

1. **Configure Variables**

   - In the src directory, copy the terraform.tfvars.sample and rename the copy to **terraform.tfvars**.
   - Open **terraform.tfvars** and update the input variables as needed (organization, project, subscription, tenant).

2. **Run Terraform Commands**

   ```bash
   terraform init 
   terraform plan -out="ai.tfplan"
   terraform apply "ai.tfplan"
   ```

   Take note of the output, which has the Azure CLI command run in Step 4.

   ```bash
   az rest --method post --url https://<service-name>.search.windows.net/indexers/<indexr-name>/run?api-version=2024-07-01 --headers "api-key=<api-key>" --skip-authorization-header --body ""
   ```

3. **Load Sample Data**

   - Sample files are provided in the **artifacts/hoisington** folder.  These contain quarterly economic research data for testing.
   - Upload them to the blob container named “hoisington” in the storage account created by Terraform.  For testing indexing updates, try uploading only part of the sample set at first, then add more later while observing changes in agent responses.  For example, upload only 2024-2025 and then 2022-2023 later.

4. **Run the Indexer**

   - After uploading files, manually trigger the Azure AI Search indexer to process the new or changed documents using the REST command from Step 1.  

   - Navigate to the index blade of the search service resource to ensure the indexer ran successfully.

### Part II - Copilot Studio

This guide assumes you’re already familiar with the basics of creating an agent in [Copilot Studio](https://copilotstudio.microsoft.com/). Most agent settings are straightforward — here’s what we’re using for this project:

| Setting                      | Value                                                        |
| ---------------------------- | ------------------------------------------------------------ |
| Name                         | Hoisington Agent                                             |
| Description                  | Use this agent to answer questions about Hoisington quarterly research |
| Instructions                 | \- You are a helpful agent who answers questions about Hoisington's quarterly research.  <br />- Use the header for page 1 to determine the year and quarter for the research.  <br />- Do must NOT present data for a year and quarter in question unless it's explicitly from the file that has that data.  For example, if the prompt is for Q1 2024 do not use any data from documents other than Q1 2024. |
| Use general knowledge        | No                                                           |
| Use information from the Web | No                                                           |

**Connecting Knowledge to Azure AI Search**

1. After the agent is created, in the **Knowledge** tab of your agent, click **Add knowledge** and select **Azure AI Search** ([image](./docs/copilot-studio-knowledge-setting-1.png))
2. In the following dialog, select Create new connection under Your Connections ([image](./docs/copilot-studio-knowledge-setting-3.png))
3. St up a connection to the Azure AI Search resource created in **Part 1**. ([image](./docs/copilot-studio-knowledge-setting-2.png)).  The URL and API admin key required in this dialog were output in Step 1 of the last section.  
4. Choose the hoisington-index ([image](./docs/copilot-studio-knowledge-setting-4.png)).

Copilot Studio will use this connection to query the indexes you’ve built in Azure AI Search.

### Part III - Test

Once the agent is created, you can prompt it with requests such as the following.   

- Summarize Hoisington's quarterly research for Q1 2025
- Summarize Hoisington's quarterly research for Q2 2022
- Compare and contrast Q1 2025 with Q2 2025.  What changed?

If only a subset of the data was uploaded, expect a reply like the following if there is no data for the year and quarter in question.

> The summary for Hoisington's quarterly research for Q1 2025 is not available. The search result provided an overview for Q1 2023 instead.  Would you like me to search for any other specific information or assist you with something else?

To remedy this, upload the remaining data and rerun in the indexer.
