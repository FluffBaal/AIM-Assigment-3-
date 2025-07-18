import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set upload directory to /tmp for Vercel serverless
os.environ['UPLOAD_DIR'] = '/tmp/uploads'

from backend.app.main import app

# Vercel expects a callable named 'app' for ASGI applications
# FastAPI instances are already ASGI applications
app = app