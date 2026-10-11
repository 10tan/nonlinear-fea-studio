import sys
import os

# Add backend source directory to python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend", "src"))

from fea.api.app import app
