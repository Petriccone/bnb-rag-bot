"""
Camada 3 - Execução: Text-to-Speech.
Gera áudio a partir do texto (OpenAI TTS). Áudios curtos: ~20–30 s (~150–200 palavras).
"""

import os
from pathlib import Path

from openai import OpenAI

# Máximo de caracteres para manter áudio em ~20–30 s (aprox. 1 palavra = 2 chars em PT)
MAX_CHARS_FOR_AUDIO = 400


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _get_client() -> OpenAI:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise ValueError("OPENAI_API_KEY não configurado.")
    return OpenAI(api_key=key)


def _truncate_for_audio(text: str, max_chars: int = MAX_CHARS_FOR_AUDIO) -> str:
    """Trunca o texto para caber em áudio curto (evitar voz longa demais)."""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    # Cortar em último espaço para não quebrar palavra
    cut = text[:max_chars].rsplit(maxsplit=1)[0]
    if not cut:
        return text[:max_chars]
    return cut + "…"


def synthesize(
    text: str,
    output_path: str | Path | None = None,
    model: str = "tts-1",
    voice: str = "nova",
) -> str:
    """
    Converte texto em áudio usando OpenAI TTS.
    Retorna o caminho do arquivo gerado (.mp3).
    output_path: se None, gera em .tmp/ com nome único.
    voice: nova (feminina), alloy, echo, fable, onyx, shimmer.
    """
    text = _truncate_for_audio(text)
    if not text:
        raise ValueError("Texto vazio após truncagem.")

    client = _get_client()
    if output_path is None:
        tmp_dir = _project_root() / ".tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        output_path = tmp_dir / "tts_output.mp3"

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
    )
    response.stream_to_file(str(path))
    return str(path)


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv(_project_root() / ".env")
    t = sys.argv[1] if len(sys.argv) > 1 else "Olá! Como posso te ajudar hoje?"
    out = synthesize(t)
    print("Áudio salvo em:", out)
