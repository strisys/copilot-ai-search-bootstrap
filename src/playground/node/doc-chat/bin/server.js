#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { run } from "./search.js";
// Create the server (MCP v1.x style)
const server = new McpServer({
    name: "hello-world-mcp",
    version: "0.1.0",
});
server.registerTool("analyze", {
    title: "Analysis Tool",
    description: "Take text exactly as given and return a list of related document data",
    inputSchema: {
        text: z.string().describe("Text used to find related data")
    }
}, async ({ text }) => {
    const results = await run(text, true, 100);
    return {
        content: [
            { type: "text", text: results }
        ]
    };
});
server.registerTool("document", {
    title: "Document Tool",
    description: "Take text exactly as given and return a list of related document titles",
    inputSchema: {
        text: z.string().describe("Text used to find related documents")
    }
}, async ({ text }) => {
    const results = (await run(text));
    return {
        content: [
            { type: "text", text: results }
        ]
    };
});
const transport = new StdioServerTransport();
await server.connect(transport);
//# sourceMappingURL=server.js.map