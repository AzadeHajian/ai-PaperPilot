import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 
def __check_openai_api_key():
    load_dotenv()
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment variables.")
        return openai_api_key
    except Exception as e:
        raise EnvironmentError("Failed to load OPENAI_API_KEY from environment variables.") from e

#
def llm_instance(model: str , temperature: float , timeout: int) -> ChatOpenAI:
    __check_openai_api_key()
    if __check_openai_api_key() is True:
        print("OpenAI API Key found successfully.")
    return ChatOpenAI(model=model, temperature=temperature, timeout=timeout) 
