import os
from collections.abc import Mapping

from katalogin.gemini import GeminiClient
from katalogin.llm import LLMClient
from katalogin.openai_compat import OpenAICompatClient


MODEL_DEFAULT = "gemini-3.6-flash"
BASE_URL_OPENAI_DEFAULT = "https://api.openai.com/v1"


def buat_klien_dari_env(env: Mapping[str, str] | None = None) -> LLMClient | None:
    sumber = os.environ if env is None else env
    provider_mentah = sumber.get("KATALOGIN_LLM_PROVIDER", "gemini")
    provider = provider_mentah.strip().lower()

    if provider == "gemini":
        kunci = sumber.get("GEMINI_API_KEY", "").strip()
        if not kunci:
            kunci = sumber.get("KATALOGIN_LLM_API_KEY", "").strip()
        if not kunci:
            return None

        model = sumber.get("KATALOGIN_LLM_MODEL", MODEL_DEFAULT).strip() or MODEL_DEFAULT
        return GeminiClient(kunci, model)

    if provider == "openai":
        kunci = sumber.get("KATALOGIN_LLM_API_KEY", "").strip()
        if not kunci:
            return None

        model = sumber.get("KATALOGIN_LLM_MODEL", "").strip()
        if not model:
            raise ValueError("KATALOGIN_LLM_MODEL wajib diisi untuk provider openai")

        base_url = (
            sumber.get("KATALOGIN_LLM_BASE_URL", BASE_URL_OPENAI_DEFAULT)
            .strip()
            .rstrip("/")
        )
        if not base_url.startswith(("http://", "https://")):
            raise ValueError(
                "KATALOGIN_LLM_BASE_URL harus diawali http:// atau https://"
            )
        return OpenAICompatClient(kunci, model, base_url)

    raise ValueError(
        "KATALOGIN_LLM_PROVIDER tidak dikenal: "
        f"{provider_mentah.strip()}. Pilihan: gemini, openai"
    )
