"""MiniMind Local AI bridge for Express'Arte Studio.
Connects to a locally running MiniMind instance via its OpenAI-compatible API.
Provides a lightweight, offline-capable assistant for 3D modeling descriptions
and creative assistance without external API keys.
"""
from __future__ import annotations
import json
import logging
import urllib.error
import urllib.request
from typing import Any
MINIMIND_API_URL = "http://127.0.0.1:8998/v1/chat/completions"
DEFAULT_MODEL = "minimind"
MAX_PROMPT = 2000
MAX_CONTEXT = 3000
MAX_HISTORY = 6
REQUEST_TIMEOUT = 120 # seconds
SYSTEM_GUIDANCE = (
"Você é o assistente MiniMind do Express'Arte Studio, focado em arte religiosa e modelagem 3D. "
"Responda em português brasileiro claro e objetivo. Ajude com ideias para chaveiros, estátuas, "
"presépios e outros itens litúrgicos. Seja conciso e técnico quando necessário."
)
class MiniMindUnavailable(RuntimeError):
"""MiniMind server is not running or not reachable."""
def available() -> bool:
"""Check if MiniMind is running and responsive."""
try:
# Simple check by trying to reach the base URL or a known endpoint
req = urllib.request.Request("http://127.0.0.1:8998", method="GET")
with urllib.request.urlopen(req, timeout=5) as resp:
return resp.status in [200, 404] # 404 is ok if the server is up but path is wrong
except Exception:
return False
def status() -> dict[str, Any]:
"""Return MiniMind availability status."""
is_up = available()
return {
"ok": True,
"provider": "minimind-local",
"server_running": is_up,
"default_model": DEFAULT_MODEL,
"message": (
"MiniMind ativo localmente." if is_up else
"MiniMind não está rodando. Execute 'python scripts/serve_openai_api.py' no diretório minimind-repo."
),
"privacy": "Todas as conversas são processadas localmente na sua máquina.",
}
def validate_payload(payload: object) -> tuple[str, str, list[tuple[str, str]]]:
"""Validate chat request payload."""
if not isinstance(payload, dict):
raise ValueError("Requisição inválida.")
question = payload.get("message")
context = payload.get("context", "")
history = payload.get("history", [])
if not isinstance(question, str) or not question.strip() or len(question) > MAX_PROMPT:
raise ValueError(f"Digite uma pergunta de até {MAX_PROMPT} caracteres.")
if not isinstance(context, str) or len(context) > MAX_CONTEXT:
raise ValueError("Contexto do projeto excedeu o limite.")
if not isinstance(history, list) or len(history) > MAX_HISTORY:
raise ValueError("Histórico de conversa inválido.")
messages: list[tuple[str, str]] = []
for entry in history:
if not isinstance(entry, dict) or entry.get("role") not in ("user", "assistant"):
raise ValueError("Histórico de conversa inválido.")
value = entry.get("text")
if not isinstance(value, str) or len(value) > 1500:
raise ValueError("Histórico de conversa excedeu o limite.")
messages.append((entry["role"], value))
return question.strip(), context, messages
def build_messages(message: str, context: str, history: list[tuple[str, str]]) -> list[dict[str, str]]:
"""Build MiniMind/OpenAI chat messages array."""
msgs: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_GUIDANCE}]
if context:
msgs.append({
"role": "system",
"content": f"CONTEXTO DA CENA: {context}",
})
for role, text in history:
msgs.append({"role": role, "content": text})
msgs.append({"role": "user", "content": message})
return msgs
def run_prompt(
message: str,
context: str = "",
history: list[tuple[str, str]] | None = None,
) -> str:
"""Send a chat completion request to local MiniMind server."""
if not available():
raise MiniMindUnavailable(
"MiniMind não está rodando na porta 8998. Inicie o servidor local primeiro."
)
msgs = build_messages(message, context, history or [])
payload = json.dumps({
"model": DEFAULT_MODEL,
"messages": msgs,
"stream": False,
"max_tokens": 1024,
}).encode("utf-8")
req = urllib.request.Request(
MINIMIND_API_URL,
data=payload,
headers={"Content-Type": "application/json"},
method="POST",
)
try:
with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
result = json.loads(resp.read().decode("utf-8"))
choices = result.get("choices", [])
if not choices:
raise MiniMindUnavailable("MiniMind retornou uma resposta vazia.")
content = choices[0].get("message", {}).get("content", "")
if not isinstance(content, str) or not content.strip():
raise MiniMindUnavailable("MiniMind retornou conteúdo vazio.")
return content.strip()[:5000]
except urllib.error.HTTPError as exc:
body = ""
try:
body = exc.read().decode("utf-8", errors="replace")[:300]
except Exception:
pass
logging.error("MiniMind HTTP error %s: %s", exc.code, body)
raise MiniMindUnavailable(f"Erro do MiniMind (HTTP {exc.code}).") from None
except (urllib.error.URLError, OSError, TimeoutError) as exc:
raise MiniMindUnavailable(f"Não foi possível conectar ao MiniMind: {exc}") from None