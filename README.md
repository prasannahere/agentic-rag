# Agentic-RAG

An advanced Retrieval-Augmented Generation (RAG) system designed for enterprise document management and intelligent question-answering. It connects to multiple data sources, processes documents, and provides contextually accurate answers using sophisticated retrieval and verification mechanisms.

## 🌟 Key Features

### Multi-Agent Architecture
- **Query Expansion Agent**: Generates multiple query variations to improve retrieval coverage
- **BGE Re-ranker Agent**: Re-ranks retrieved documents using BAAI/bge-reranker models for better relevance
- **Answer Verification Agent**: Validates generated answers to ensure quality and accuracy

### Multi-Source Document Integration
- **SharePoint Connector**: Watches and syncs documents from SharePoint
- **Azure Blob Storage**: Monitors and processes files from Azure Blob containers
- **Google Drive**: Tracks and downloads documents from Google Drive folders
- **Auto-Watch**: Continuous monitoring with automatic processing of new documents

### Advanced RAG Pipeline
- **Semantic Search**: Uses sentence transformers (all-MiniLM-L6-v2) for embeddings
- **Vector Storage**: ChromaDB for efficient similarity search
- **Query Expansion**: Transforms questions into multiple semantic variations
- **Re-ranking**: BGE-based cross-encoder for improved context selection
- **Answer Verification**: LLM-based validation with confidence scoring

### Document Processing
- Supports multiple formats: PDF, DOCX, PPTX, TXT, and more
- Intelligent chunking and text splitting
- Metadata extraction and tracking
- OCR support for scanned documents

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Sources Layer                       │
├──────────────┬──────────────┬─────────────────┬─────────────┤
│  SharePoint  │  Azure Blob  │  Google Drive   │   Local     │
└──────┬───────┴──────┬───────┴────────┬────────┴──────┬──────┘
       │              │                │               │
       └──────────────┴────────────────┴───────────────┘
                            │
                    ┌───────▼────────┐
                    │  File Watchers │
                    │  + Processors  │
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │   Document     │
                    │   Pipeline     │
                    │ • Embedder     │
                    │ • Indexer      │
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │   ChromaDB     │
                    │ Vector Storage │
                    └───────┬────────┘
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
┌──────▼──────┐   ┌─────────▼────────┐   ┌──────▼──────┐
│   Query     │   │   BGE Reranker   │   │  Verifier   │
│  Expansion  │   │      Agent       │   │    Agent    │
└──────┬──────┘   └─────────┬────────┘   └──────┬──────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                    ┌───────▼────────┐
                    │   LLM Answer   │
                    │   Generation   │
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │  FastAPI REST  │
                    │      API       │
                    └────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Azure Storage account (for Blob connector)
- SharePoint credentials (for SP connector)
- Google Cloud service account (for Drive connector)
- OpenAI API key or compatible LLM endpoint

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd agentic-rag
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure data sources**

Create/update configuration files in the `config/` directory:

- `config.json` - Google Drive configuration
- `sp-config.json` - SharePoint configuration
- `llm_config.yaml` - LLM settings
- `expander_prompts.yaml` - Query expansion prompts
- `service_account.json` - Google Cloud credentials

4. **Start the API server**
```bash
python main.py
```

The API will be available at `http://localhost:8100`

## 📖 Usage

### API Endpoint

**POST /ask**
```bash
curl -X POST "http://localhost:8100/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the password reset procedure?"}'
```

Response:
```json
{
  "question": "What is the password reset procedure?",
  "answer": "Based on the documents, the password reset procedure involves..."
}
```

### Python SDK

```python
from rag_with_reranker import RAGWithReranker

# Initialize the RAG system
rag = RAGWithReranker(
    collection_name="my_files",
    reranker_model="BAAI/bge-reranker-base",
    initial_k=10,              # Initial retrieval count
    rerank_top_k=3,            # Top results after reranking
    score_threshold=0.0,       # Minimum relevance score
    verification_threshold=0.25,  # Verification trigger threshold
    use_query_expansion=True   # Enable query expansion
)

# Query the system
result = rag.query("What is the SSL certificate renewal process?")

print(result["answer"])
print(f"Sources: {len(result['sources'])}")
print(f"Best score: {result['best_score']:.4f}")
```

