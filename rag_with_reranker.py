import os
from typing import List, Tuple, Optional
from sentence_transformers import SentenceTransformer, CrossEncoder
import chromadb
from generator import LanguageModel
from expander import QueryExpansionAgent
from verifier import AnswerVerificationAgent
import verifier
from config import PathConfig

class BGEReranker:
    """BGE-based re-ranker for improving retrieval results."""
    
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):

        print(f"[INFO] Loading BGE re-ranker: {model_name}")
        self.reranker = CrossEncoder(model_name)
        print(f"[INFO] Re-ranker loaded successfully")
    
    def rerank(
        self, 
        query: str, 
        documents: List[str], 
        top_k: Optional[int] = None
    ) -> List[Tuple[int, float]]:
        """
        Re-rank documents based on query relevance.
        
        Args:
            query: The search query
            documents: List of documents to re-rank
            top_k: Number of top results to return (None = all)
            
        Returns:
            List of (original_index, score) tuples sorted by score descending
        """
        # Create pairs of (query, doc) for re-ranking
        pairs = [[query, doc] for doc in documents]
        
        # Get scores from re-ranker
        scores = self.reranker.predict(pairs)
        
        # Create list of (index, score) and sort by score descending
        ranked_results = [(idx, float(score)) for idx, score in enumerate(scores)]
        ranked_results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k if specified
        if top_k is not None:
            ranked_results = ranked_results[:top_k]
        
        return ranked_results



