#!/usr/bin/env python3
"""Express'Arte V7 — servidor LOCAL, sem frameworks de terceiros.

Publica somente ./site e guarda a comunidade em ./dados (fora da pasta pública).
Padrão 127.0.0.1:8765; NÃO expõe a Internet. Uso pessoal no computador.
"""
from __future__ import annotations
import argparse
import os
import base64
import json
import logging
import re
import sqlite3
import threading
import uuid
import webbrowser
from datetime import datetime, timezone
from email.parser import BytesParser
from email.policy import default
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from blender_bridge import BridgeJobs, blender_status
import copilot_bridge
import ollama_bridge

BASE = Path(__file__).resolve().parent
PUBLIC = BASE / "site"
# No Windows, keep user documents OUTSIDE versioned ZIP folders.
# EXPRESSARTE_DATA_DIR can override location for migration/testing.
DEFAULT_DATA = Path(os.environ.get('LOCALAPPDATA', str(BASE))) / 'ExpressArteStudio' / 'dados' if os.name == 'nt' else BASE / 'dados'
DATA = Path(os.environ.get('EXPRESSARTE_DATA_DIR', str(DEFAULT_DATA))).expanduser().resolve()
UPLOADS = DATA / "arquivos"
DATABASE = DATA / "expressarte.sqlite3"
STUDIO_DIR = DATA / "projetos"
MAX_SCENE_BODY = 36 * 1024 * 1024
MAX_STUDIO_PROJECTS = 80
MAX_BODY = 37 * 1024 * 1024
MAX_MODEL = 25 * 1024 * 1024
MAX_IMAGE = 5 * 1024 * 1024
LIMIT = 50
SQL_LOCK = threading.RLock()
EXT_MODELS = {'.stl', '.3mf', '.zip'}
EXT_PHOTOS = {'.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.gif':'image/gif'}
BRIDGE = None  # Inicializado em main() ou durante testes isolados.
COPILOT_LOCK = threading.Lock()  # Impede requisições simultâneas que poderiam gastar créditos involuntariamente.


def init_database():
    global STUDIO_DIR
    STUDIO_DIR = DATA / 'projetos'
    DATA.mkdir(parents=True,exist_ok=True)
    UPLOADS.mkdir(parents=True, exist_ok=True)
    STUDIO_DIR.mkdir(parents=True,exist_ok=True)
    with SQL_LOCK, sqlite3.connect(DATABASE) as c:
        c.execute('PRAGMA journal_mode=WAL')
        c.execute('''CREATE TABLE IF NOT EXISTS projects (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, author TEXT NOT NULL,
          category TEXT NOT NULL, description TEXT NOT NULL,
          model_name TEXT NOT NULL, model_file TEXT NOT NULL,
          photo_file TEXT, created_at TEXT NOT NULL
        )''')
        c.execute('CREATE INDEX IF NOT EXISTS ix_projects_created ON projects(created_at DESC)')
        c.execute('''CREATE TABLE IF NOT EXISTS studio_documents (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, updated_at TEXT NOT NULL,
            created_at TEXT NOT NULL, bytes INTEGER NOT NULL
        )''')
        c.execute('CREATE INDEX IF NOT EXISTS ix_studio_updated ON studio_documents(updated_at DESC)')


def valid_model(blob: bytes, suffix: str):
    if suffix == '.stl':
        if len(blob) < 84:
            return False
        n = int.from_bytes(blob[80:84], 'little')
        if n and 84 + 50 * n == len(blob):
            return True
        head = blob[:300].strip().lower()
        return head.startswith(b'solid') and (b'facet' in blob[:2000].lower())
    return blob[:4] in (b'PK\x03\x04', b'PK\x05\x06')


def valid_photo(blob: bytes, suffix: str):
    return (
        suffix == '.png' and blob.startswith(b'\x89PNG\r\n\x1a\n')
        or suffix in {'.jpg','.jpeg'} and blob.startswith(b'\xff\xd8\xff')
        or suffix == '.webp' and blob[:4] == b'RIFF' and blob[8:12] == b'WEBP'
        or suffix == '.gif' and blob[:6] in {b'GIF87a', b'GIF89a'}
    )


