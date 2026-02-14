"""
Script para subir o platform backend (FastAPI).
Use: python run_platform_backend.py
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "platform_backend.main:app",
        host="0.0.0.0",  # aceita conexões de localhost e de outras interfaces (evita "contactar o servidor" no Windows)
        port=8000,
        reload=True,
    )
