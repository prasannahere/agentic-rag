from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from pydantic import BaseModel
from agentic_rag.infrastructure.connectors.upload.main import UploadConnector
import uvicorn
import threading
from agentic_rag.application.rag_pipeline import RAGWithReranker
from agentic_rag.domain.utils import PathConfig
from fastapi.middleware.cors import CORSMiddleware

# ====== Basic Auth ======
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()

# Set your login username & password
USERNAME = "admin"
PASSWORD = "premo123"


def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    """Simple username-password authentication"""
    correct_username = secrets.compare_digest(credentials.username, USERNAME)
    correct_password = secrets.compare_digest(credentials.password, PASSWORD)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            # Remove the WWW-Authenticate header to prevent browser popup
        )
    return True


# ====== FastAPI App ======
app = FastAPI(
    title="ConversaLite API",
    description="API for Agentic-RAG intelligent Q&A pipeline with Reranker and Chroma.",
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


# Global RAG system instance
rag_system = None


def get_rag_system():
    global rag_system
    if rag_system is None:
        rag_system = RAGWithReranker(
            collection_name="my_files",
            reranker_model="BAAI/bge-reranker-base",
            initial_k=10,
            rerank_top_k=3,
            score_threshold=0.0,
            verification_threshold=0.25,
            use_query_expansion=True,
        )
    return rag_system


@app.on_event("startup")
def startup_event():
    """Start SharePoint watcher on startup (if exists)."""
    try:
        from agentic_rag.infrastructure.connectors.sharepoint.main import watcher

        thread = threading.Thread(target=watcher.run, daemon=True)
        thread.start()
    except ImportError:
        print("[WARNING] SharePoint watcher not available")


# ===============================
# PROTECTED ROUTES (Login Required)
# ===============================

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    authenticated: bool = Depends(authenticate)
):
    client = UploadConnector()
    client.upload_file(file.filename, file.file)
    return {"message": f"File '{file.filename}' added to RAG successfully"}


@app.post("/ask")
def ask_question(
    req: QueryRequest,
    authenticated: bool = Depends(authenticate)
):
    rag = get_rag_system()
    result = rag.query(req.question, verbose=False)
    return {"question": req.question, "answer": result["answer"]}


# ===============================
# Public Route
# ===============================

@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ===============================
# Run App
# ===============================
if __name__ == "__main__":
    uvicorn.run("agentic_rag.infrastructure.api.main:app", host="0.0.0.0", port=8100, reload=True)
