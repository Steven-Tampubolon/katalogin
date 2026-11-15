import os
from collections.abc import Mapping

from katalogin.gemini import GeminiClient
from katalogin.llm import LLMClient


MODEL_DEFAULT = "gemini-3.6-flash"


def buat_klien_dari_env(env: Mapping[str, str] | None = None) -> LLMClient | None:
    sumber = os.environ if env is None else env
    kunci = sumber.get("GEMINI_API_KEY", "").strip()
    if not kunci:
        return None

    model = sumber.get("KATALOGIN_LLM_MODEL", MODEL_DEFAULT).strip() or MODEL_DEFAULT
    return GeminiClient(kunci, model)
