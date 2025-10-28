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
        print(f"[INFO] Initializing Azure OpenAI client with endpoint: {self.config.get('endpoint')}")
        print(f"[INFO] Initializing Azure OpenAI client with version: {self.config.get('version')}")
        print(f"[INFO] Initializing Azure OpenAI client with api_key: {self.config.get('api_key')}")
        return AzureOpenAI(
            azure_endpoint=self.config.get('endpoint'),
            api_version=self.config.get('version'),
            api_key=self.config.get('api_key'),
        )
    
    def generate_answer(self, query: str, context: str) -> str:
        """
        Generate an answer using context + query.
        The assistant should ONLY use the provided context.
        If context is insufficient, it must explicitly say it doesn't know.


        """
        
        prompt = f"""
        You are an precise and factual assistant. Follow these rules strictly:
    
        1. Only use information from the provided context.
        2. Keep answers concise and to the point.
        3. Do not provide additional commentary.
        4. When giving an answer, quote the part of the context you are using (if possible).
        
        Context:
        {context}
    
        Question:
        {query}
    
        """
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "system", "content": dedent(prompt)}],
        )
        return response.choices[0].message.content.strip()
    