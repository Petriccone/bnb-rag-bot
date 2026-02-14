"""
Camada 3 - Execução: Speech-to-Text via OpenAI Whisper.
Recebe caminho do arquivo de áudio (ex.: baixado do Telegram), retorna texto.
"""

import os
from pathlib import Path

from openai import OpenAI

# Limite de tamanho para a API (25 MB para Whisper)
MAX_FILE_SIZE_MB = 25


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _get_client() -> OpenAI:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise ValueError("OPENAI_API_KEY não configurado.")
    return OpenAI(api_key=key)


def transcribe(audio_path: str | Path, language: str | None = "pt") -> str:
    """
    Transcreve áudio para texto usando Whisper.
    audio_path: caminho local do arquivo (ogg, mp3, wav, m4a, etc.).
    language: código ISO (pt para português); None para detecção automática.
    """
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de áudio não encontrado: {path}")
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"Arquivo muito grande ({size_mb:.1f} MB). Máximo: {MAX_FILE_SIZE_MB} MB.")

    client = _get_client()
    with open(path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language=language,
            response_format="text",
        )
    if isinstance(transcript, str):
        return transcript.strip()
    return (getattr(transcript, "text", None) or "").strip()


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv(_project_root() / ".env")
    if len(sys.argv) < 2:
        print("Uso: python -m execution.stt <caminho_audio>")
        sys.exit(1)
    print(transcribe(sys.argv[1]))
