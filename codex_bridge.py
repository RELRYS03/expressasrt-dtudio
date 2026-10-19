"""OpenAI Codex/GPT bridge for Express'Arte Studio.

Reads the API key exclusively from the local .env file or environment
variable OPENAI_API_KEY. Never hardcodes credentials. Complements the
existing GitHub Copilot and Ollama integrations as a third AI provider.
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"
MAX_PROMPT = 2000
MAX_CONTEXT = 3000
MAX_HISTORY = 6
REQUEST_TIMEOUT = 90  # seconds

SYSTEM_GUIDANCE = (
    "Você é o assistente de IA (Codex/GPT) do Express'Arte Studio, "
    "um editor 3D para impressão. Responda em português brasileiro claro e objetivo. "
    "Ajude o usuário com modelagem 3D, materiais, fatiamento, impressão 3D, "
    "Blender, Mesh Doctor e operações do Studio. "
    "Não afirme ter executado operações se não recebeu confirmação. "
    "Nunca altere arquivos nem peça tokens, segredos ou senhas. "
    "O contexto geométrico fornecido é apenas texto de diagnóstico. "
    "Recomende confirmação no Blender ou fatiador quando necessário."
)


class CodexUnavailable(RuntimeError):
    """OpenAI API is unreachable or misconfigured."""


class CodexUnauthorized(CodexUnavailable):
    """API key is missing, invalid or expired."""


def _load_env_file() -> dict[str, str]:
    """Parse .env file from project root without external dependencies."""
    env_path = Path(__file__).resolve().parent / ".env"
    values: dict[str, str] = {}
    if not env_path.is_file():
        return values
    try:
        with open(env_path, encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if "=" not in stripped:
                    continue
                key, _, value = stripped.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"")
                if key:
                    values[key] = value
    except OSError:
        pass
    return values


def _get_api_key() -> str | None:
    """Resolve OPENAI_API_KEY from env var or .env file."""
    key = os.environ.get("OPENAI_API_KEY")
    if key and key.strip() and not key.startswith("sk-sua-chave"):
        return key.strip()
    env_values = _load_env_file()
    key = env_values.get("OPENAI_API_KEY")
    if key and key.strip() and not key.startswith("sk-sua-chave"):
        return key.strip()
    return None


def _get_model() -> str:
    """Resolve model from env var, .env file or default."""
    model = os.environ.get("EXPRESSARTE_CODEX_MODEL")
    if model and model.strip():
        return model.strip()
    env_values = _load_env_file()
    model = env_values.get("EXPRESSARTE_CODEX_MODEL")
    if model and model.strip():
        return model.strip()
    return DEFAULT_MODEL


def available() -> bool:
    """Check if an OpenAI API key is configured."""
    return _get_api_key() is not None


def status() -> dict[str, Any]:
    """Return Codex/OpenAI availability status."""
    key = _get_api_key()
    model = _get_model()
    if key:
        return {
            "ok": True,
            "provider": "openai-codex",
            "configured": True,
            "model": model,
            "message": f"OpenAI configurado com modelo {model}.",
            "privacy": "Pergunta e contexto opcional são enviados à API da OpenAI via HTTPS.",
        }
    return {
        "ok": True,
        "provider": "openai-codex",
        "configured": False,
        "model": model,
        "message": "Chave OPENAI_API_KEY não encontrada. Adicione no arquivo .env do projeto.",
        "privacy": "Pergunta e contexto opcional são enviados à API da OpenAI via HTTPS.",
    }


def validate_payload(payload: object) -> tuple[str, str, list[tuple[str, str]], str]:
    """Validate chat request payload for Codex provider."""
    if not isinstance(payload, dict):
        raise ValueError("Requisição inválida.")
    question = payload.get("message")
    context = payload.get("context", "")
    history = payload.get("history", [])
    model = payload.get("model", _get_model())

    if not isinstance(question, str) or not question.strip() or len(question) > MAX_PROMPT:
        raise ValueError(f"Digite uma pergunta de até {MAX_PROMPT} caracteres.")
    if not isinstance(context, str) or len(context) > MAX_CONTEXT:
        raise ValueError("Contexto do projeto excedeu o limite.")
    if not isinstance(history, list) or len(history) > MAX_HISTORY:
        raise ValueError("Histórico de conversa inválido.")
    if not isinstance(model, str) or not model.strip():
        model = _get_model()

    messages: list[tuple[str, str]] = []
    for entry in history:
        if not isinstance(entry, dict) or entry.get("role") not in ("user", "assistant"):
            raise ValueError("Histórico de conversa inválido.")
        value = entry.get("text")
        if not isinstance(value, str) or len(value) > 1500:
            raise ValueError("Histórico de conversa excedeu o limite.")
        messages.append((entry["role"], value))

    return question.strip(), context, messages, model.strip()


def build_messages(
    message: str, context: str, history: list[tuple[str, str]]
) -> list[dict[str, str]]:
    """Build OpenAI chat messages array with system guidance and context."""
    msgs: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_GUIDANCE}]

    if context:
        msgs.append({
            "role": "system",
            "content": f"DADOS RESUMIDOS DA CENA (dados fornecidos com consentimento):\n{context}",
        })

    for role, text in history:
        msgs.append({"role": role, "content": text})

    msgs.append({"role": "user", "content": message})
    return msgs


def run_prompt(
    message: str,
    context: str = "",
    history: list[tuple[str, str]] | None = None,
    model: str | None = None,
) -> str:
    """Send a chat completion request to OpenAI API."""
    api_key = _get_api_key()
    if not api_key:
        raise CodexUnavailable(
            "Chave OPENAI_API_KEY não configurada. Adicione no arquivo .env do projeto."
        )

    use_model = model or _get_model()
    msgs = build_messages(message, context, history or [])
    payload = json.dumps({
        "model": use_model,
        "messages": msgs,
        "max_tokens": 4096,
        "temperature": 0.7,
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENAI_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            choices = result.get("choices", [])
            if not choices:
                raise CodexUnavailable("OpenAI retornou resposta vazia.")
            content = choices[0].get("message", {}).get("content", "")
            if not isinstance(content, str) or not content.strip():
                raise CodexUnavailable("OpenAI retornou conteúdo vazio.")
            return content.strip()[:10000]
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
        if exc.code in (401, 403):
            raise CodexUnauthorized(
                "Chave OPENAI_API_KEY inválida ou expirada. Verifique em https://platform.openai.com/api-keys"
            ) from None
        if exc.code == 429:
            raise CodexUnavailable("Limite de requisições da OpenAI atingido. Aguarde e tente novamente.") from None
        logging.error("OpenAI HTTP error %s: %s", exc.code, body)
        raise CodexUnavailable(f"Erro da OpenAI (HTTP {exc.code}).") from None
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise CodexUnavailable(f"Não foi possível conectar à API da OpenAI: {exc}") from None