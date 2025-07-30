from keys import *
from langchain.schema import SystemMessage, HumanMessage
from langchain_together import ChatTogether
from langchain_groq import ChatGroq

# --- LLM Initialization ---
# def initialize_llm():
#     """Initializes and returns the ChatTogether LLM instance."""
#     return ChatTogether(
#         model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
#         temperature=0.85, # Moderate temperature for balanced creativity and factualness
#         together_api_key=TOGETHER_API_KEY,
#         max_tokens=700 # Limit response length to prevent excessive verbosity
#     )


def initialize_llm():
    """Initializes and returns the ChatTogether LLM instance."""
    return ChatGroq(
          model=GROQ_LLAMA_3_8B,
          api_key=GROQ_API_KEY,
          max_tokens=500
    )