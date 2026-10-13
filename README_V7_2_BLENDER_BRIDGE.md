# Express’Arte V7.2 — Blender Bridge (Windows)

## O que mudou

Esta é uma **integração local inicial com o Blender**, que você já possui instalado. O Studio, catálogo, comunidade, calculadora e Mesh Doctor continuam no mesmo servidor. A nova aba **Blender Pro** cria medalhas com base, borda, argola e letras em alto-relevo em um processo do Blender executado no computador. O processo é isolado por tarefa.

**Três exportações previstas:**

- `.blend`: cena editável com partes e materiais separados;
- `.glb`: modelo com materiais, próprio para visualização e GameDev;
- `.stl`: tentativa de união booleana em um único volume, sem cores. A geração bloqueia se encontrar arestas não manifold no objeto de impressão.

A integração gera um **modelo paramétrico de medalha**. Ainda **não** importa SVG colorido por regiões, não cria figuras 360° a partir de fotos, nem faz pintura multicolorida automática 3MF. Não há IA generativa externa ligada a esta função.

## Instalar e iniciar

1. Extraia **todo** o ZIP em uma pasta do Windows. Não abra arquivos diretamente dentro do ZIP.
2. Feche o servidor de uma versão anterior, caso esteja aberto.
3. Execute `INICIAR_EXPRESSARTE_WINDOWS.bat` (requer Python 3).
4. Abra `http://127.0.0.1:8765` → **Studio 3D** → **Blender Pro**.
5. Caso apareça **Blender não encontrado**, feche o servidor, execute `CONFIGURAR_BLENDER_WINDOWS.bat`, informe o caminho completo do `blender.exe` e reinicie o servidor.
6. Ajuste o formato, diâmetro, cores e texto da medalha; clique em **Gerar medalha no Blender**. Aguarde aparecerem os três downloads.
7. Clique em **Importar STL gerado para este Studio**, se quiser visualizá-lo e editar medidas aqui. Salve antes qualquer projeto existente, pois importar STL **substitui a cena atual**.

A criação do arquivo ocorre em `dados/blender_jobs/ID-DA-TAREFA/`. Os dados nunca são enviados a provedores externos.

## Atualização sem perder comunidade

- Nunca apague a pasta `dados/` de uma instalação que contém publicações.
- Para migrar publicações, **feche os servidores** e execute `MIGRAR_COMUNIDADE_WINDOWS.bat` na nova versão. Informe o caminho da pasta antiga. O procedimento recusa substituir um banco que já contém publicações e cria backup do banco anterior vazio.
- A calculadora e algumas páginas históricas podem manter dados no armazenamento **local do navegador**, associado à origem `http://127.0.0.1:8765`; continue usando o mesmo endereço e perfil do navegador para preservar esses dados.

## Testes e limitações

**Executados aqui:** validações de parâmetros, API HTTP ponta a ponta com simulador de Blender, rejeição de origens externas, rejeição de arquivos incompletos, testes de comunidade 9/9, sintaxe JavaScript e Python, navegação básica da nova aba usando Chromium com API simulada.

**Não executados aqui:** o Blender real não está instalado no ambiente do assistente. A construção de geometria por `bpy`, a união booleana, a exportação real `.blend/.glb/.stl` e compatibilidade exata com a versão do Blender do seu PC **precisam do primeiro teste em Windows**. O script foi entregue com saída de erro explícita e log local para diagnóstico, sem prometer resultados não verificados.

O pacote mantém os scripts originais, a marca, comunidade, calculadora e backups existentes. A integração não usa `shell=True` nem aceita executar código Python arbitrário enviado pelo navegador.

Se o Blender apresentar erro, abra `dados/blender_jobs/<id>/exec.log` e envie o trecho final da mensagem para diagnóstico. Não envie senhas ou arquivos pessoais.
