import os
import sys

# Adiciona o diretório raiz ao sys.path para permitir imports absolutos
# como 'from platform_backend.main import app'
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from platform_backend.main import app

# Vercel serverless function entry point
# O Vercel procura por uma variável 'app' no módulo definido em 'builds'
