#!/usr/bin/env node
import { StdioServerTransport } from "@modelcontextprotocol/sdk/stdio.js";
import { Server } from "@modelcontextprotocol/sdk/server.js";
import { CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";

// Create the server
const server = new Server(
  {
    name: "hello-world-mcp",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Register a simple tool
server.tool("hello", CallToolRequestSchema, async () => {
  return {
    content: [
      {
        type: "text",
        text: "Hello from MCP server 👋",
      },
    ],
  };
});

// Start with stdio transport (what VSCode MCP client expects)
const transport = new StdioServerTransport();
await server.connect(transport);