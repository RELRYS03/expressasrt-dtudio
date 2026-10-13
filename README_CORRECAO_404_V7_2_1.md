# Express’Arte Studio V7.2.1 — correção do erro 404 no Windows

Esta atualização corrige a **inicialização**, o acesso ao Studio e o diagnóstico da ponte Blender. **Não altera as ferramentas geométricas da V7.2** e **não prova ainda a execução do Blender real no computador do usuário**.

## Por que a tela 404 apareceu?

A versão V7.2 contém `site/studio.html`. O launcher antigo tentava usar sempre a porta 8765. Se outra versão da Express’Arte (ou outro serviço) já estivesse executando ali, o novo servidor não conseguia iniciar. O navegador podia então acessar o servidor antigo, que não reconhecia `/studio.html`, resultando em 404.

É a **causa mais provável**, mas a captura não mostra o endereço completo nem o processo em execução; se persistir, precisamos da URL completa e da janela do servidor.

## Como iniciar agora

1. Extraia o ZIP completo, sem executar BAT ou HTML diretamente dentro do arquivo compactado.
2. Abra `ExpressArte_Studio_V7_2_1_CORRECAO_404_WINDOWS/`.
3. Dê dois cliques em `INICIAR_EXPRESSARTE_WINDOWS.bat`.
4. A janela verificará os arquivos principais e iniciará na porta 8765 ou na próxima livre (8766, 8767...).
5. O Chrome abrirá o Studio diretamente na aba **Blender Pro**.
6. Guarde a porta mostrada na janela; ela é o endereço correto da sua instalação, e pode ser diferente de 8765.
7. Para reabrir sem lembrar a porta, execute `ABRIR_STUDIO_BLENDER_WINDOWS.bat` enquanto o servidor estiver funcionando.
8. Abra `http://127.0.0.1:PORTA/diagnostico.html` substituindo PORTA pela porta mostrada no console. A página identifica versão 7.2.1 e se o Blender está disponível.

Se o Blender não aparecer, execute `CONFIGURAR_BLENDER_WINDOWS.bat` e informe o caminho de `blender.exe`; depois reinicie o servidor.

## O que mudou

- Server `--auto-port`: evita conflito com serviços que já usam a porta 8765.
- Server `--open-studio`: abre `/studio.html#blender`, em vez de exigir que o usuário encontre manualmente o caminho.
- Studio reconhece `#blender` e abre a aba Blender Pro.
- Rotas `/api/health` e `/api/diagnostico` informam versão **7.2.1**.
- Página `site/diagnostico.html` mostra informações do servidor e da instalação local do Blender.
- Windows BAT valida presença de `server.py` e `site/studio.html` antes de executar.
- Novo `ABRIR_STUDIO_BLENDER_WINDOWS.bat` usa a URL da última inicialização.
- Mantidos: Studio, site, catálogo, comunidade e calculadora, Blender Bridge e históricos.

## Testes realizados neste ambiente

- Python `py_compile` e validação sintática de JavaScript: aprovados.
- Teste HTTP de rota: `/studio.html`, `/diagnostico.html`, `/api/diagnostico`, `/api/health`: aprovados.
- Teste de conflito de porta: bloqueada deliberadamente a porta solicitada, servidor V7.2.1 abriu automaticamente a seguinte: **aprovado**.
- Páginas catálogo, comunidade e calculadora acessíveis: **aprovado**.
- Regressão do servidor de comunidade: **9/9** testes aprovados.
- Regressão da ponte Blender com executável **simulado**: **2/2** testes aprovados.
- Teste da ferramenta de migração SQLite: aprovado.

## Limitações honestas

Não executamos o Blender real no PC do usuário; a primeira geração de medalha dependerá de confirmação no Windows. O servidor continua apenas em localhost; outras pessoas não acessam sua comunidade pela internet. A imagem para escultura neural 360° e exportação 3MF colorida ainda não estão implementadas.

**Nunca apague a pasta `dados/` de uma instalação anterior se houver publicações da comunidade.** Utilize a migração existente e mantenha um backup do banco. O novo ZIP não substitui os arquivos do sistema anterior automaticamente.
