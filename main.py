import asyncio
from mcp_server.client import agent_instance

if __name__ == "__main__":
    user_prompt = input("Enter your research question: ")
    asyncio.run(agent_instance(user_prompt, model="gpt-4o", temperature=0, timeout=60))
