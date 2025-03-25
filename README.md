# Nextflow Developer Tools MCP

A Model Context Protocol (MCP) server designed for Nextflow development and testing, built with FastMCP.

> [!WARNING]
> This MCP is designed for developing Nextflow itself, not for writing Nextflow pipelines.

## Overview

This MCP provides a suite of tools for Nextflow development, including:

- Building Nextflow from source
- Running tests (integration tests, specific tests, plugin tests)
- Running the development version of Nextflow
- Managing the Nextflow development directory
- Accessing Nextflow documentation

## Installation

### Prerequisites

- [Claude Desktop App](https://claude.ai/desktop)
- Python 3.8+ with pip
- Git repository of Nextflow (cloned locally)

### Installing with FastMCP to use in Claude Desktop

1. Install the FastMCP CLI tool:

```bash
pip install fastmcp
```

2. Clone this repository:

```bash
git clone https://github.com/yourusername/nextflow-dev-mcp.git
cd nextflow-dev-mcp
```

3. Install the MCP in Claude Desktop:

```bash
fastmcp install mcp-nextflow.py
```

This will make the MCP available in the Claude Desktop app.

### Installing with FastMCP to use in Cursor

1. Fetch the virtual environment path which includes the FastMCP CLI tool. If you are using `uv` this will be in the `.venv` directory.
1. Get the directory of your Nextflow cloned repository.
1. Add the following json to the cursor MCP servers:

```json
{
    "mcpServers": {
        "server-name": {
            "command": "/path/to/your/.venv/bin/python",
            "args": [
                "/path/to/your/mcp-nextflow/mcp-nextflow.py"
            ],
            "env": {
                "NEXTFLOW_DIR": "/path/to/your/nextflow"
            }
        }
    }
}
```

Then, you should be able to use the MCP in Cursor. In Agentic mode, ask the agent to "test the nf-amazon plugin" and it should run `make test module=plugins:nf-amazon`.

### Setting Environment Variables

You can specify the Nextflow directory during installation:

```bash
NEXTFLOW_DIR=/path/to/your/nextflow fastmcp install mcp-nextflow.py
```

## Using with Claude

Once installed, you can access the MCP in the Claude Desktop app:

1. Open Claude Desktop
2. Click on the **Tools** menu button in the Claude interface
3. Select **Nextflow Developer Tools** from the list of installed MCPs

## Using with Cursor

[Cursor](https://cursor.sh/) is an AI-powered code editor that works with Claude. To use the MCP with Cursor:

1. Make sure you've installed the MCP as described above
2. Open your Nextflow project in Cursor
3. In a chat with Claude in Cursor, you can reference the MCP:
   ```
   Using the Nextflow Developer Tools, run the integration tests for the nf-amazon plugin
   ```
