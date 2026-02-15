"""
Entrypoint da API na Vercel (FastAPI).
vercel.json encaminha todas as rotas para este arquivo.
Localmente: python run_platform_backend.py
"""
from platform_backend.main import app