### Running Individual Connectors

```bash
# SharePoint connector
python runners/run_spconnector.py

# Azure Blob connector
python runners/run_blobconnector.py

# Google Drive connector
python runners/run_gdrive.py
```

## 🔧 Configuration

### LLM Configuration (`config/llm_config.yaml`)
```yaml
model: gpt-4
temperature: 0.7
max_tokens: 1000
api_key: your-api-key
```

### Query Expansion Prompts (`config/expander_prompts.yaml`)
Configure how queries are expanded for better retrieval coverage.

### Data Source Configurations
- **SharePoint**: `config/sp-config.json`
- **Azure Blob**: Configure in `blobconnector/azure_blob_api.py`
- **Google Drive**: `config/config.json`

## 🎯 Advanced Features

### Query Expansion
The system automatically generates 3 variations of each query:
- Original semantic meaning preserved
- Question → Statement transformation
- Multiple perspectives on the same topic

### Re-ranking Pipeline
1. Initial retrieval: Top 10 documents via semantic search
2. Re-ranking: BGE cross-encoder scores all candidates
3. Selection: Top 3 highest-scoring documents
4. Threshold filtering: Only includes documents above score threshold

### Answer Verification
- Automatically triggered when confidence score < 0.25
- Validates answer against retrieved context
- Returns "No information available" for low-confidence responses

## 📁 Project Structure

```
agentic-rag/
├── blobconnector/         # Azure Blob Storage integration
├── spconnector/           # SharePoint integration
├── gdrive/                # Google Drive integration
├── document_pipeline/     # Document processing and indexing
├── runners/               # Standalone connector runners
├── config/                # Configuration files
├── data/                  # Downloaded documents and cache
├── chroma_store/          # ChromaDB vector storage
├── rag_with_reranker.py   # Main RAG implementation
├── generator.py           # LLM answer generation
├── expander.py            # Query expansion agent
├── verifier.py            # Answer verification agent
├── main.py                # FastAPI server
└── requirements.txt       # Python dependencies
```

## 🔍 How It Works

1. **Document Ingestion**: Watchers monitor data sources for new documents
2. **Processing**: Documents are chunked, embedded, and stored in ChromaDB
3. **Query Processing**: User queries are expanded into multiple variations
4. **Retrieval**: Each query variation retrieves top-k documents
5. **Re-ranking**: BGE re-ranker scores all candidates for relevance
6. **Answer Generation**: LLM generates answer using top-scored context
7. **Verification**: Low-confidence answers are validated or rejected

## 🛠️ Technology Stack

- **Vector Store**: ChromaDB
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Re-ranker**: BAAI/bge-reranker-base
- **LLM**: OpenAI GPT / Compatible endpoints
- **API Framework**: FastAPI
- **Document Processing**: LangChain, PyPDF, python-docx
- **Cloud Integrations**: Azure SDK, Google Drive API, SharePoint API

## 📊 Performance Tuning

### Retrieval Parameters
- `initial_k`: Number of documents to retrieve initially (default: 10)
- `rerank_top_k`: Number of documents after re-ranking (default: 3)
- `score_threshold`: Minimum relevance score (default: 0.0)

### Quality Controls
- `verification_threshold`: Trigger verification below this score (default: 0.25)
- `use_query_expansion`: Enable/disable query expansion (default: True)

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Code follows existing patterns
- Documentation is updated
- Tests pass (if applicable)

## 📝 License

[Add your license here]

## 🆘 Support

For issues, questions, or contributions, please [open an issue](link-to-issues) or contact the development team.

---

**Built with ❤️ for enterprise document intelligence**

