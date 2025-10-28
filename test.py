from fastapi import FastAPI
from pydantic import BaseModel
from generator import LanguageModel
from document_pipeline.embedder import setup_chroma
from spconnector.main import watcher
import uvicorn
import threading
from rag_with_reranker import RAGWithReranker
from config import PathConfig

# ====== Core RAG Pipeline ======
class RAGPipeline:
    def __init__(self, config_path: str):
        self.lm = LanguageModel(config_path)
        self.collection, self.embedder = setup_chroma()

    def run_query(self, query: str, n_results: int = 5) -> str:

        query_emb = self.embedder.encode([query]).tolist()
        results = self.collection.query(query_embeddings=query_emb, n_results=n_results)
        context = "\n\n".join(results["documents"][0])
        print(results["documents"])

        return self.lm.generate_answer(query, context)


def ask_question(req: str):
    
    #answer = rag_pipeline.run_query(req.question, req.n_results) 

    # Uses PathConfig defaults for all paths
    client  = RAGWithReranker(
        collection_name="my_files",
        reranker_model="BAAI/bge-reranker-base",  # Change to "BAAI/bge-reranker-v2-m3" for multilingual
        initial_k=10,      # Retrieve 10 documents initially
        rerank_top_k=3,    # Use top 3 after re-ranking
        score_threshold=0.0  # Minimum score to include
    )
    answer=client.query(req)
    answer=answer["answer"]
    return {"question": req, "answer": answer}

if __name__ == "__main__":
    print(ask_question("string"))