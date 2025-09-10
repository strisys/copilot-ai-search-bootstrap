#!/usr/bin/env node
import { StdioServerTransport } from "@modelcontextprotocol/sdk/stdio.js";
import { Server } from "@modelcontextprotocol/sdk/server.js";
import { CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";

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

server.registerTool(
  "hello",
  {
    description: "Say hello with a custom value",
    inputSchema: {
      value: z.string().describe("Text to include in the greeting")
    }
  },
  async ({ value }) => {
    return {
      content: [
        { type: "text", text: `Hello from MCP server 👋 ${value}` }
      ]
    };
  }
);

// Start with stdio transport (what VSCode MCP client expects)
const transport = new StdioServerTransport();
await server.connect(transport);