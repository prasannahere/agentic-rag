from crewai import Agent, Task, Crew
from crewai.llm import LLM as BaseLLM
import yaml
import requests
from pydantic import BaseModel, Field
from config import PathConfig


class VerificationOutput(BaseModel):
    """Output schema for answer verification"""
    
    is_valid: bool = Field(..., description="Whether the answer is valid and legitimate")
    confidence_score: float = Field(..., description="Confidence score from 0.0 to 1.0")
    reasoning: str = Field(..., description="Detailed explanation of the verification decision")
    concerns: str = Field(..., description="Any red flags or issues identified during verification")
    recommendation: str = Field(..., description="Recommendation: 'accept', 'reject', or 'clarify'")

class AnswerVerificationAgent:
    """
    CrewAI agent that critically verifies if an answer legitimately addresses the question.
    Approaches with healthy skepticism while remaining objective and unbiased.
    """
    
    def __init__(self, llm_config_path: str = None):
        """
        Initialize the answer verification agent.
        
        Args:
            llm_config_path: Path to LLM configuration file (defaults to PathConfig)
        """
        print("[INFO] Initializing Answer Verification Agent...")
        llm_config_path = llm_config_path or str(PathConfig.get_llm_config_path())
        self.llm_config = self._load_yaml(llm_config_path)
        self.llm = self._init_llm()
        print("[INFO] Answer Verification Agent ready")
    
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
            temperature=0.3,  # Lower temperature for consistent, objective evaluation
            context_window=llm_settings['context_window_size'],
            timeout=llm_settings['timeout']
        )
    
    def verify_answer(self, question: str, answer: str) -> dict:
        """
        Critically verify if the provided answer legitimately addresses the question.
        
        Approaches with healthy skepticism - assumes the answer might be incorrect,
        incomplete, or irrelevant, but evaluates objectively based on evidence.
        
        Args:
            question: The original question asked
            answer: The answer to be verified
            
        Returns:
            Dictionary containing verification results with the following keys:
            - is_valid: bool indicating if answer is legitimate
            - confidence_score: float from 0.0 to 1.0
            - reasoning: detailed explanation of the verification
            - concerns: any red flags or issues identified
            - recommendation: 'accept', 'reject', or 'clarify'
        """
        agent = Agent(
            role="Critical Answer Verification Specialist",
            goal="Objectively verify if answers legitimately address questions with healthy skepticism",
            backstory="""You are a meticulous answer verification specialist with expertise in 
            critical thinking and objective evaluation. Your primary approach is skeptical - you 
            assume answers might be wrong, incomplete, or irrelevant until proven otherwise.
            
            However, you remain completely objective and unbiased. Your skepticism is methodical,
            not predetermined. You evaluate based on evidence and logic, not prejudice.
            
            Your evaluation framework:
            
            1. RELEVANCE CHECK:
               - Does the answer actually address the question asked?
               - Is it answering a different question?
               - Are there topic mismatches?
            
            2. COMPLETENESS CHECK:
               - Does it provide a complete answer?
               - Are critical details missing?
               - Does it leave important aspects unaddressed?
            
            3. ACCURACY CHECK:
               - Are the facts and procedures stated correctly?
               - Are there contradictions or inconsistencies?
               - Does it contain vague or ambiguous information?
            
            4. CLARITY CHECK:
               - Is the answer clear and understandable?
               - Is it actionable if it's a procedural answer?
               - Does it contain confusing or circular reasoning?
            
            5. RED FLAGS:
               - Generic/template-like responses
               - Overly vague statements
               - Contradictory information
               - Missing critical safety or security steps
               - Irrelevant information padding
            
            You approach each answer thinking "This might not be right" but then evaluate 
            objectively. If the answer passes your rigorous checks, you acknowledge it.
            If it fails, you clearly articulate why.
            """,
            verbose=False,
            llm=self.llm,
            allow_delegation=False,
            reasoning=True
        )
        
        task = Task(
            description=f"""
            Critically verify if the provided answer legitimately addresses the question.
            Approach with primary suspicion but evaluate objectively.
            
            QUESTION:
            {question}
            
            ANSWER TO VERIFY:
            {answer}
            
            VERIFICATION PROTOCOL:
            
            Step 1 - Initial Skepticism:
            Start by assuming this answer might be inadequate. What could be wrong with it?
            
            Step 2 - Relevance Analysis:
            - Does this answer actually address what was asked?
            - Is there a semantic mismatch between question and answer?
            - Is it answering a different question entirely?
            
            Step 3 - Completeness Analysis:
            - Are all aspects of the question addressed?
            - Are critical steps or information missing?
            - Would someone be able to act on this answer fully?
            
            Step 4 - Accuracy Analysis:
            - Do the facts/procedures make sense?
            - Are there contradictions or inconsistencies?
            - Is information too vague to be useful?
            
            Step 5 - Red Flag Detection:
            - Generic/boilerplate language without specifics?
            - Missing critical details (contacts, systems, approval steps)?
            - Circular reasoning or non-answers?
            - Information that seems irrelevant or padding?
            
            Step 6 - Objective Conclusion:
            Despite your initial skepticism, if the answer passes all checks, acknowledge it.
            If it fails any checks, be specific about what's wrong.
            
            SCORING GUIDE:
            - 0.0-0.3: Answer is inadequate/wrong (reject)
            - 0.4-0.6: Answer has issues but partial value (clarify)
            - 0.7-0.8: Answer is good with minor concerns (accept with notes)
            - 0.9-1.0: Answer is comprehensive and legitimate (accept)
            
            Provide your verification with complete objectivity.
            """,
            expected_output="""Structured verification with:
            1. is_valid: true/false
            2. confidence_score: 0.0-1.0
            3. reasoning: detailed explanation
            4. concerns: specific issues identified
            5. recommendation: accept/reject/clarify""",
            agent=agent,
            output_pydantic=VerificationOutput
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )
        
        result = crew.kickoff()
        
        verification_result = {
            "is_valid": result.pydantic.is_valid,
            "confidence_score": result.pydantic.confidence_score,
            "reasoning": result.pydantic.reasoning,
            "concerns": result.pydantic.concerns,
            "recommendation": result.pydantic.recommendation
        }

        print(verification_result)
        print("================================================")
        print(f"Question: {question}")
        print(f"Answer: {answer}")
        print(f"Verification Result: {verification_result}")
        print("================================================")
        return verification_result

