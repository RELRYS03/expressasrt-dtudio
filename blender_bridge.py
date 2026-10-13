"""Bridge local Express'Arte -> Blender. Sem shell, sem código enviado pelo usuário.

A API recebe somente dados estruturados para uma operação com script empacotado.
Nada é enviado a provedores externos. Um trabalho Blender por vez.
"""
from __future__ import annotations
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / 'bridge' / 'make_medal.py'
FORMATS = {"stl": "application/sla", "glb": "model/gltf-binary", "blend": "application/octet-stream"}
MAX_JOBS = 24
JOB_TIMEOUT = 180
HEX = re.compile(r'^#[0-9a-fA-F]{6}$')


def find_blender() -> Path | None:
    supplied = os.getenv('EXPRESSARTE_BLENDER_PATH', '').strip().strip('"')
    if not supplied:
        config_file = ROOT / 'dados' / 'blender_path.txt'
        if config_file.is_file():
            supplied = config_file.read_text(encoding='utf-8').strip().strip('\"')
    if supplied:
        p = Path(supplied).expanduser()
        return p if p.is_file() else None
    binary = shutil.which('blender') or shutil.which('blender.exe')
    if binary:
        return Path(binary)
    if os.name == 'nt':
        parents = [os.getenv('PROGRAMFILES'), os.getenv('PROGRAMFILES(X86)'), os.getenv('LOCALAPPDATA')]
        candidates = []
        for base in parents:
            if not base:
                continue
            root = Path(base) / 'Blender Foundation'
            if root.exists():
                candidates.extend(root.glob('Blender */blender.exe'))
                candidates.extend(root.glob('Blender/blender.exe'))
        if candidates:
            return sorted(candidates, reverse=True)[0]
    return None


def blender_status() -> dict:
    exe = find_blender()
    if not exe:
        msg = ('Blender não encontrado automaticamente. Configure EXPRESSARTE_BLENDER_PATH com o caminho de blender.exe. '
               'O Studio continua funcionando, mas a modelagem Blender fica desativada.')
        return {'ok': True, 'available': False, 'message': msg, 'version': None}
    try:
        p = subprocess.run([str(exe), '--version'], capture_output=True, text=True, timeout=12, check=False)
        if p.returncode != 0:
            raise RuntimeError('blender --version retornou erro')
        version = (p.stdout or p.stderr).splitlines()[0][:90]
        return {'ok': True, 'available': True, 'version': version, 'message': 'Blender localizado no computador.', 'path': str(exe)}
    except (OSError, subprocess.TimeoutExpired, RuntimeError) as exc:
        return {'ok': True, 'available': False, 'version': None, 'message': f'Blender encontrado, mas não pôde iniciar: {exc}'}


def normalize_medal(payload: object) -> dict:
    if not isinstance(payload, dict) or len(payload) > 20:
        raise ValueError('Informe um projeto de medalha válido.')
    allowed = {'name', 'diameter', 'thickness', 'text_height', 'ring', 'shape', 'base_color', 'text_color', 'accent_color', 'border'}
    if set(payload) - allowed:
        raise ValueError('Campo desconhecido na configuração da medalha.')
    name = payload.get('name', 'EXPRESS ARTE')
    if not isinstance(name, str) or len(name.strip()) < 1 or len(name.strip()) > 22:
        raise ValueError('Texto deve ter entre 1 e 22 caracteres.')
    if any(ord(c) < 32 for c in name):
        raise ValueError('Texto contém caracteres inválidos.')
    result = {'name': name.strip()}
    specs = [('diameter', 80., 35., 180.), ('thickness', 3., 2., 12.), ('text_height', 1.2, 0.4, 5.)]
    for field, default, lo, hi in specs:
        v = payload.get(field, default)
        if isinstance(v, bool) or not isinstance(v, (float, int)):
            raise ValueError(f'{field} precisa ser número.')
        val = float(v)
        if not lo <= val <= hi:
            raise ValueError(f'{field} fora do intervalo permitido: {lo}–{hi}.')
        result[field] = val
    if result['text_height'] > result['thickness'] * 1.5:
        raise ValueError('Alto-relevo excessivo para a base. Reduza o texto.')
    ring = payload.get('ring', True)
    if not isinstance(ring, bool):
        raise ValueError('A argola deve ser ligada ou desligada.')
    result['ring'] = ring
    border = payload.get('border', True)
    if not isinstance(border, bool):
        raise ValueError('O aro decorativo deve ser ligado ou desligado.')
    result['border'] = border
    shape = payload.get('shape', 'circle')
    if shape not in ('circle', 'hexagon', 'shield'):
        raise ValueError('Formato inválido. Use círculo, hexágono ou escudo.')
    result['shape'] = shape
    defaults = {'base_color': '#6B3E26', 'text_color': '#F2DFBE', 'accent_color': '#C98C58'}
    for key, default in defaults.items():
        val = payload.get(key, default)
        if not isinstance(val, str) or not HEX.fullmatch(val):
            raise ValueError(f'Cor inválida: {key}.')
        result[key] = val.upper()
    return result


