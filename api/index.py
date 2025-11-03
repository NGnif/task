# Vercel serverless entry point for the Flask app
from app import create_app

# Vercel expects a module-level `app`
app = create_app()

