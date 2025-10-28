"""
Standalone runner for Azure Blob Storage connector.
Run this from the project root: python -m runners.run_blobconnector
"""
import sys
from pathlib import Path

# Ensure the project root is in the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now import and run the blobconnector
from blobconnector.main import watcher

if __name__ == "__main__":
    print("Starting Azure Blob Storage connector...")
    print("=" * 50)
    watcher.run()


