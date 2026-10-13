"""Assistente offline para conectar Blender instalado no Windows à Express'Arte."""
from pathlib import Path
import subprocess
from blender_bridge import find_blender, blender_status, ROOT

def main():
    detected = blender_status()
    if detected['available']:
        print('Blender encontrado:', detected['version'])
        print('Executável:', detected.get('path'))
        print('A integração já está configurada.')
        return
    print('O Blender não foi encontrado automaticamente.')
    print('Exemplo de caminho: C:\\Program Files\\Blender Foundation\\Blender 4.5\\blender.exe')
    raw = input('Cole o caminho completo do blender.exe: ').strip().strip('"')
    path = Path(raw)
    if not path.is_file() or path.name.lower() not in ('blender.exe', 'blender'):
        print('Caminho inválido. O arquivo precisa ser o executável oficial blender.exe.')
        return
    try:
        result = subprocess.run([str(path),'--version'],capture_output=True,text=True,timeout=12)
        if result.returncode or 'Blender' not in result.stdout[:200]:
            print('O executável indicado não respondeu como Blender.')
            return
    except (OSError, subprocess.TimeoutExpired) as exc:
        print('Falha ao iniciar o Blender:', exc)
        return
    config = ROOT/'dados'/'blender_path.txt'
    config.parent.mkdir(exist_ok=True)
    config.write_text(str(path),encoding='utf-8')
    print('Blender conectado:',result.stdout.splitlines()[0])
    print('Configuração local salva em dados\\blender_path.txt')
    print('Reinicie o servidor Express’Arte para atualizar.')
if __name__=='__main__':main()
