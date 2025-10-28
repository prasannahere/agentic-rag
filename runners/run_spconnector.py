"""
Standalone runner for SharePoint connector.
Run this from the project root: python -m runners.run_spconnector
"""
import sys
from pathlib import Path

# Ensure the project root is in the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now import and run the spconnector
from spconnector.main import watcher

if __name__ == "__main__":
    print("Starting SharePoint connector...")
    print("=" * 50)
    watcher.run()


