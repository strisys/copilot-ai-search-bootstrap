#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

// Create the server (MCP v1.x style)
const server = new McpServer({
  name: "hello-world-mcp",
  version: "0.1.0",
});

server.registerTool(
  "echo",
  {
    title: "Echo Tool",
    description: "Echo back the provided text exactly as given. Do not add punctuation, prefixes, or formatting.",
    inputSchema: {
      text: z.string().describe("Verbatim text to echo back")
    }
  },
  async ({ text }) => ({
    content: [
      { type: "text", text: `Hello from MCP server 👋 ${text}` }
    ]
  })
);


// Start (stdio transport)
const transport = new StdioServerTransport();
await server.connect(transport);
