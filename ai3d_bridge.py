"""AI 3D Generation bridge for Express'Arte Studio.

Integrates open-source AI-to-3D pipelines discovered via REA analysis:
- Hunyuan3D-2 (Tencent): Image/Text -> GLB via FastAPI (/generate, /send, /status/{uid})
- Pixal3D Pipeline: Batch image -> GLB via ComfyUI watcher (folder-based)
- TRELLIS (Microsoft): Image/Text -> GLB/Gaussian via Gradio API

This bridge provides a unified interface to query available backends and
submit generation jobs. Each backend must be installed and running separately;
this module only orchestrates HTTP calls and folder watching.

All backends are optional and run locally. No data leaves the user's machine
unless the user explicitly configures a remote endpoint.
"""
from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Backend configuration
# ---------------------------------------------------------------------------

HUNYUAN_API_URL = "http://127.0.0.1:8080"
TRELLIS_API_URL = "http://127.0.0.1:7860"
PIXAL3D_INBOX = Path.home() / "Pixal3D-pipeline" / "pipeline" / "inbox"
PIXAL3D_RESULTS = Path.home() / "Pixal3D-pipeline" / "pipeline" / "results"

REQUEST_TIMEOUT = 10  # seconds for status checks


class AI3DBackendUnavailable(RuntimeError):
    """A requested 3D generation backend is not reachable."""


# ---------------------------------------------------------------------------
# Availability checks
# ---------------------------------------------------------------------------

def _check_http(url: str, timeout: int = REQUEST_TIMEOUT) -> bool:
    """Return True if an HTTP GET to *url* returns 200."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def hunyuan_available() -> bool:
    """Check if Hunyuan3D-2 api_server.py is running."""
    return _check_http(f"{HUNYUAN_API_URL}/docs") or _check_http(HUNYUAN_API_URL)


def trellis_available() -> bool:
    """Check if TRELLIS Gradio app is running."""
    return _check_http(f"{TRELLIS_API_URL}/info") or _check_http(TRELLIS_API_URL)


def pixal3d_available() -> bool:
    """Check if Pixal3D inbox folder exists (watcher may or may not be running)."""
    return PIXAL3D_INBOX.is_dir()


# ---------------------------------------------------------------------------
# Status aggregation
# ---------------------------------------------------------------------------

def status() -> dict[str, Any]:
    """Return availability status of all AI-3D backends."""
    backends = []

    h_ok = hunyuan_available()
    backends.append({
        "id": "hunyuan3d",
        "name": "Hunyuan3D-2 (Tencent)",
        "available": h_ok,
        "url": HUNYUAN_API_URL,
        "capabilities": ["text-to-3d", "image-to-3d", "texture-generation"],
        "output_format": "glb",
        "message": (
            "Hunyuan3D-2 API ativa em " + HUNYUAN_API_URL
            if h_ok else
            "Hunyuan3D-2 não está rodando. Execute 'python api_server.py' no diretório Hunyuan3D-2."
        ),
    })

    t_ok = trellis_available()
    backends.append({
        "id": "trellis",
        "name": "TRELLIS (Microsoft)",
        "available": t_ok,
        "url": TRELLIS_API_URL,
        "capabilities": ["image-to-3d", "text-to-3d", "gaussian-splatting", "mesh-export"],
        "output_format": "glb / ply",
        "message": (
            "TRELLIS Gradio ativo em " + TRELLIS_API_URL
            if t_ok else
            "TRELLIS não está rodando. Execute 'python app.py' no diretório TRELLIS."
        ),
    })

    p_ok = pixal3d_available()
    backends.append({
        "id": "pixal3d",
        "name": "Pixal3D Pipeline",
        "available": p_ok,
        "inbox": str(PIXAL3D_INBOX),
        "results": str(PIXAL3D_RESULTS),
        "capabilities": ["batch-image-to-3d", "auto-background-removal"],
        "output_format": "glb",
        "message": (
            f"Pasta inbox encontrada em {PIXAL3D_INBOX}. Coloque imagens lá para gerar modelos automaticamente."
            if p_ok else
            "Pixal3D não configurado. Clone https://github.com/infinition/Pixal3D-pipeline e execute SETUP.bat."
        ),
    })

    return {
        "ok": True,
        "provider": "ai3d-multi-backend",
        "backends": backends,
        "available_count": sum(1 for b in backends if b["available"]),
    }


# ---------------------------------------------------------------------------
# Hunyuan3D-2 async job submission
# ---------------------------------------------------------------------------

def hunyuan_submit(params: dict[str, Any]) -> dict[str, Any]:
    """Submit an async generation job to Hunyuan3D-2.

    Parameters (all optional, passed as JSON body):
        prompt: str          – text description
        image: str           – base64-encoded PNG/JPEG
        octree_resolution: int (default 256)
        num_inference_steps: int (default 20)
        guidance_scale: float (default 7.5)

    Returns {"uid": "..."} on success.
    """
    if not hunyuan_available():
        raise AI3DBackendUnavailable("Hunyuan3D-2 não está rodando.")

    payload = json.dumps(params).encode("utf-8")
    req = urllib.request.Request(
        f"{HUNYUAN_API_URL}/send",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {"ok": True, "uid": data.get("uid"), "backend": "hunyuan3d"}
    except urllib.error.HTTPError as exc:
        raise AI3DBackendUnavailable(f"Hunyuan3D-2 retornou HTTP {exc.code}") from None
    except Exception as exc:
        raise AI3DBackendUnavailable(f"Erro ao enviar job: {exc}") from None


def hunyuan_status(uid: str) -> dict[str, Any]:
    """Poll Hunyuan3D-2 job status. Returns {"ready": True/False, "url": "..."} when done."""
    if not hunyuan_available():
        raise AI3DBackendUnavailable("Hunyuan3D-2 não está rodando.")

    url = f"{HUNYUAN_API_URL}/status/{uid}"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            # The endpoint returns 200 + file path string when ready,
            # or 404 when still processing.
            body = resp.read().decode("utf-8").strip()
            return {"ok": True, "ready": True, "file_path": body, "backend": "hunyuan3d"}
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"ok": True, "ready": False, "backend": "hunyuan3d"}
        raise AI3DBackendUnavailable(f"Hunyuan3D-2 status HTTP {exc.code}") from None
    except Exception as exc:
        raise AI3DBackendUnavailable(f"Erro ao consultar status: {exc}") from None


# ---------------------------------------------------------------------------
# Pixal3D folder-based submission
# ---------------------------------------------------------------------------

def pixal3d_submit_image(image_path: str) -> dict[str, Any]:
    """Copy an image into the Pixal3D inbox folder for batch processing.

    The watcher picks it up automatically within POLL_SECONDS (default 5s).
    """
    src = Path(image_path)
    if not src.is_file():
        raise ValueError(f"Arquivo de imagem não encontrado: {image_path}")
    if not PIXAL3D_INBOX.is_dir():
        raise AI3DBackendUnavailable(
            f"Pasta inbox do Pixal3D não existe: {PIXAL3D_INBOX}. "
            "Execute SETUP.bat do Pixal3D-pipeline primeiro."
        )

    dest = PIXAL3D_INBOX / src.name
    try:
        import shutil
        shutil.copy2(str(src), str(dest))
    except OSError as exc:
        raise AI3DBackendUnavailable(f"Erro ao copiar imagem para inbox: {exc}") from None

    return {
        "ok": True,
        "backend": "pixal3d",
        "inbox_path": str(dest),
        "message": f"Imagem copiada para {dest}. O watcher processará automaticamente.",
    }