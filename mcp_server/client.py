import os
import traceback
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from models.llm_openai import llm_instance
from prompts.prompt import task_prompt, security_prompt

# Load environment variables
load_dotenv()


async def agent_instance(
    user_prompt: str, model: str, temperature: float, timeout: int
):
    """
    Creates and runs an agent instance with MCP tools.

    Args:
        user_prompt (str): The user's research query
        model (str): The LLM model to use (e.g., 'gpt-4', 'gpt-3.5-turbo')
        temperature (float): Temperature for response generation (0.0 - 1.0)
        timeout (int): Timeout for API calls in seconds

    Returns:
        str: The agent's response
    """
    # Input validation
    try:
        if not user_prompt or not isinstance(user_prompt, str):
            raise ValueError("user_prompt must be a non-empty string")

        if not model or not isinstance(model, str):
            raise ValueError("model must be a non-empty string")

        if not isinstance(temperature, (int, float)) or not (0.0 <= temperature <= 1.0):
            raise ValueError("temperature must be a number between 0.0 and 1.0")

        if not isinstance(timeout, int) or timeout <= 0:
            raise ValueError("timeout must be a positive integer")

    except Exception as e:
        print(f"Input validation error: {e}")
        raise

    # Define all tools in one MultiServerMCPClient config
    mcp_tools = MultiServerMCPClient(
        {
            "serper": {"url": "http://localhost:8001/sse", "transport": "sse"},
        }
    )
    print("Connecting to MCP tools and agents")  # Initialize the MCP client

    # await is a part of async function to wait for the MCP client to be ready
    try:
        tools = await mcp_tools.get_tools()
    except Exception as e:
        print(f"Error getting tools from MCP client: {e}")
        traceback.print_exception(e)
        raise RuntimeError("Failed to get tools from MCP client.")

    print(f"Loaded Tools: {[tool.name for tool in tools]}")
    agent = create_react_agent(
        model=llm_instance(model=model, temperature=temperature, timeout=timeout),
        tools=tools,
    )  # Create the agent with the LLM and tools

    # Combine task and security prompts to ensure credential protection
    system_prompt = task_prompt() + "\n\n" + security_prompt()

    resposne = await agent.ainvoke(
        {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        }
    )

    print("Agent response received")
    print(f"Agent Response: {resposne['messages'][-1].content}")
    return resposne["messages"][-1].content
