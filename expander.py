from crewai import Agent, Task, Crew
from crewai.llm import LLM as BaseLLM
import yaml
import requests
from pydantic import BaseModel, Field
from config import PathConfig

class QueryExpansionOutput(BaseModel):
    """Output schema for query expansion with 3 outputs"""
    
    expanded_query_1: str = Field(..., description="First expanded query variation")
    expanded_query_2: str = Field(..., description="Second expanded query variation")
    expanded_query_3: str = Field(..., description="Third expanded query variation")


class QueryExpansionAgent:
    """
    CrewAI agent that expands and transforms queries for better SOP matching.
    Transforms question-like queries into information-like statements since SOPs
    are written in guideline format, not as questions.
    """
    
    def __init__(self, llm_config_path: str = None):
        """
        Initialize the query expansion agent.
        
        Args:
            llm_config_path: Path to LLM configuration file (defaults to PathConfig)
        """
        print("[INFO] Initializing Query Expansion Agent...")
        llm_config_path = llm_config_path or str(PathConfig.get_llm_config_path())
        self.llm_config = self._load_yaml(llm_config_path)
        self.llm = self._init_llm()
        print("[INFO] Query Expansion Agent ready")
    
    def _load_yaml(self, file_path: str) -> dict:
        """Load YAML configuration file"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    
    def _init_llm(self) -> BaseLLM:
        """Initialize custom LLM from configuration"""
        llm_settings = self.llm_config['llm']
        
        class CustomLLM(BaseLLM):
            def __init__(self, model: str, api_key: str, endpoint: str, temperature: float = 0.7, 
                        context_window: int = 8192, timeout: int = 120):
                super().__init__(model=model, temperature=temperature)
                self.api_key = api_key
                self.endpoint = endpoint
                self.context_window = context_window
                self.timeout = timeout

            def call(self, messages, tools=None, callbacks=None, available_functions=None, **kwargs):
                if isinstance(messages, str):
                    messages = [{"role": "user", "content": messages}]
                payload = {"model": self.model, "messages": messages, "temperature": self.temperature}
                response = requests.post(
                    self.endpoint,
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                response_data = response.json()
                message = response_data["choices"][0]["message"]
                return message.get("content", "")

            def supports_function_calling(self) -> bool:
                return False

            def get_context_window_size(self) -> int:
                return self.context_window

        return CustomLLM(
            model=llm_settings['model'],
            api_key=llm_settings['api_key'],
            endpoint=llm_settings['endpoint'],
            temperature=0.7,  # Higher temperature for diverse query expansions
            context_window=llm_settings['context_window_size'],
            timeout=llm_settings['timeout']
        )
    
    def expand_query(self, original_query: str) -> list:
        """
        Transform a question-like query into an information-like statement.
        
        IMPORTANT: Questions have poor matching with SOPs (Standard Operating Procedures)
        because SOPs are written as guidelines and instructions, not as questions.
        
        This method transforms:
        - "What is the password reset process?" -> "password reset process steps procedure"
        - "How do I request SSL certificate?" -> "SSL certificate request procedure guidelines"
        - "Who handles access requests?" -> "access request handling process responsibility"
        
        Args:
            original_query: The original question
            
        Returns:
            List of 3 transformed queries as information-seeking statements
        """
        agent = Agent(
            role="Query Transformation Specialist",
            goal="Transform question-based queries into information-seeking statements that match SOP document style",
            backstory="""You are an expert at transforming questions into information-seeking statements.
            You understand that Standard Operating Procedures (SOPs) and guidelines are written in an 
            instructional, informative style - NOT as questions. Therefore, to find relevant information 
            in such documents, we must search using statements and keywords rather than questions.
            
            Your expertise lies in:
            1. Converting "What is X?" into "X definition details information"
            2. Converting "How to do Y?" into "Y process procedure steps"
            3. Converting "Who handles Z?" into "Z handling responsibility process"
            4. Extracting key concepts and converting them to search-friendly terms
            5. Removing question words (what, how, who, when, where, why) and rephrasing as statements

            Examples:
            - "I am locked out of my account what can i do, the password says wrong!" -> 
            [
            "Password reset procedure" ,  
            "locked out of account protocol"  ,
            "account access recovery"
            ]
            """,
            verbose=False,
            llm=self.llm,
            allow_delegation=False
        )
        
        task = Task(
            description=f"""
            Transform the following question into an information-seeking statement suitable for searching SOPs and guidelines:

            Original Question: "{original_query}"

            CRITICAL: SOPs are written as instructions and guidelines, NOT as questions!
            Transform this question into a statement that describes the information being sought.

            Strategy:
            1. Removing question words (what, how, who, when, where, why)
            2. Converting to declarative statement form
            3. Keeping key nouns and action verbs
            4. Adding terms like 'process', 'procedure', 'steps', 'guidelines' if applicable

            Rules:
            1. Output ONLY the transformed query - no explanations, no quotes, no preamble
            2. Make it concise to get highest cosine similarity score in vectorDB
            3. Remove all question words and question marks
            4. Use keywords and phrases that would appear in a guideline document
            5. Focus on nouns, verbs, and domain-specific terms/jargons

            Output format: Just the transformed query text""",
            expected_output="3 transformed query statements without explanations or quotes",
            agent=agent,
            output_pydantic=QueryExpansionOutput

        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )
        
        result = crew.kickoff()
        transformed = [original_query,result.pydantic.expanded_query_1, result.pydantic.expanded_query_2, result.pydantic.expanded_query_3]
        
        print(f"[Query Expansion] '{original_query}' -> '{transformed}'")
        return transformed
