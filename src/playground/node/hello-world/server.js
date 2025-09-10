#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

// create the server
const server = new Server(
  { name: "hello-world-mcp", version: "0.1.0" },
  { capabilities: { tools: {} } }
);

// parameterized tool
server.registerTool(
  "hello",
  {
    description: "Say hello with a custom value",
    inputSchema: {
      value: z.string().describe("Text to include in the greeting")
    }
  },
  async ({ value }) => ({
    content: [
      { type: "text", text: `Hello from MCP server 👋 ${value}` }
    ]
  })
);

// start (stdio transport)
const transport = new StdioServerTransport();
await server.connect(transport);