class BridgeJobs:
    """Guarda estado somente em memória; saídas somente em dados/blender_jobs/<uuid>."""
    def __init__(self, data_dir: Path):
        self.root = data_dir / 'blender_jobs'
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix='expressarte-blender')
        self.jobs: dict[str, dict] = {}

    def submit(self, config: object) -> dict:
        cfg = normalize_medal(config)
        exe = find_blender()
        if not exe:
            raise FileNotFoundError('Blender não encontrado. Configure EXPRESSARTE_BLENDER_PATH com o caminho completo do blender.exe.')
        if not SCRIPT.is_file():
            raise RuntimeError('Script de modelagem ausente no pacote.')
        with self.lock:
            active = sum(v['status'] in ('waiting', 'working') for v in self.jobs.values())
            if active >= 2:
                raise OverflowError('Duas tarefas já aguardam processamento. Aguarde e tente novamente.')
            job_id = str(uuid.uuid4())
            entry = {'id': job_id, 'status': 'waiting', 'message': 'Aguardando Blender', 'created': time.time(), 'config': cfg, 'files': []}
            self.jobs[job_id] = entry
            self.pool.submit(self._run, job_id, str(exe))
            return self.public(job_id)

    def public(self, job_id: str) -> dict | None:
        with self.lock:
            entry = self.jobs.get(job_id)
            if not entry:
                return None
            return {k: entry[k] for k in ('id', 'status', 'message', 'files')}

    def _run(self, job_id: str, exe: str):
        with self.lock:
            cfg = self.jobs[job_id]['config']
            self.jobs[job_id].update(status='working', message='Modelando medalha no Blender…')
        directory = self.root / job_id
        directory.mkdir(mode=0o700, exist_ok=True)
        config_path = directory / 'config.json'
        config_path.write_text(json.dumps(cfg, ensure_ascii=False), encoding='utf-8')
        command = [exe, '--background', '--factory-startup', '--python-exit-code', '8', '--python', str(SCRIPT), '--', str(config_path), str(directory)]
        try:
            proc = subprocess.run(command, capture_output=True, text=True, timeout=JOB_TIMEOUT, check=False)
            (directory / 'exec.log').write_text(((proc.stdout or '') + '\n' + (proc.stderr or ''))[-14000:], encoding='utf-8')
            if proc.returncode != 0:
                raise RuntimeError(f'Blender retornou código {proc.returncode}. Confira o log local dados/blender_jobs/{job_id}/exec.log')
            expected = {'stl': directory / 'Expressarte_Medalha.stl', 'glb': directory / 'Expressarte_Medalha.glb', 'blend': directory / 'Expressarte_Medalha.blend'}
            for ext, path in expected.items():
                if not path.is_file() or path.stat().st_size < 20:
                    raise RuntimeError(f'O Blender não criou um arquivo {ext.upper()} válido.')
            stl = expected['stl'].read_bytes()
            if len(stl) < 84 or len(stl) != 84 + 50 * int.from_bytes(stl[80:84], 'little'):
                raise RuntimeError('Blender exportou um STL inválido/incompleto.')
            if expected['glb'].read_bytes()[:4] != b'glTF':
                raise RuntimeError('Blender exportou um GLB sem cabeçalho válido.')
            files = [{'format': ext.upper(), 'url': f'/api/blender/jobs/{job_id}/files/{ext}', 'bytes': path.stat().st_size} for ext, path in expected.items()]
            with self.lock:
                self.jobs[job_id].update(status='done', files=files, message='Modelagem concluída. Revise no fatiador antes de imprimir.')
        except subprocess.TimeoutExpired:
            with self.lock:
                self.jobs[job_id].update(status='error', message='O Blender excedeu o limite de 3 minutos para esta tarefa.')
        except Exception as exc:
            with self.lock:
                self.jobs[job_id].update(status='error', message=str(exc)[:260])
        finally:
            config_path.unlink(missing_ok=True)

    def download(self, job_id: str, extension: str) -> tuple[Path, str] | None:
        with self.lock:
            entry = self.jobs.get(job_id)
            if not entry or entry['status'] != 'done' or extension not in FORMATS:
                return None
        path = self.root / job_id / f'Expressarte_Medalha.{extension}'
        if not path.is_file():
            return None
        return path, FORMATS[extension]
