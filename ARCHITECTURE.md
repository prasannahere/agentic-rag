# Agentic RAG Architecture

This document describes the layered architecture of the Agentic RAG system.

## Architecture Overview

The project follows a clean, layered architecture pattern with clear separation of concerns:

```
agentic-rag/
├── src/
│   └── agentic_rag/
│       ├── domain/              # Domain Layer - Business logic and core entities
│       │   ├── exceptions.py    # Custom exceptions
│       │   ├── state.py         # State management models
│       │   ├── utils.py         # PathConfig and utilities
│       │   └── prompts/         # Prompt templates
│       │
│       ├── application/         # Application Layer - Business workflows
│       │   ├── agents/          # AI agents (expander, verifier)
│       │   │   ├── expander.py
│       │   │   └── verifier.py
│       │   └── rag_pipeline.py  # Main RAG pipeline orchestration
│       │
│       └── infrastructure/      # Infrastructure Layer - External integrations
│           ├── api/             # FastAPI application
│           │   └── main.py
│           ├── persistence/    # Database and storage
│           │   ├── embedder.py
│           │   └── indexer.py
│           ├── llm/            # LLM clients
│           │   └── generator.py
│           └── connectors/     # External data source connectors
│               ├── sharepoint/
│               ├── blob/
│               └── gdrive/
│
├── config/                     # Configuration files
├── data/                       # Data storage
├── chroma_store/              # ChromaDB vector store
├── tests/                      # Test suite
├── Dockerfile                 # Containerization
├── docker-compose.yaml        # Docker Compose configuration
└── pyproject.toml            # Project metadata and dependencies
```

## Layer Responsibilities

### Domain Layer (`domain/`)
- **Purpose**: Core business logic, models, and domain entities
- **Contains**:
  - Exception definitions
  - State management models (QueryState, DocumentState)
  - Path configuration utilities
  - Prompt templates
- **Dependencies**: None (pure Python, no external frameworks)

### Application Layer (`application/`)
- **Purpose**: Business workflows and orchestration
- **Contains**:
  - RAG pipeline orchestration
  - Query expansion agent
  - Answer verification agent
  - Business logic for document processing
- **Dependencies**: Domain layer, Infrastructure layer

### Infrastructure Layer (`infrastructure/`)
- **Purpose**: External integrations and technical implementations
- **Contains**:
  - **API**: FastAPI REST endpoints
  - **Persistence**: ChromaDB, embeddings, indexing
  - **LLM**: Language model clients
  - **Connectors**: SharePoint, Azure Blob, Google Drive integrations
- **Dependencies**: Domain layer, Application layer

### Tests Layer (`tests/`)
- **Purpose**: Test suite for all layers
- **Contains**: Unit tests, integration tests, fixtures

## Containerization

The project includes Docker support for easy deployment:

- **Dockerfile**: Defines the application container
- **docker-compose.yaml**: Orchestrates services and volumes
- **Environment variables**: Configured via `.env` file

## Configuration

Configuration is managed through:
- `config/llm_config.yaml`: LLM settings
- `config/expander_prompts.yaml`: Query expansion prompts
- `config/sp-config.json`: SharePoint configuration
- `config/config.json`: Google Drive configuration
- `.env`: Environment variables (API keys, paths)

## Running the Application

### Local Development
```bash
make install
make run
```

### Docker
```bash
make docker-build
make docker-up
```

### API Endpoints
- `POST /ask`: Query the RAG system
- `GET /health`: Health check

## Benefits of This Architecture

1. **Separation of Concerns**: Each layer has a clear responsibility
2. **Testability**: Easy to test each layer independently
3. **Maintainability**: Changes in one layer don't affect others
4. **Scalability**: Easy to add new connectors or features
5. **Portability**: Can swap implementations (e.g., different vector DBs)

