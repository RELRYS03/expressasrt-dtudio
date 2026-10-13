"""Verifica versão e abre a biblioteca somente no servidor correto."""
from pathlib import Path
import os, json, urllib.request, webbrowser, sys
root=Path(os.environ.get('LOCALAPPDATA', str(Path(__file__).parent)))/'ExpressArteStudio'/'dados'
address=root/'URL_ATUAL.txt'
if not address.exists():
    print('Inicie INICIAR_EXPRESSARTE_WINDOWS.bat antes de usar este atalho.');sys.exit(1)
url=address.read_text('utf-8').strip()
try:
    with urllib.request.urlopen(url+'/api/health', timeout=5) as response:
        info=json.load(response)
    if info.get('version')!='7.3.1':
        raise RuntimeError('Outra versao do servidor ativa: '+str(info.get('version'))+'. Abra a V7.3.1 pelo BAT.')
except Exception as err:
    print('Nao foi possivel confirmar a versao do Studio:',err);sys.exit(2)
print('Abrindo 30 formas no Studio V7.3.1:',url+'/studio.html#formas')
webbrowser.open(url+'/studio.html#formas')