def clean_text(s: str, n: int) -> str:
    return ''.join(ch for ch in s if ch.isprintable() or ch in '\n\t').strip()[:n]


class Handler(SimpleHTTPRequestHandler):
    server_version = 'ExpressArte-Local/7.3.2'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC), **kwargs)

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        if self.path.split('?',1)[0].endswith(('.html','.js','.css')):
            self.send_header('Cache-Control','no-store')
        super().end_headers()

    def log_message(self, fmt, *args):
        logging.info('%s - %s', self.address_string(), fmt % args)

    def respond_json(self, status, obj):
        payload = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(payload)

    def error_json(self, status, msg):
        self.respond_json(status, {'ok':False, 'error':msg})

    def check_local_origin(self):
        host = self.headers.get('Host','')
        allowed = (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}')
        origin = self.headers.get('Origin', '')
        return host in allowed and (not origin or origin in ('http://' + allowed[0], 'http://' + allowed[1]))

    def read_scene_payload(self):
        if not self.check_local_origin():
            raise PermissionError('Requisição local não autorizada.')
        if not self.headers.get('Content-Type','').lower().startswith('application/json'):
            raise ValueError('Envie JSON.')
        try: size = int(self.headers.get('Content-Length','-1'))
        except ValueError: size = -1
        if size < 1 or size > MAX_SCENE_BODY:
            raise OverflowError('Documento acima do limite de 36 MB ou vazio.')
        payload = json.loads(self.rfile.read(size))
        if not isinstance(payload,dict): raise ValueError('Documento inválido.')
        name = clean_text(str(payload.get('name','')),90)
        doc = payload.get('doc')
        if not name: raise ValueError('Informe o nome do projeto.')
        if not isinstance(doc,dict) or doc.get('format')!='expressarte-scene' or doc.get('version')!=1:
            raise ValueError('Formato de projeto ExpressArte incompatível.')
        coords = doc.get('positions')
        parts = doc.get('parts')
        if not isinstance(coords,str) or len(coords)<48 or not re.fullmatch('[A-Za-z0-9+/=]+',coords):
            raise ValueError('Geometria ausente ou codificação inválida.')
        try: coords_size=len(base64.b64decode(coords,validate=True))
        except Exception: raise ValueError('Geometria Base64 inválida.')
        if coords_size%36 or coords_size>16_000_000: raise ValueError('Geometria inválida ou maior que 16 MB.')
        if not isinstance(parts,list) or not 1<=len(parts)<=1000:
            raise ValueError('O projeto precisa de 1 a 1000 peças.')
        for item in parts:
            if not isinstance(item,dict) or not isinstance(item.get('name'),str) or len(item['name'])>90:
                raise ValueError('Peça inválida.')
        # Only data, never executable code; full semantic validation happens on load in Studio.
        serialized=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode('utf-8')
        if len(serialized)>MAX_SCENE_BODY: raise OverflowError('Documento excedeu 36 MB.')
        return name, serialized

    def write_scene(self, pid=None):
        try:
            name, serialized = self.read_scene_payload()
            stamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds')
            with SQL_LOCK, sqlite3.connect(DATABASE) as conn:
                if pid:
                    old=conn.execute('SELECT created_at FROM studio_documents WHERE id=?',(pid,)).fetchone()
                    if not old:return self.error_json(404,'Projeto não encontrado.')
                    created=old[0]
                else:
                    count=conn.execute('SELECT COUNT(*) FROM studio_documents').fetchone()[0]
                    if count>=MAX_STUDIO_PROJECTS: return self.error_json(409,'Limite de 80 projetos salvos. Faça backup e exclua um projeto antigo.')
                    pid=str(uuid.uuid4());created=stamp
                STUDIO_DIR.mkdir(parents=True,exist_ok=True)
                target=STUDIO_DIR/(pid+'.exarte')
                temp=STUDIO_DIR/(pid+'.tmp')
                temp.write_bytes(serialized)
                temp.replace(target)
                conn.execute('INSERT OR REPLACE INTO studio_documents (id,name,updated_at,created_at,bytes) VALUES (?,?,?,?,?)',
                             (pid,name,stamp,created,len(serialized)))
            self.respond_json(200 if created!=stamp else 201,{'ok':True,'id':pid,'name':name,'updated_at':stamp})
        except PermissionError as exc: self.error_json(403,str(exc))
        except OverflowError as exc: self.error_json(413,str(exc))
        except (ValueError,json.JSONDecodeError) as exc: self.error_json(400,str(exc)[:240])
        except Exception:
            logging.exception('Falha ao salvar projeto privado')
            self.error_json(500,'Não foi possível salvar o projeto.')

    def do_PUT(self):
        m=re.fullmatch(r'/api/studio/projects/([a-f0-9-]{36})',urlsplit(self.path).path)
        if not m:return self.error_json(404,'Rota desconhecida.')
        self.write_scene(m.group(1))

    def do_DELETE(self):
        m=re.fullmatch(r'/api/studio/projects/([a-f0-9-]{36})',urlsplit(self.path).path)
        if not m:return self.error_json(404,'Rota desconhecida.')
        if not self.check_local_origin():return self.error_json(403,'Origem não autorizada.')
        pid=m.group(1)
        with SQL_LOCK,sqlite3.connect(DATABASE) as db:
            exists=db.execute('SELECT id FROM studio_documents WHERE id=?',(pid,)).fetchone()
            if not exists:return self.error_json(404,'Projeto não encontrado.')
            db.execute('DELETE FROM studio_documents WHERE id=?',(pid,))
            (STUDIO_DIR/(pid+'.exarte')).unlink(missing_ok=True)
        self.respond_json(200,{'ok':True,'deleted':pid})

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/studio/projects':
            with SQL_LOCK,sqlite3.connect(DATABASE) as db:
                db.row_factory=sqlite3.Row
                rows=db.execute('SELECT id,name,updated_at,bytes FROM studio_documents ORDER BY updated_at DESC LIMIT 80').fetchall()
            return self.respond_json(200,{'ok':True,'projects':[dict(r) for r in rows]})
        m=re.fullmatch(r'/api/studio/projects/([a-f0-9-]{36})',path)
        if m:
            pid=m.group(1)
            with SQL_LOCK,sqlite3.connect(DATABASE) as db:
                row=db.execute('SELECT name FROM studio_documents WHERE id=?',(pid,)).fetchone()
            if not row:return self.error_json(404,'Projeto não encontrado.')
            file=STUDIO_DIR/(pid+'.exarte')
            if not file.is_file():return self.error_json(404,'O arquivo deste projeto não existe no disco.')
            try: doc=json.loads(file.read_text(encoding='utf-8'))
            except (ValueError,OSError):return self.error_json(500,'Projeto armazenado está danificado.')
            return self.respond_json(200,{'ok':True,'id':pid,'name':row[0],'doc':doc})
        if path == '/api/ai/copilot/status':
            if not self.check_local_origin():
                return self.error_json(403, 'Origem não autorizada.')
            return self.respond_json(200, copilot_bridge.status())
        if path == '/api/ai/ollama/status':
            if not self.check_local_origin():
                return self.error_json(403, 'Origem não autorizada.')
            return self.respond_json(200, ollama_bridge.status())
        if path == '/api/ai/providers':
            if not self.check_local_origin():
                return self.error_json(403, 'Origem não autorizada.')
            return self.respond_json(200, {
                'ok': True,
                'providers': [
                    {'id': 'github-copilot', 'name': 'GitHub Copilot', **copilot_bridge.status()},
                    {'id': 'ollama-local', 'name': 'Ollama Local', **ollama_bridge.status()},
                ],
            })
        if path == '/api/blender/status':
            return self.respond_json(200, blender_status())
        match = re.fullmatch(r'/api/blender/jobs/([a-f0-9-]{36})', path)
        if match:
            if BRIDGE is None:
                return self.error_json(503, 'Servidor Blender Bridge ainda não está inicializado.')
            job = BRIDGE.public(match.group(1))
            return self.respond_json(200, {'ok':True, **job}) if job else self.error_json(404, 'Trabalho Blender desconhecido.')
        match = re.fullmatch(r'/api/blender/jobs/([a-f0-9-]{36})/files/(stl|glb|blend)', path)
        if match:
            if BRIDGE is None:
                return self.error_json(503, 'Servidor Blender Bridge indisponível.')
            result = BRIDGE.download(*match.groups())
            if result is None:
                return self.error_json(404, 'Arquivo ainda não disponível.')
            fpath, mimetype = result
            data = fpath.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', mimetype)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Content-Disposition', f'attachment; filename="{fpath.name}"')
            self.send_header('Cache-Control','no-store')
            self.end_headers()
            self.wfile.write(data)
            return
        if path in ('/api/health', '/api/diagnostico'):
            return self.respond_json(200, {
                'ok': True, 'product': 'Express’Arte Studio', 'version': '7.3.2',
                'storage': 'local sqlite', 'studio_available': (PUBLIC / 'studio.html').is_file(),
                'blender_tab': (PUBLIC / 'assets' / 'blender-bridge-v72.js').is_file(),
                'blender': blender_status() if path == '/api/diagnostico' else None,
                'studio_path': '/studio.html',
                'calculator_path':'/calculadora.html',
                'mesh_doctor_path':'/mesh-doctor.html',
                'studio_projects_available':STUDIO_DIR.is_dir(),
                'copilot_sdk_installed':copilot_bridge.available(),
            })
        if path == '/api/community':
            with SQL_LOCK, sqlite3.connect(DATABASE) as c:
                c.row_factory=sqlite3.Row
                rows=c.execute('SELECT id,name,author,category,description,model_name,photo_file,created_at FROM projects ORDER BY created_at DESC LIMIT ?', (LIMIT,)).fetchall()
            projects=[]
            for row in rows:
                d=dict(row)
                d['model_url']='/api/community/files/'+d['id']+'/model'
                d['photo_url']=('/api/community/files/'+d['id']+'/photo') if d.pop('photo_file') else None
                projects.append(d)
            return self.respond_json(200, {'ok':True,'projects':projects,'limit':LIMIT})
        match = re.fullmatch(r'/api/community/files/([a-f0-9-]{36})/(model|photo)', path)
        if match:
            pid, kind = match.groups()
            try:
                uuid.UUID(pid)
            except ValueError:
                return self.error_json(404,'Projeto desconhecido')
            with SQL_LOCK, sqlite3.connect(DATABASE) as c:
                row=c.execute('SELECT model_file,model_name,photo_file FROM projects WHERE id=?', (pid,)).fetchone()
            if not row:return self.error_json(404,'Projeto não encontrado')
            fname=row[0] if kind=='model' else row[2]
            if not fname or not re.fullmatch(r'[a-f0-9-]{36}\.(?:stl|3mf|zip|png|jpg|jpeg|webp|gif)',fname):
                return self.error_json(404,'Arquivo não encontrado')
            file_path=UPLOADS/fname
            if not file_path.is_file():return self.error_json(404,'Arquivo não encontrado')
            ext=file_path.suffix
            ctype=EXT_PHOTOS.get(ext,'application/octet-stream')
            data=file_path.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type',ctype)
            self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','no-store')
            if kind=='model':
                # Never render uploaded STL/3MF/ZIP as active web content.
                self.send_header('Content-Disposition',f'attachment; filename="projeto-{pid}{ext}"')
            self.end_headers()
            self.wfile.write(data)
            return
        if path.startswith('/api/'):
            return self.error_json(404,'Rota API desconhecida')
        return super().do_GET()

    def copilot_chat(self):
        if not self.check_local_origin():
            return self.error_json(403, 'Origem não autorizada para o Copilot.')
        if not self.headers.get('Content-Type', '').lower().startswith('application/json'):
            return self.error_json(415, 'Envie JSON.')
        try:
            size = int(self.headers.get('Content-Length', '-1'))
        except ValueError:
            size = -1
        if not 2 <= size <= 6500:
            return self.error_json(413, 'Pergunta ou contexto acima do limite de segurança.')
        try:
            self.connection.settimeout(20)
            request = json.loads(self.rfile.read(size))
            question, context, history = copilot_bridge.validate_payload(request)
        except (ValueError, json.JSONDecodeError, TimeoutError, OSError) as exc:
            return self.error_json(400, str(exc)[:180])
        if not copilot_bridge.available():
            return self.error_json(503, 'Instale o SDK com INSTALAR_COPILOT_WINDOWS.bat antes de usar o Copilot.')
        if not COPILOT_LOCK.acquire(blocking=False):
            return self.error_json(429, 'Já existe uma pergunta sendo processada. Aguarde a resposta anterior.')
        try:
            answer = copilot_bridge.run_prompt(question, context, history)
            return self.respond_json(200, {'ok': True, 'provider': 'github-copilot-sdk', 'answer': answer})
        except copilot_bridge.CopilotUnauthorized:
            return self.error_json(401, 'Autentique sua conta com o Copilot CLI. Consulte o guia COPILOT_COMO_CONECTAR.md.')
        except copilot_bridge.CopilotUnavailable as exc:
            return self.error_json(503, str(exc))
        except Exception:
            logging.exception('Erro inesperado na integração Copilot (sem conteúdo da pergunta)')
            return self.error_json(502, 'Falha inesperada no serviço Copilot.')
        finally:
            COPILOT_LOCK.release()

    def ollama_chat(self):
        if not self.check_local_origin():
            return self.error_json(403, 'Origem não autorizada para o assistente local.')
        if not self.headers.get('Content-Type', '').lower().startswith('application/json'):
            return self.error_json(415, 'Envie JSON.')
        try:
            size = int(self.headers.get('Content-Length', '-1'))
        except ValueError:
            size = -1
        if not 2 <= size <= 8000:
            return self.error_json(413, 'Pergunta ou contexto acima do limite de segurança.')
        try:
            self.connection.settimeout(20)
            request = json.loads(self.rfile.read(size))
            question, context, history, model = ollama_bridge.validate_payload(request)
        except (ValueError, json.JSONDecodeError, TimeoutError, OSError) as exc:
            return self.error_json(400, str(exc)[:180])
        if not ollama_bridge.available():
            return self.error_json(503, 'Ollama não está rodando. Instale em https://ollama.com e execute "ollama serve".')
        try:
            answer = ollama_bridge.run_prompt(question, context, history, model)
            return self.respond_json(200, {'ok': True, 'provider': 'ollama-local', 'model': model, 'answer': answer})
        except ollama_bridge.OllamaModelError as exc:
            return self.error_json(404, str(exc))
        except ollama_bridge.OllamaUnavailable as exc:
            return self.error_json(503, str(exc))
        except Exception:
            logging.exception('Erro inesperado na integração Ollama (sem conteúdo da pergunta)')
            return self.error_json(502, 'Falha inesperada no assistente local.')

    def do_POST(self):
        if urlsplit(self.path).path == '/api/ai/copilot/chat':
            return self.copilot_chat()
        if urlsplit(self.path).path == '/api/ai/ollama/chat':
            return self.ollama_chat()
        if urlsplit(self.path).path == '/api/studio/projects':
            return self.write_scene()
        if urlsplit(self.path).path == '/api/blender/medals':
            return self.create_blender_medal()
        if urlsplit(self.path).path != '/api/community':
            return self.error_json(404,'Rota não encontrada')
        origin=self.headers.get('Origin','')
        if origin and origin not in (f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'):
            return self.error_json(403,'Origem não autorizada para gravação local')
        try:
            content_length=int(self.headers.get('Content-Length','-1'))
        except ValueError:
            content_length=-1
        if content_length<1 or content_length>MAX_BODY:
            return self.error_json(413,'Publicação excede o limite permitido')
        ctype=self.headers.get('Content-Type','')
        if not ctype.lower().startswith('multipart/form-data;'):
            return self.error_json(415,'Envie formulário multipart com arquivo')
        try:
            body=self.rfile.read(content_length)
            mime=(f'Content-Type: {ctype}\r\nMIME-Version: 1.0\r\n\r\n').encode()+body
            message=BytesParser(policy=default).parsebytes(mime)
            if not message.is_multipart():
                raise ValueError('Formulário de upload inválido')
            fields={}
            for part in message.iter_parts():
                key=part.get_param('name',header='content-disposition')
                if not key or key not in {'name','author','category','description','model','photo'}:
                    continue
                payload=part.get_payload(decode=True) or b''
                filename=part.get_filename()
                if filename is not None:
                    fields[key]=(filename,payload)
                else:
                    fields[key]=payload.decode('utf-8',errors='replace')
            name=clean_text(fields.get('name',''),90)
            author=clean_text(fields.get('author',''),60) or 'Criador local'
            description=clean_text(fields.get('description',''),1600)
            category=clean_text(fields.get('category',''),50) or 'Outros'
            if not name:
                raise ValueError('Informe o nome do projeto')
            model=fields.get('model')
            if not isinstance(model,tuple):
                raise ValueError('Selecione arquivo STL, 3MF ou ZIP')
            model_name, model_data=model
            model_name=Path(model_name.replace('\\','/').split('/')[-1]).name
            ext=Path(model_name).suffix.lower()
            if ext not in EXT_MODELS or len(model_data)==0 or len(model_data)>MAX_MODEL or not valid_model(model_data,ext):
                raise ValueError('Arquivo do modelo inválido ou maior que 25 MB')
            photo_name=None;photo_data=None;photo_ext=None
            photo=fields.get('photo')
            if isinstance(photo,tuple) and photo[1]:
                pn,pd=photo;pe=Path(pn).suffix.lower()
                if pe not in EXT_PHOTOS or len(pd)>MAX_IMAGE or not valid_photo(pd,pe):
                    raise ValueError('Capa inválida ou maior que 5 MB')
                photo_name,photo_data,photo_ext=pn,pd,pe
            pid=str(uuid.uuid4())
            model_file=pid+ext
            image_file=pid+photo_ext if photo_data else None
            model_path=UPLOADS/model_file
            model_path.write_bytes(model_data)
            try:
                if image_file:(UPLOADS/image_file).write_bytes(photo_data)
                with SQL_LOCK, sqlite3.connect(DATABASE) as c:
                    c.execute('INSERT INTO projects VALUES (?,?,?,?,?,?,?,?,?)', (
                        pid,name,author,category,description,model_name,model_file,image_file,
                        datetime.now(timezone.utc).isoformat(timespec='seconds')))
            except Exception:
                model_path.unlink(missing_ok=True)
                if image_file:(UPLOADS/image_file).unlink(missing_ok=True)
                raise
            return self.respond_json(201,{'ok':True,'id':pid,'message':'Projeto salvo neste computador'})
        except ValueError as e:
            return self.error_json(400,str(e))
        except Exception:
            logging.exception('Erro interno ao publicar projeto')
            return self.error_json(500,'Não foi possível salvar o projeto no servidor')


    def create_blender_medal(self):
        if BRIDGE is None:
            return self.error_json(503, 'Servidor Blender Bridge não inicializado.')
        origin = self.headers.get('Origin', '')
        authorized = (f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}')
        if origin and origin not in authorized:
            return self.error_json(403, 'Origem não autorizada.')
        host = self.headers.get('Host', '')
        if host not in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'):
            return self.error_json(403, 'Servidor acessível apenas localmente.')
        if not self.headers.get('Content-Type', '').lower().startswith('application/json'):
            return self.error_json(415, 'Envie JSON com parâmetros da medalha.')
        try:
            size = int(self.headers.get('Content-Length','0'))
            if not 1 <= size <= 8192:
                return self.error_json(413, 'Configuração muito grande ou vazia.')
            data = json.loads(self.rfile.read(size).decode('utf-8'))
            job = BRIDGE.submit(data)
            return self.respond_json(202, {'ok': True, **job})
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError) as exc:
            return self.error_json(400, str(exc)[:240])
        except FileNotFoundError as exc:
            return self.error_json(503, str(exc))
        except OverflowError as exc:
            return self.error_json(429, str(exc))
        except Exception:
            logging.exception('Erro ao iniciar job Blender')
            return self.error_json(500, 'Erro interno ao iniciar Blender.')


