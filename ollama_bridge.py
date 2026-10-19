"""Ollama local AI bridge for Express'Arte Studio.

Provides a second AI provider that runs entirely locally via Ollama,
requiring no API keys or external network access. Complements the
existing GitHub Copilot SDK integration.
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "llama3.2"
MAX_PROMPT = 2000
MAX_CONTEXT = 3000
MAX_HISTORY = 6
REQUEST_TIMEOUT = 120  # seconds

SYSTEM_GUIDANCE = (
    "Você é o assistente de IA local do Express'Arte Studio, "
    "um editor 3D para impressão. Responda em português brasileiro claro e objetivo. "
    "Ajude o usuário com modelagem 3D, materiais, fatiamento, impressão 3D, "
    "Blender, Mesh Doctor e operações do Studio. "
    "Não afirme ter executado operações se não recebeu confirmação. "
    "Nunca altere arquivos nem peça tokens, segredos ou senhas. "
    "O contexto geométrico fornecido é apenas texto de diagnóstico. "
    "Recomende confirmação no Blender ou fatiador quando necessário."
)


class OllamaUnavailable(RuntimeError):
    """Ollama server is not running or not reachable."""


class OllamaModelError(RuntimeError):
    """Requested model is not available in Ollama."""


def available() -> bool:
    """Check if Ollama is running and responsive."""
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


def status() -> dict[str, Any]:
    """Return Ollama availability status and installed models."""
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "") for m in data.get("models", [])]
            return {
                "ok": True,
                "provider": "ollama-local",
                "server_running": True,
                "default_model": DEFAULT_MODEL,
                "available_models": models[:20],
                "message": f"Ollama ativo com {len(models)} modelo(s) instalado(s).",
                "privacy": "Todas as conversas são processadas localmente. Nenhum dado sai do seu computador.",
            }
    except (urllib.error.URLError, OSError, TimeoutError):
        return {
            "ok": True,
            "provider": "ollama-local",
            "server_running": False,
            "default_model": DEFAULT_MODEL,
            "available_models": [],
            "message": "Ollama não está rodando. Instale em https://ollama.com e execute 'ollama serve'.",
            "privacy": "Todas as conversas são processadas localmente. Nenhum dado sai do seu computador.",
        }


def validate_payload(payload: object) -> tuple[str, str, list[tuple[str, str]], str]:
    """Validate chat request payload for Ollama provider."""
    if not isinstance(payload, dict):
        raise ValueError("Requisição inválida.")
    question = payload.get("message")
    context = payload.get("context", "")
    history = payload.get("history", [])
    model = payload.get("model", DEFAULT_MODEL)

    if not isinstance(question, str) or not question.strip() or len(question) > MAX_PROMPT:
        raise ValueError(f"Digite uma pergunta de até {MAX_PROMPT} caracteres.")
    if not isinstance(context, str) or len(context) > MAX_CONTEXT:
        raise ValueError("Contexto do projeto excedeu o limite.")
    if not isinstance(history, list) or len(history) > MAX_HISTORY:
        raise ValueError("Histórico de conversa inválido.")
    if not isinstance(model, str) or not model.strip():
        model = DEFAULT_MODEL

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
    """Build Ollama chat messages array with system guidance and context."""
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
    """Send a chat completion request to local Ollama server."""
    if not available():
        raise OllamaUnavailable(
            "Ollama não está rodando. Instale em https://ollama.com e execute 'ollama serve'."
        )

    use_model = model or DEFAULT_MODEL
    msgs = build_messages(message, context, history or [])
    payload = json.dumps({
        "model": use_model,
        "messages": msgs,
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result.get("message", {}).get("content", "")
            if not isinstance(content, str) or not content.strip():
                raise OllamaUnavailable("Ollama retornou uma resposta vazia.")
            return content.strip()[:10000]
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
        if exc.code == 404:
            raise OllamaModelError(
                f"Modelo '{use_model}' não encontrado. Execute 'ollama pull {use_model}' para instalar."
            ) from None
        logging.error("Ollama HTTP error %s: %s", exc.code, body)
        raise OllamaUnavailable(f"Erro do Ollama (HTTP {exc.code}).") from None
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise OllamaUnavailable(f"Não foi possível conectar ao Ollama: {exc}") from None