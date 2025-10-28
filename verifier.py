from crewai import Agent, Task, Crew
from crewai.llm import LLM as BaseLLM
import yaml
import requests
from pydantic import BaseModel, Field
from config import PathConfig


class VerificationOutput(BaseModel):
    """Output schema for answer verification"""
    
    is_relevant_context: bool = Field(..., description="Conext relevance to the question")
    reasoning: str = Field(..., description="Detailed explanation of the verification decision")
    answer: str = Field(..., description="Answer to the question")

class AnswerVerificationAgent:
    """
    CrewAI agent that intelligently verifies if retrieved context is relevant to a question
    and generates accurate answers from the context when relevant.
    """
    
    def __init__(self, llm_config_path: str = None):
        """
        Initialize the context verification and answer generation agent.
        
        Args:
            llm_config_path: Path to LLM configuration file (defaults to PathConfig)
        """
        print("[INFO] Initializing Context Verification and Answer Generation Agent...")
        llm_config_path = llm_config_path or str(PathConfig.get_llm_config_path())
        self.llm_config = self._load_yaml(llm_config_path)
        self.llm = self._init_llm()
        print("[INFO] Context Verification and Answer Generation Agent ready")
    
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
    
    def verify_context_and_answer(self, question: str, context: str) -> dict:
        """
        Intelligently verify if the provided context is relevant to the question.
        If relevant, generate a smart answer from the context.
        
        Args:
            question: The question asked by the user
            context: The retrieved context to verify and use for answering
            
        Returns:
            Dictionary containing verification results with the following keys:
            - is_relevant_context: bool indicating if context is relevant to question
            - reasoning: detailed explanation of relevance and answer generation
            - answer: the generated answer from context (or empty if not relevant)
        """
        agent = Agent(
            role="Context Relevance Analyst and Answer Generator",
            goal="Intelligently verify context relevance to questions and generate accurate answers from relevant context",
            backstory="""You are an expert context analyst and answer generation specialist.
            Your primary responsibility is to evaluate whether retrieved context is actually
            relevant to a given question, and if so, generate a high-quality answer from that context.
            
            Your two-phase evaluation process:
            
            PHASE 1: CONTEXT RELEVANCE VERIFICATION
            ========================================
            You first determine if the provided context has ANY meaningful connection to the question:
            
            1. SEMANTIC RELEVANCE:
               - Does the context discuss topics directly related to the question?
               - Are there keywords, concepts, or entities that match?
               - Is there topical alignment between context and question?
            
            2. INFORMATION UTILITY:
               - Does the context contain information that could help answer the question?
               - Even if partial, does it provide useful details?
               - Could someone use this context to address the question?
            
            3. REJECTION CRITERIA (mark as NOT relevant):
               - Context discusses completely different topics
               - No semantic overlap between context and question
               - Context is about a different domain/subject entirely
               - Context provides zero useful information for the question
            
            PHASE 2: INTELLIGENT ANSWER GENERATION (if relevant)
            =====================================================
            If context IS relevant, generate a smart, accurate answer:
            
            1. EXTRACT KEY INFORMATION:
               - Identify all relevant facts, procedures, steps from context
               - Synthesize information across different parts of context
               - Focus on what directly addresses the question
            
            2. GENERATE COMPREHENSIVE ANSWER:
               - Provide clear, complete answer based on context
               - Include specific details (contacts, steps, systems, etc.)
               - Structure answer logically and clearly
               - Stay faithful to the context - don't hallucinate
            
            3. ENSURE QUALITY:
               - Answer should be actionable and useful
               - Include all critical information from context
               - Be concise but complete
               - Maintain accuracy to source context
            
            You are objective and intelligent - if context is relevant (even partially), 
            you recognize it and generate the best possible answer. If context is truly
            irrelevant, you clearly mark it as such without attempting to force an answer.
            """,
            verbose=False,
            llm=self.llm,
            allow_delegation=False,
            # reasoning=True,
            #max_reasoning_attempts=1
        )
        
        task = Task(
            description=f"""
            Your task is to intelligently verify if the provided context is relevant to the question,
            and if so, generate a smart, accurate answer from that context.
            
            QUESTION:
            {question}
            
            RETRIEVED CONTEXT:
            {context}
            
            EVALUATION PROTOCOL:
            
            STEP 1: CONTEXT RELEVANCE CHECK
            ================================
            Analyze if the context has ANY meaningful connection to the question:
            
            - Does the context discuss the same topic/subject as the question?
            - Are there matching keywords, concepts, entities, or themes?
            - Does the context contain information that could help answer the question?
            - Is there semantic alignment between context and question?
            
            DECISION CRITERIA:
            
            ✓ Mark as RELEVANT if:
              - Context discusses the topic asked about
              - Context contains information useful for answering
              - There is clear topical/semantic overlap
              - Context provides even partial information related to question
            
            ✗ Mark as NOT RELEVANT if:
              - Context is about a completely different topic
              - Zero semantic overlap with question
              - Context provides no useful information for the question
              - Complete domain/subject mismatch
            
            STEP 2: ANSWER GENERATION (only if context is relevant)
            ========================================================
            If context IS relevant, generate a comprehensive answer:
            
            1. EXTRACT all relevant information from context:
               - Identify key facts, procedures, steps, details
               - Find specific information (contacts, systems, dates, etc.)
               - Note any important requirements or conditions
            
            2. SYNTHESIZE into a clear answer:
               - Directly address the question
               - Include all relevant details from context
               - Structure logically and clearly
               - Be specific and actionable
               - Stay faithful to context - no hallucinations
            
            3. ENSURE COMPLETENESS:
               - Cover all aspects the context addresses
               - Include critical details (who, what, when, where, how)
               - Make answer useful and actionable
            
            STEP 3: OUTPUT GENERATION
            =========================
            
            If context is RELEVANT:
            - is_relevant_context: true
            - reasoning: Explain why context is relevant and how you generated the answer
            - answer: Your comprehensive, well-structured answer from the context
            
            If context is NOT RELEVANT:
            - is_relevant_context: false
            - reasoning: Explain why context is not relevant to the question
            - answer: "" (empty string)
            
            Be intelligent and objective in your evaluation.
            """,
            expected_output="""Structured output with:
            1. is_relevant_context: true/false
            2. reasoning: detailed explanation
            3. answer: generated answer from context (or empty if not relevant)""",
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
            "is_relevant_context": result.pydantic.is_relevant_context,
            "reasoning": result.pydantic.reasoning,
            "answer": result.pydantic.answer
        }

        print("\n" + "="*80)
        print("CONTEXT VERIFICATION AND ANSWER GENERATION")
        print("="*80)
        print(f"Question: {question}")
        print(f"\nContext Preview: {context[:200]}..." if len(context) > 200 else f"\nContext: {context}")
        print(f"\nIs Context Relevant: {verification_result['is_relevant_context']}")
        print(f"\nReasoning: {verification_result['reasoning']}")
        if verification_result['is_relevant_context']:
            print(f"\nGenerated Answer: {verification_result['answer']}")
        else:
            print("\nNo answer generated (context not relevant)")
        print("="*80 + "\n")
        
        return verification_result

