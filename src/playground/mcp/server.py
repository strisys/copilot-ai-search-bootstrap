import sys
from pathlib import Path
from fastmcp import FastMCP

sys.path.append(str(Path(__file__).resolve().parents[1]))
from shared.search import run

mcp = FastMCP("Hoisington")

@mcp.tool()
def analyze(text: str) -> str:
   """Query the Hoisington documents.  Pass the full text specified in the prompt."""
   return run(text)

@mcp.tool()
def documents(text: str) -> str:
   """Query the Hoisington documents for document names only.  Pass the full text specified in the prompt."""
   return run(text, titles_only=True)

if __name__ == "__main__":
   mcp.run(transport="stdio")
