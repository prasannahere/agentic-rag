"""
Centralized configuration for Agentic-RAG paths and settings.

This module provides a single source of truth for all file paths used throughout
the application, ensuring portability across different environments and operating systems.
"""

from pathlib import Path
import os


class PathConfig:
    """Central configuration for all file paths in the application."""
    
    # Auto-detect project root (where config.py is located)
    PROJECT_ROOT = Path(__file__).parent.resolve()
    
    # Configuration directories and files
    CONFIG_DIR = PROJECT_ROOT / "config"
    LLM_CONFIG = CONFIG_DIR / "llm_config.yaml"
    EXPANDER_PROMPTS = CONFIG_DIR / "expander_prompts.yaml"
    SERVICE_ACCOUNT = CONFIG_DIR / "service_account.json"
    SP_CONFIG = CONFIG_DIR / "sp-config.json"
    
    # Data directories
    DATA_DIR = PROJECT_ROOT / "data"
    DOWNLOADED_FILES = DATA_DIR / "downloaded_files"
    
    # SharePoint data directories
    SP_DATA_DIR = DATA_DIR / "spdata"
    SP_DOWNLOADED_FILES = SP_DATA_DIR / "sp_downloaded_files"
    SP_SEEN_FILES = SP_DATA_DIR / "sp_seen_files.json"
    
    # Blob storage data directories
    BLOB_DATA_DIR = DATA_DIR / "blob-data"
    BLOB_DOWNLOADED_FILES = BLOB_DATA_DIR / "blob_downloaded_files"
    BLOB_SEEN_FILES = BLOB_DATA_DIR / "blob_seen_files.json"
    
    # Database paths
    CHROMA_STORE = PROJECT_ROOT / "chroma_store"
    
    # Environment variable overrides (optional)
    @classmethod
    def get_db_path(cls, override: str = None) -> Path:
        """
        Get the ChromaDB path with optional override.
        
        Args:
            override: Optional path override. If None, checks environment variable.
            
        Returns:
            Path object for the ChromaDB store.
        """
        if override:
            return Path(override)
        env_path = os.getenv('CHROMA_DB_PATH')
        return Path(env_path) if env_path else cls.CHROMA_STORE
    
    @classmethod
    def get_config_path(cls, override: str = None) -> Path:
        """
        Get the main config file path with optional override.
        
        Args:
            override: Optional path override. If None, checks environment variable.
            
        Returns:
            Path object for the config file.
        """
        if override:
            return Path(override)
        env_path = os.getenv('CONFIG_PATH')
        return Path(env_path) if env_path else cls.LLM_CONFIG
    
    @classmethod
    def get_llm_config_path(cls, override: str = None) -> Path:
        """
        Get the LLM config file path with optional override.
        
        Args:
            override: Optional path override. If None, checks environment variable.
            
        Returns:
            Path object for the LLM config file.
        """
        if override:
            return Path(override)
        env_path = os.getenv('LLM_CONFIG_PATH')
        return Path(env_path) if env_path else cls.LLM_CONFIG
    
    @classmethod
    def ensure_directories(cls):
        """Create all necessary directories if they don't exist."""
        directories = [
            cls.CONFIG_DIR,
            cls.DATA_DIR,
            cls.DOWNLOADED_FILES,
            cls.SP_DATA_DIR,
            cls.SP_DOWNLOADED_FILES,
            cls.BLOB_DATA_DIR,
            cls.BLOB_DOWNLOADED_FILES,
            cls.CHROMA_STORE,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Convenience function for backward compatibility
def get_project_root() -> Path:
    """Get the project root directory."""
    return PathConfig.PROJECT_ROOT

