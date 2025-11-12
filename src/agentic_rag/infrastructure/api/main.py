from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import threading
from agentic_rag.application.rag_pipeline import RAGWithReranker
from agentic_rag.domain.utils import PathConfig
from fastapi.middleware.cors import CORSMiddleware


# ====== FastAPI App ======
app = FastAPI(
    title="ConversaLite API", 
    description="API for Agentic-RAG intelligent Q&A pipeline with Reranker and Chroma integration.", 
    version="0.6.0", 
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config_file = str(PathConfig.get_config_path())


class QueryRequest(BaseModel):
    question: str


# Global variable for RAG system (initialized lazily)
rag_system = None


def get_rag_system():
    """Get or initialize the RAG system (lazy initialization)"""
    global rag_system
    if rag_system is None:
        rag_system = RAGWithReranker(
            collection_name="my_files",
            reranker_model="BAAI/bge-reranker-base",
            initial_k=10,
            rerank_top_k=3,
            score_threshold=0.0,
            verification_threshold=0.25,
            use_query_expansion=True
        )
    return rag_system


@app.on_event("startup")
def startup_event():
    """Initialize RAG system and start watcher on application startup"""
    # Initialize RAG system
    # Run watcher in a background thread so it doesn't block FastAPI
    try:
        from agentic_rag.infrastructure.connectors.sharepoint.main import watcher
        thread = threading.Thread(target=watcher.run, daemon=True)
        thread.start()
    except ImportError:
        print("[WARNING] SharePoint watcher not available")


@app.post("/ask")
def ask_question(req: QueryRequest):
    """Query the RAG system with a question"""
    rag = get_rag_system()
    result = rag.query(req.question, verbose=False)
    answer = result["answer"]
    return {"question": req.question, "answer": answer}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("agentic_rag.infrastructure.api.main:app", host="0.0.0.0", port=8100, reload=True)