def main():
    parser=argparse.ArgumentParser(description='Servidor local Express’Arte V7')
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--open', action='store_true', help='Abrir o navegador após iniciar')
    parser.add_argument('--auto-port', action='store_true', help='Usar primeira porta livre entre a escolhida e as 20 seguintes')
    parser.add_argument('--open-studio', action='store_true', help='Abrir a aba Blender Pro diretamente')
    parser.add_argument('--open-forms', action='store_true', help='Abrir biblioteca de formas diretamente')
    args=parser.parse_args()
    if not 1024<=args.port<=65535:
        parser.error('A porta deve estar entre 1024 e 65535')
    init_database()
    global BRIDGE
    BRIDGE = BridgeJobs(DATA)
    logging.basicConfig(level=logging.INFO,format='[%(asctime)s] %(message)s')
    address='127.0.0.1'
    server = None
    errors = []
    for port in (range(args.port, min(65536, args.port + 21)) if args.auto_port else [args.port]):
        try:
            server = ThreadingHTTPServer((address, port), Handler)
            break
        except OSError as exc:
            errors.append(str(exc))
            if not args.auto_port:
                raise SystemExit(f'Porta {port} ocupada ou indisponível: {exc}. Feche servidores Express’Arte antigos ou use --auto-port.')
    if server is None:
        raise SystemExit('Nenhuma porta local disponível. Feche outros servidores Express’Arte. ' + '; '.join(errors[:2]))
    port = server.server_port
    url = f'http://127.0.0.1:{port}'
    start_page = url + ('/studio.html#formas' if args.open_forms else '/studio.html#blender' if args.open_studio else '/')
    (DATA / 'URL_ATUAL.txt').write_text(url + '\n', encoding='utf-8')
    if port != args.port:
        print(f'\nATENÇÃO: A porta {args.port} já estava ocupada (provavelmente por versão antiga).', flush=True)
        print(f'Iniciando Express’Arte V7.3.2 na porta {port} para não abrir a versão errada.', flush=True)
    print(f'\nEXPRESS’ARTE V7.3.2 EM EXECUÇÃO: {url}', flush=True)
    print(f'FORMAS PROFISSIONAIS: {url}/studio.html#formas', flush=True)
    print(f'STUDIO / BLENDER PRO: {url}/studio.html#blender', flush=True)
    print(f'DIAGNÓSTICO: {url}/diagnostico.html', flush=True)
    print('Blender Bridge:', blender_status()['message'], flush=True)
    print('Dados permanentes de projetos/comunidade:', DATA, flush=True)
    print('Pressione Ctrl+C para encerrar. Não publique este servidor na internet.\n', flush=True)
    if args.open:
        threading.Timer(0.5, lambda: webbrowser.open(start_page)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServidor encerrado.')
    finally:
        server.server_close()


if __name__=='__main__':main()
