# Tech Stack & Architecture: NLP-to-SQL Framework

## 1. The Approach
We implemented an **Agentic Tool-Calling** approach rather than zero-shot generation. 
When asked a question, the AI enters a "ReAct" (Reasoning and Acting) loop. It writes a SQL query, executes it against the live SQLite database using a tool, analyzes the results, and fixes its own query if it fails or if the data isn't correct. Once satisfied, it returns the final SQL and data.

## 2. Tooling
We provided the agent with a single, powerful tool: `execute_sql()`. 
The agent uses this tool iteratively:
1. Exploring the schema (e.g., `SELECT name FROM sqlite_master`)
2. Checking available columns in specific tables
3. Running the final data retrieval query

## 3. Data Retrieval (No RAG)
We **did not use standard RAG (Retrieval-Augmented Generation)** or vector databases. 
Instead of retrieving relevant text chunks from a vector store, our agent retrieves its context *dynamically* by directly querying the live database's schema metadata at runtime.

## 4. Core Integration (No MCP)
We **did not use the Model Context Protocol (MCP)**. The tools and database connections are wired directly into the application layer using standard Python functions and LangChain/LangGraph abstractions.

## 5. Agent Orchestration
We implemented a dual-agent architecture to handle different model tiers flexibly:
*   **LangGraph ReAct Agent (Local):** We built a custom `OllamaReActAgent` using LangGraph (`create_react_agent`) specifically tailored for local Ollama models. Smaller local models sometimes struggle with complex multi-step proprietary abstractions, so LangGraph provides a highly robust, strict tool-calling loop that maintains focus.
*   **Deep Agents SDK (Cloud):** The framework retains the original `deepagents` SDK setup via `DeepAgentRunner` designed for high-end cloud models (like OpenAI or Anthropic).

## 6. LLM Configuration
*   **Local Execution (Ollama):** The active pipeline runs locally on **`qwen3.5:4b`** via an Ollama instance. This allows the system to process sensitive data completely offline with zero API costs.
*   *Note: The frontend UI originally referenced `qwen3.5:35b`, however the backend actually executed the lighter `4b` model to ensure reasonable inference times on local hardware. The UI has now been updated to reflect the active `4b` model.*
