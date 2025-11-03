# Vercel serverless entry point for the Flask app
import os
import tempfile

# Ensure a writable instance path for Flask on serverless FS
_inst = os.path.join(tempfile.gettempdir(), "flask-instance")
try:
    os.makedirs(_inst, exist_ok=True)
except Exception:
    pass
os.environ.setdefault("INSTANCE_PATH", _inst)

from app import create_app

# Vercel expects a module-level `app`
app = create_app()
