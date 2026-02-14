"""
Entrypoint da API para Vercel (FastAPI). Detectado automaticamente sem "builds" no vercel.json.
Localmente use: python run_platform_backend.py
"""
from platform_backend.main import app
