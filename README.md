# Document Chat with Copilot Studio backed by Azure AI Search
### Background

While Copilot Studio can use a OneDrive folder as a knowledge source, the timing of data refreshes from that folder is unpredictable. This project replicates — and improves on — the Azure resources that Copilot Studio likely uses behind the scenes in that scenario.

The goal is to give you full control over both **when** indexing happens (chunking and vectorization) and **how well** it’s performed.

**Approach**

The project uses VS Code Dev Containers to provide a ready-to-use environment where Terraform provisions:

- **Azure AI Search** resources
- A **storage account** for document storage
- **Indexers** to chunk and vectorize files

Unlike the default OneDrive setup, these indexers can be triggered on demand whenever files change, ensuring timely and consistent updates to your search index.

### Part 1 - Azure Setup 

1. **Configure Variables**

   - In the src directory, rename terraform.tfvars.sample to terraform.tfvars.
   - Open terraform.tfvars and update the input variables as needed for your environment.

2. **Run Terraform Commands**

   ```bash
   terraform init 
   terraform plan -out="ai.tfplan"
   terraform apply "ai.tfplan"
   ```

3. **Load Sample Data**

   - Sample files are provided in the artfacts/hoisington folder.
   - These contain quarterly economic research data for testing.
   - Upload them to the blob container named hoisington in the storage account created by Terraform.
   - For testing indexing updates, try uploading only part of the sample set at first, then add more later while observing changes in agent responses.

4. **Run the Indexer**

   1. After uploading files, manually trigger the Azure AI Search indexer to process the new or changed documents.

### Part II - Copilot Studio

This guide assumes you’re already familiar with the basics of creating an agent in Copilot Studio. Most agent settings are straightforward — here’s what we’re using for this project:

| Setting                      | Value                                                        |
| ---------------------------- | ------------------------------------------------------------ |
| Name                         | Hoisington Agent                                             |
| Description                  | Use the agent to answer questions about Hoisington quarterly research |
| Instructions                 | You are a helpful agent who answers questions about Hoisington's quarterly research.  Use the header for page 1 to determine the year and quarter for the research |
| Use general knowledge        | No                                                           |
| Use information from the Web | No                                                           |

**Connecting Knowledge to Azure AI Search**

1. In the **Knowledge** tab of your agent, click **Add knowledge** and select **Azure AI Search** ([image](./docs/copilot-studio-knowledge-setting-1.png))
2. When prompted, set up a connection to the Azure AI Search resource created in **Part 1**. ([image](./docs/copilot-studio-knowledge-setting-2.png))
3. Have the following information ready:
   - **URL** of the Azure AI Search service
   - **Administration key** for that service

Copilot Studio will use this connection to query the indexes you’ve built in Azure AI Search.

### Part III - Test

Once the agent is created, you can prompt it with requests such as the following.

- Summarize Hoisington's quarterly research for Q1 2025
- Summarize Hoisington's quarterly research for Q2 2024
- Compare and contrast Q1 2025 with Q2 2025.  What changed?
