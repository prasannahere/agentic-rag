import yaml
from textwrap import dedent
from openai import AzureOpenAI  # make sure AzureOpenAI is imported correctly
from config import PathConfig

class LanguageModel:
    """
    A wrapper for Azure OpenAI to be used in a RAG pipeline.
    Accepts context and query to generate answers.
    """
    def __init__(self, config_path: str = None):
        # Use llm_config.yaml by default
        if config_path is None:
            config_path = PathConfig.LLM_CONFIG
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        self.config = config_data.get('generator', {})
        self.client = self._init_client()
        self.model_name = self.config.get('model')

    def _init_client(self):
        """Initialize Azure OpenAI client"""

        return AzureOpenAI(
            azure_endpoint=self.config.get('endpoint'),
            api_version=self.config.get('version'),
            api_key=self.config.get('api_key'),
        )
    

    def generate_answer(self, query: str, context: str) -> str:
        """
        Generate an answer strictly based on the provided context.
        If the context lacks sufficient info, respond accordingly.
        """

        messages = [
            {"role": "system", "content": dedent(
            """
                You are a precise and factual assistant.
                Follow these rules strictly:
                1. Use ONLY the information provided in the context.
                2. Keep answers concise, clear, and factual.
                3. If the context does not have enough information, say exactly:
                   "I don't know based on the provided context."
                4. When possible, quote or refer to the relevant part of the context.
            """
            )}
            ,
            {"role": "assistant", "content": f"Context:\n{context}"},
            {"role": "user", "content": query}        
            ]

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.config.get('temperature', 0.2),
            max_tokens=self.config.get('max_tokens', 512),
        )

        return response.choices[0].message.content.strip()
    