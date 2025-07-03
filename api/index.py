import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.main import app

# Vercel expects a callable named 'app'
# FastAPI instances are already ASGI applications