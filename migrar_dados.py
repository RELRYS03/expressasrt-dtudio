"""Importação opt-in: dados de versões antigas para o armazenamento permanente da Express'Arte.
Nunca sobrescreve dados persistidos com publicações ou projetos existentes.
Feche ambos os servidores antes de migrar.
"""
from pathlib import Path
from datetime import datetime
import shutil
import sqlite3
from server import DATA as TARGET

ROOT=Path(__file__).resolve().parent

def count_rows(db: Path, table: str)->int:
    if not db.is_file(): return 0
    try:
        with sqlite3.connect(f'file:{db.as_posix()}?mode=ro',uri=True) as conn:
            return conn.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]
    except sqlite3.Error: return 0

def migrate(previous: Path):
    source=previous.expanduser().resolve()/'dados'
    old=source/'expressarte.sqlite3'
    target=TARGET.resolve()
    if not old.is_file(): raise ValueError('Escolha uma pasta da versão anterior que contenha dados\\expressarte.sqlite3.')
    if source.resolve()==target: raise ValueError('Origem e destino são a mesma pasta.')
    target.mkdir(parents=True,exist_ok=True)
    dest=target/'expressarte.sqlite3'
    old_count=count_rows(old,'projects')
    old_studio=count_rows(old,'studio_documents')
    new_count=count_rows(dest,'projects')
    new_studio=count_rows(dest,'studio_documents')
    if new_count or new_studio:
        raise ValueError(f'O destino já contém {new_count} publicação(ões) e {new_studio} projeto(s) de Studio. Operação recusada para proteger seus dados. Faça backup manual antes de mesclar.')
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
    if dest.exists():
        shutil.copy2(dest,target/f'expressarte.sqlite3.backup-{stamp}')
    # SQLite online backup includes committed WAL data.
    with sqlite3.connect(f'file:{old.as_posix()}?mode=ro',uri=True) as frm:
        with sqlite3.connect(dest) as dst:
            frm.backup(dst)
    copied=0
    for subdir,extensions in [('arquivos',{'.stl','.3mf','.zip','.png','.jpg','.jpeg','.webp','.gif'}),('projetos',{'.exarte'})]:
        src=source/subdir;dst=target/subdir;dst.mkdir(parents=True,exist_ok=True)
        if not src.is_dir(): continue
        for file in src.iterdir():
            if file.is_file() and file.suffix.lower() in extensions and len(file.name)<110 and not (dst/file.name).exists():
                shutil.copy2(file,dst/file.name);copied+=1
    print(f'Migração concluída: {old_count} postagem(ns), {old_studio} projeto(s) e {copied} arquivo(s) copiados.')
    print('Os dados antigos continuam na pasta anterior. Destino:',target)

if __name__=='__main__':
    print('Feche todas as janelas servidor ExpressArte antes de migrar.')
    print('Pasta atual de dados permanentes:',TARGET)
    raw=input('Cole o caminho da pasta PRINCIPAL da versão anterior: ').strip().strip('"')
    try:migrate(Path(raw))
    except (OSError,sqlite3.Error,ValueError) as exc:print('Migração NÃO realizada:',exc)
