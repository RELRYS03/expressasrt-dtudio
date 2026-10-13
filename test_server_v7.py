"""Testes automatizados da API local V7; não alteram a biblioteca de projetos real."""
import importlib.util, json, tempfile, threading, urllib.request, urllib.error, uuid, struct
from pathlib import Path
from http.server import ThreadingHTTPServer
from contextlib import contextmanager
from urllib.parse import urljoin

spec=importlib.util.spec_from_file_location('exserver',Path(__file__).with_name('server.py'))
srv=importlib.util.module_from_spec(spec);spec.loader.exec_module(srv)

def multipart(fields):
    boundary='ExBoundary-'+uuid.uuid4().hex
    body=bytearray()
    for name,val in fields.items():
        body+=f'--{boundary}\r\n'.encode()
        if isinstance(val,tuple):
            filename,data,ctype=val
            body+=f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\nContent-Type: {ctype}\r\n\r\n'.encode()+data+b'\r\n'
        else:body+=f'Content-Disposition: form-data; name="{name}"\r\n\r\n{val}\r\n'.encode('utf-8')
    body+=f'--{boundary}--\r\n'.encode()
    return bytes(body),f'multipart/form-data; boundary={boundary}'


def request(url,body=None,ctype=None,origin=None):
    headers={}
    if ctype:headers['Content-Type']=ctype
    if origin:headers['Origin']=origin
    req=urllib.request.Request(url,data=body,headers=headers,method='POST' if body is not None else 'GET')
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            return r.status,r.read(),dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code,e.read(),dict(e.headers)


def cube_stl():
    # 1 triangle is sufficient for API validation; topology is validated separately by Mesh Doctor.
    header=b'Expressarte test STL'.ljust(80,b' ')
    tri=struct.pack('<12fH',0,0,1,0,0,0,10,0,0,0,10,0,0)
    return header+struct.pack('<I',1)+tri


def run():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        srv.DATA=root/'dados';srv.UPLOADS=srv.DATA/'arquivos';srv.DATABASE=srv.DATA/'test.sqlite3';srv.init_database()
        http=ThreadingHTTPServer(('127.0.0.1',0),srv.Handler)
        port=http.server_port
        thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{port}'
        try:
            code,data,_=request(base+'/api/health')
            assert code==200 and json.loads(data)['ok']
            code,data,_=request(base+'/api/community')
            assert code==200 and json.loads(data)['projects']==[]
            valid=cube_stl()
            body,ctype=multipart({'name':'Meu chaveiro & teste','author':'Ateliê Local','category':'Personalizados','description':'STL de teste','model':('modelo.stl',valid,'model/stl'),'photo':('capa.png',b'\x89PNG\r\n\x1a\n'+b'fake-data','image/png')})
            code,data,_=request(base+'/api/community',body,ctype,origin=base)
            assert code==201, (code,data)
            pid=json.loads(data)['id']
            code,data,_=request(base+'/api/community')
            assert code==200
            projects=json.loads(data)['projects'];assert len(projects)==1
            assert projects[0]['name']=='Meu chaveiro & teste' and projects[0]['id']==pid
            code,model,headers=request(base+projects[0]['model_url'])
            assert code==200 and model==valid and 'attachment' in headers.get('Content-Disposition','')
            code,photo,_=request(base+projects[0]['photo_url'])
            assert code==200 and photo.startswith(b'\x89PNG')
            bad,ctype=multipart({'name':'Falha','model':('ruim.stl',b'falso conteudo','model/stl')})
            code,data,_=request(base+'/api/community',bad,ctype,origin=base)
            assert code==400
            code,data,_=request(base+'/api/community',body,ctype='multipart/form-data; boundary=wrong',origin='https://outro-site.com')
            assert code==403
            code,data,_=request(base+'/api/nao-existe')
            assert code==404
            assert len(list(srv.UPLOADS.iterdir()))==2
            assert srv.DATABASE.is_file()
            print('TESTES SERVIDOR: 9/9 PASSARAM (saúde, lista, postagem, persistência, modelo, foto, entrada inválida, origem externa, rota ausente)')
        finally:http.shutdown();thread.join(timeout=5);http.server_close()
if __name__=='__main__':run()