class RAGWithReranker:
    """RAG system with BGE re-ranker for improved context selection."""
    
    def __init__(
        self,
        config_path: str = None,
        db_path: str = None,
        collection_name: str = "my_files",
        reranker_model: str = "BAAI/bge-reranker-base",
        initial_k: int = 10,
        rerank_top_k: int = 3,
        score_threshold: float = 0.0,
        verification_threshold: float = 0.25,
        use_query_expansion: bool = True,
        llm_config_path: str = None
    ):
        """
        Initialize RAG system with re-ranker and query expansion.
        
        Args:
            config_path: Path to config file for LLM (defaults to PathConfig)
            db_path: Path to ChromaDB storage (defaults to PathConfig)
            collection_name: Name of Chroma collection
            reranker_model: BGE re-ranker model to use
            initial_k: Number of documents to retrieve initially
            rerank_top_k: Number of top re-ranked docs to use as context
            score_threshold: Minimum re-ranker score to include document
            verification_threshold: Score threshold below which verification agent is invoked
            use_query_expansion: Enable query expansion (generates 3 queries)
            llm_config_path: Path to LLM config for query expansion agent (defaults to PathConfig)
        """
        # Use PathConfig defaults if not provided
        config_path = config_path or str(PathConfig.get_config_path())
        db_path = db_path or str(PathConfig.get_db_path())
        llm_config_path = llm_config_path or str(PathConfig.get_llm_config_path())
        
        # Setup ChromaDB and embedder
        print("[INFO] Setting up ChromaDB connection...")
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(collection_name)
        self.verifier = AnswerVerificationAgent(llm_config_path=llm_config_path)
        
        # Same embedder used for indexing
        print("[INFO] Loading embedding model...")
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Setup re-ranker
        self.reranker = BGEReranker(model_name=reranker_model)
        
        # Setup query expansion agent if enabled
        self.use_query_expansion = use_query_expansion
        self.query_expander = None
        if use_query_expansion:
            self.query_expander = QueryExpansionAgent(llm_config_path=llm_config_path)
        
        # Setup LLM
        print("[INFO] Initializing language model...")
        self.llm = LanguageModel(config_path)
        
        # Configuration
        self.initial_k = initial_k
        self.rerank_top_k = rerank_top_k
        self.score_threshold = score_threshold
        self.verification_threshold = verification_threshold
        
        print(f"[INFO] RAG with Re-ranker initialized successfully")
        print(f"[INFO] Config: initial_k={initial_k}, rerank_top_k={rerank_top_k}, threshold={score_threshold}")
        if use_query_expansion:
            print(f"[INFO] Query Expansion: ENABLED - generates 3 expanded queries")
    
    def retrieve_and_rerank(
        self, 
        query: str,
        verbose: bool = True
    ) -> Tuple[List[str], List[dict], List[float]]:
        """
        Retrieve documents from Chroma and re-rank them.
        
        Args:
            query: Search query
            verbose: Whether to print debug information
            
        Returns:
            Tuple of (selected_documents, metadatas, scores)
        """
        # Step 1: Initial retrieval from ChromaDB
        if verbose:
            print(f"\n[STEP 1] Retrieving top {self.initial_k} documents from ChromaDB...")
        
        query_embedding = self.embedder.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=self.initial_k
        )
        
        initial_docs = results["documents"][0]
        initial_metas = results["metadatas"][0]
        
        if verbose:
            print(f"[INFO] Retrieved {len(initial_docs)} documents")
        
        # Step 2: Re-rank using BGE
        if verbose:
            print(f"\n[STEP 2] Re-ranking documents with BGE...")
        
        ranked_indices_scores = self.reranker.rerank(
            query=query,
            documents=initial_docs,
            top_k=None  # Get all scores first
        )
        
        # Step 3: Filter by score threshold and select top_k
        selected_docs = []
        selected_metas = []
        selected_scores = []
        
        if verbose:
            print(f"\n[STEP 3] Selecting top {self.rerank_top_k} documents (threshold={self.score_threshold})...")
            print("\nRe-ranking Results:")
        
        for rank, (orig_idx, score) in enumerate(ranked_indices_scores[:self.rerank_top_k], 1):
            if score >= self.score_threshold:
                selected_docs.append(initial_docs[orig_idx])
                selected_metas.append(initial_metas[orig_idx])
                selected_scores.append(score)
                
                if verbose:
                    file_name = initial_metas[orig_idx].get('file', 'unknown')
                    chunk_num = initial_metas[orig_idx].get('chunk', '?')
                    print(f"  #{rank} [Score: {score:.4f}] {os.path.basename(file_name)} (chunk {chunk_num})")
        
        if verbose:
            print(f"\n[INFO] Selected {len(selected_docs)} documents for context")
        
        return selected_docs, selected_metas, selected_scores
    

    
    def build_context(
        self, 
        documents: List[str], 
        metadatas: List[dict],
        scores: List[float]
    ) -> str:
        """
        Build context string from selected documents.
        
        Args:
            documents: Selected documents
            metadatas: Metadata for each document
            scores: Re-ranker scores
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, (doc, meta, score) in enumerate(zip(documents, metadatas, scores), 1):
            file_name = os.path.basename(meta.get('file', 'unknown'))
            chunk_num = meta.get('chunk', '?')
            
            context_parts.append(
                f"[Source {i}: {file_name}, Chunk {chunk_num}, Relevance: {score:.2f}]\n{doc}"
            )
        
        return "\n\n" + "="*80 + "\n\n".join(context_parts)
    
    def query(self, query: str, verbose: bool = True) -> dict:
        """
        Complete RAG pipeline with query expansion.
        
        This method implements query expansion:
        1. Generate 3 expanded queries
        2. Retrieve and rerank for all 3 queries
        3. Use the query with the best score
        
        Args:
            query: User query
            verbose: Whether to print debug information
            
        Returns:
            Dictionary with answer, context, and metadata
        """
        if verbose:
            print("="*80)
            print(f"🔍 Original Query: {query}")
            print("="*80)
        
        if self.use_query_expansion or self.query_expander:

            if verbose:
                print("[INFO] Query expansion is enabled")
                print(f"[INFO] Generating 3 expanded queries...")
                expanded_queries = self.query_expander.expand_query(query)

                print(f"[INFO] Generated {len(expanded_queries)} queries:")
                for i, eq in enumerate(expanded_queries, 1):
                    print(f"  {i}. {eq}")
        else:
            expanded_queries = [query]
        

        
        # Track best result across all 3 queries
        best_result = None
        best_score = -1
        
        # Try each expanded query
        for i, expanded_query in enumerate(expanded_queries, 1):
            if verbose:
                print(f"\n{'-'*80}")
                print(f"🔍 Query {i}/{len(expanded_queries)}")
                print(f"Query: '{expanded_query}'")
                print(f"{'-'*80}")
            
            # Retrieve and re-rank
            documents, metadatas, scores = self.retrieve_and_rerank(
                expanded_query, 
                verbose=verbose
            )
            
            # Check results
            if not documents or not scores:
                max_score = 0.0
                if verbose:
                    print(f"[WARNING] No documents retrieved")
            else:
                max_score = max(scores)
                
                # Update best result
                if max_score > best_score:
                    best_score = max_score
                    best_result = {
                        "documents": documents,
                        "metadatas": metadatas,
                        "scores": scores,
                        "query_used": expanded_query,
                        "query_index": i
                    }
                    if verbose:
                        print(f"\n✅ [NEW BEST] Score: {max_score:.4f}")
                else:
                    if verbose:
                        print(f"\n⚠️  Score: {max_score:.4f} (best so far: {best_score:.4f})")
        
        # Check if we found anything
        if best_result is None or best_score <= 0:
            if verbose:
                print(f"\n{'='*80}")
                print("❌ [NO RESULTS] No relevant documents found")
                print(f"{'='*80}\n")
            
            return {
                "query": query,
                "answer": "No information available. I couldn't find relevant documents for this query.",
                "context": "",
                "sources": [],
                "scores": [],
                "best_score": best_score
            }
        
        # Use best result
        documents = best_result["documents"]
        metadatas = best_result["metadatas"]
        scores = best_result["scores"]
        query_used = best_result["query_used"]
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"📊 [FINAL RESULTS]")
            print(f"   Best Query: #{best_result['query_index']}")
            print(f"   Query used: '{query_used}'")
            print(f"   Best score: {best_score:.4f}")
            print(f"{'='*80}")
        
        # Build context
        context = self.build_context(documents, metadatas, scores)
        
        # Generate answer
        if verbose:
            print(f"\n[STEP 4] Generating answer with LLM...")
        
        answer = self.llm.generate_answer(query, context)

        if best_score < self.verification_threshold:
            print(f"[INFO] Answer score is less than {self.verification_threshold}. Verifying answer...")
            verification_result = self.verifier.verify_answer(question=query, answer=answer)

            if not verification_result['is_valid']:
                print(f"[INFO] Answer is not valid. Returning no information available.")
                return {
                    "query": query,
                    "query_used": query_used,
                    "answer": "No information available. I couldn't find relevant documents for this query.",
                    "context": "",
                    "sources": [],
                    "scores": [],
                    "best_score": best_score
                }
        
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"📝 Answer:\n{answer}")
            print(f"{'='*80}\n")
        
        return {
            "query": query,
            "query_used": query_used,
            "answer": answer,
            "context": context,
            "sources": [
                {
                    "file": meta.get("file"),
                    "chunk": meta.get("chunk"),
                    "score": score
                }
                for meta, score in zip(metadatas, scores)
            ],
            "scores": scores,
            "best_score": best_score
        }



def main():
    """Example usage of RAG with re-ranker and query expansion."""
    
    # Initialize RAG system with re-ranker and query expansion
    # Uses PathConfig defaults for all paths
    rag = RAGWithReranker(
        collection_name="my_files",
        reranker_model="BAAI/bge-reranker-base",  # Change to "BAAI/bge-reranker-v2-m3" for multilingual
        initial_k=10,              # Retrieve 10 documents initially
        rerank_top_k=3,            # Use top 3 after re-ranking
        score_threshold=0.0,       # Minimum score to include in context
        verification_threshold=0.25,  # Invoke verification agent if score < 0.25
        use_query_expansion=True   # Enable query expansion (generates 3 queries)
    )
    
    print("\n" + "="*80)
    print("RAG SYSTEM WITH QUERY EXPANSION FOR SOP MATCHING")
    print("="*80)
    print("\n[INFO] This system uses query expansion:")
    print("[INFO] - Generates 3 expanded queries")
    print("[INFO] - Tries all 3 queries and selects best result")
    print("[INFO] - Original query is NOT used, only expanded versions")
    print("\n[INFO] Query transformations (questions → information statements):")
    print("  - 'What is password reset?' → 'password reset process procedure steps'")
    print("  - 'How to request SSL?' → 'SSL certificate request procedure guidelines'")
    print("\n" + "="*80 + "\n")
    
    # Example queries - these will be transformed from questions to statements
    queries = [
        "What is the facility whose Tariff ID ends with 4875?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n\n{'#'*80}")
        print(f"# QUERY {i}/{len(queries)}")
        print(f"{'#'*80}\n")
        
        result = rag.query(query, verbose=True)
        
        # Display summary
        print(f"\n{'='*80}")
        print("QUERY SUMMARY")
        print("="*80)
        print(f"Original Query: {result['query']}")
        print(f"Query Used:     {result.get('query_used', 'N/A')}")
        print(f"Best Score:     {result['best_score']:.4f}")
        print(f"Sources:        {len(result['sources'])} documents")
        print("="*80)
        
        if i < len(queries):
            print("\n\n" + "~"*80)
            print("Moving to next query...")
            print("~"*80)


if __name__ == "__main__":
    main()

