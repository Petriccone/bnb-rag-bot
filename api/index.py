import os
import sys
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Adiciona o diretório raiz ao sys.path para permitir imports absolutos
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

try:
    from platform_backend.main import app
except Exception as e:
    # DEBUG MODE: Se falhar ao importar o app, cria um app de fallback
    # que retorna o erro para o usuário ver no navegador.
    error_msg = f"Startup Error: {str(e)}"
    error_trace = traceback.format_exc()
    
    app = FastAPI()

    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
    async def catch_all(path_name: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Vercel Startup Failed",
                "message": error_msg,
                "traceback": error_trace.split("\n"),
                "sys_path": sys.path,
                "cwd": os.getcwd(),
                "dir_contents": os.listdir(os.getcwd()) if os.path.exists(os.getcwd()) else "cwd not found"
            }
        )
