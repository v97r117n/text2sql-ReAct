"""Agent — wraps LLM + tools into an agentic loop.

For cloud providers (Anthropic, OpenAI), uses Deep Agents for the agentic loop.
For local Ollama models, uses LangGraph's create_react_agent for a simpler
ReAct-style tool-calling loop that works reliably with smaller models.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage


def _get_chat_model(model_str: str):
    """Parse 'provider:model_name' and return a LangChain chat model."""
    if ":" in model_str:
        provider, model_name = model_str.split(":", 1)
    else:
        provider, model_name = "anthropic", model_str

    provider = provider.lower()
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model_name, max_tokens=4096)
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_name)
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=model_name,
            temperature=0,
            num_predict=4096,
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def _is_ollama(model_str: str) -> bool:
    """Check if the model string uses the Ollama provider."""
    return model_str.lower().startswith("ollama:")


class OllamaReActAgent:
    """Simple ReAct agent using LangGraph for local Ollama models.

    This bypasses Deep Agents and uses LangGraph's create_react_agent,
    which works reliably with smaller models that support tool calling.
    """

    def __init__(self, model_str: str, tools: list, system_prompt: str):
        from langgraph.prebuilt import create_react_agent

        self.llm = _get_chat_model(model_str)
        self.system_prompt = system_prompt
        self.tools = tools

        self.agent = create_react_agent(
            model=self.llm,
            tools=tools,
            prompt=system_prompt,
        )

    def invoke(self, input_dict: dict) -> dict:
        """Run the agent."""
        messages = []
        for msg in input_dict.get("messages", []):
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))

        result = self.agent.invoke(
            {"messages": messages},
            config={"recursion_limit": 40},
        )

        return {"messages": result["messages"]}


class DeepAgent:
    """LangChain Deep Agents harness with text2sql tools and system prompt."""

    def __init__(self, model_str: str, tools: list, system_prompt: str):
        from deepagents import create_deep_agent as _deepagents_create

        self.llm = _get_chat_model(model_str)
        self.system_prompt = system_prompt

        self.agent = _deepagents_create(
            model=self.llm,
            tools=tools,
            system_prompt=system_prompt,
            subagents=[],
        )

    def invoke(self, input_dict: dict) -> dict:
        """Run the agent."""
        messages = []
        for msg in input_dict.get("messages", []):
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))

        result = self.agent.invoke(
            {"messages": messages},
            config={"recursion_limit": 50},
        )

        return {"messages": result["messages"]}


def create_deep_agent(
    model: str,
    tools: list,
    system_prompt: str,
    token_limit: int = 75_000,
) -> DeepAgent | OllamaReActAgent:
    """Create an agent with tools and a system prompt.

    Uses OllamaReActAgent for Ollama models (better tool-calling support
    for smaller local models) and DeepAgent for cloud providers.
    """
    if _is_ollama(model):
        return OllamaReActAgent(
            model_str=model,
            tools=tools,
            system_prompt=system_prompt,
        )
    return DeepAgent(
        model_str=model,
        tools=tools,
        system_prompt=system_prompt,
    )
