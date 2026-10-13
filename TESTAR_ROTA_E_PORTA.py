from pathlib import Path
import json, socket, subprocess, time, urllib.request, urllib.error, os, sys
BASE=Path(__file__).parent
port=26785
occupied=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
occupied.bind(('127.0.0.1',port));occupied.listen(1)
p=subprocess.Popen([sys.executable,'-u',str(BASE/'server.py'),'--port',str(port),'--auto-port'],cwd=BASE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
try:
    url=f'http://127.0.0.1:{port+1}'
    result=None
    for _ in range(40):
        try:
            with urllib.request.urlopen(url+'/api/diagnostico',timeout=1) as r:
                result=json.load(r)
            break
        except Exception:
            time.sleep(.15)
    if not result:
        raise AssertionError('Servidor não iniciou na porta alternativa; output='+repr(p.poll()))
    assert result['version']=='7.3.0',result
    assert result['studio_available'] and result['blender_tab'],result
    with urllib.request.urlopen(url+'/studio.html',timeout=4) as r:
        html=r.read().decode('utf-8')
    assert 'pane-blender' in html and "location.hash === '#blender'" in html
    with urllib.request.urlopen(url+'/diagnostico.html',timeout=4) as r:
        di=r.read().decode('utf-8')
    assert '/api/diagnostico' in di
    with urllib.request.urlopen(url+'/api/health',timeout=4) as r:
        health=json.load(r)
    assert health['version']=='7.3.0'
    with urllib.request.urlopen(url+'/calculadora.html',timeout=4) as r:
        assert r.status==200
    with urllib.request.urlopen(url+'/comunidade.html',timeout=4) as r:
        assert r.status==200
    with urllib.request.urlopen(url+'/catalogo.html',timeout=4) as r:
        assert r.status==200
    result={'ok':True,'version':result['version'],'studio':True,'diagnostico':True,'port_conflict_resolved':True,'redirect_port':port+1,'catalogo':True,'comunidade':True,'calculadora':True,'blender_available':result['blender']['available']}
    print(json.dumps(result,ensure_ascii=False,indent=2))
finally:
    p.terminate()
    try:p.wait(timeout=3)
    except subprocess.TimeoutExpired:p.kill()
    occupied.close()
