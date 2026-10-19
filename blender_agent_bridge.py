"""Blender Agent Bridge for Express'Arte Studio.
Connects to a running Blender instance via a local HTTP server (addon) or TCP socket.
Translates natural language commands into Blender Python API calls.
Supports: creating keychains, characters, basic shapes, and editing existing objects.
"""
from __future__ import annotations
import json
import logging
import urllib.error
import urllib.request
from typing import Any
BLENDER_API_URL = "http://127.0.0.1:8090/blender/command" # Default port for custom addon
class BlenderUnavailable(RuntimeError):
"""Blender is not running or the API addon is not active."""
def available() -> bool:
"""Check if Blender API endpoint is reachable."""
try:
req = urllib.request.Request(BLENDER_API_URL.replace("/command", "/status"), method="GET")
with urllib.request.urlopen(req, timeout=2) as resp:
return resp.status == 200
except Exception:
return False
def status() -> dict[str, Any]:
"""Return Blender connection status."""
is_up = available()
return {
"ok": True,
"provider": "blender-local",
"connected": is_up,
"message": (
"Blender conectado e pronto para receber comandos." if is_up else
"Blender não detectado. Instale o 'ExpressArte Blender Addon' e inicie o servidor interno."
),
}
def send_command(command: str, params: dict | None = None) -> dict[str, Any]:
"""Send a high-level command to Blender."""
if not available():
raise BlenderUnavailable("Blender não está respondendo na porta 8090.")
payload = {
"command": command,
"params": params or {}
}
req = urllib.request.Request(
BLENDER_API_URL,
data=json.dumps(payload).encode("utf-8"),
headers={"Content-Type": "application/json"},
method="POST",
)
try:
with urllib.request.urlopen(req, timeout=30) as resp:
result = json.loads(resp.read().decode("utf-8"))
if result.get("error"):
raise RuntimeError(f"Erro no Blender: {result['error']}")
return result
except urllib.error.HTTPError as exc:
raise BlenderUnavailable(f"Erro HTTP do Blender: {exc.code}") from None
except Exception as exc:
raise BlenderUnavailable(f"Falha na comunicação com Blender: {exc}") from None
# --- High-level helpers for common tasks ---
def create_keychain(name: str = "Keychain", shape: str = "circle", text: str = ""):
"""Create a simple keychain object."""
params = {"name": name, "shape": shape, "text": text}
return send_command("create_keychain", params)
def create_character(name: str = "Character", type: str = "humanoid"):
"""Create a base character mesh."""
params = {"name": name, "type": type}
return send_command("create_character", params)
def edit_object(obj_name: str, operation: str, **kwargs):
"""Perform an edit on an existing object (e.g., scale, move, rotate)."""
params = {"obj_name": obj_name, "operation": operation, **kwargs}
return send_command("edit_object", params)