#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

// Create the server (MCP v1.x style)
const server = new McpServer({
  name: "hello-world-mcp",
  version: "0.1.0",
});

// Parameterized tool using zod + registerTool
server.registerTool(
  "hello",
  {
    title: "Hello Tool",
    description: "Say hello with a custom value",
    inputSchema: { value: z.string().describe("Text to include in the greeting") }
  },
  async ({ value }) => ({
    content: [{ type: "text", text: `Hello from MCP server 👋 ${value}` }]
  })
);

// Start (stdio transport)
const transport = new StdioServerTransport();
await server.connect(transport);
