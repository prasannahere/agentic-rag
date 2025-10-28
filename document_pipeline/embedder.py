import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import PathConfig

def setup_chroma(db_path=None, collection_name="my_files"):
    """Setup Chroma persistent client and SentenceTransformer embedder."""
    # Use PathConfig default if not provided
    db_path = db_path or str(PathConfig.get_db_path())
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(collection_name)
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return collection, embedder
