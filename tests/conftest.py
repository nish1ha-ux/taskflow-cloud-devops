import os
import sys

# Add the repository root to sys.path so that 'app.app' is importable.
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, repo_root)
