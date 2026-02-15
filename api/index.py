"""
Entrypoint para Vercel (função em api/).
Repassa para o mesmo app do platform_backend.
"""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from platform_backend.main import app
