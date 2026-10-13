# V7.3 — Auditoria, correções e evidências de teste

## Escopo implementado

1. Restaurado o acesso à calculadora com rota local `/calculadora.html`, destaque no site e acesso na própria oficina. Rota testada com HTTP 200.
2. Mesh Doctor `/mesh-doctor.html`: núcleo offline autônomo preservado; diagnóstico de até 300 mil faces e orientação explícita sobre limite de reparo em 140 mil. O arquivo real de 253.440 triângulos foi carregado e diagnosticado.
3. API SQLite para **projetos privados do Studio**: criação, listagem, reabertura, atualização e exclusão. Separada das publicações comunitárias; não envia arquivos para a internet. Documentos `.exarte` armazenados em `dados/projetos`.
4. **Armazenamento permanente Windows:** `%LOCALAPPDATA%\ExpressArteStudio\dados`, que não depende do nome da pasta extraída. Migração opt-in não sobrescreve destino com dados existentes.
5. Salvamento manual e automático no Studio, acesso pelo botão **Meus projetos**, reabertura do último projeto, tentativa de salvamento antes de navegar para outras páginas; backup manual `.exarte` mantido.
6. Biblioteca de **20 formas** com malhas fechadas, incluindo formas côncavas trianguladas; objetos são editáveis como partes individuais.
7. **Imagem → camadas 3D por cores**: separação determinística local em 2–4 grupos, criação de base e peças independentes por cor. Arte RGB, não segmentação semântica por IA.
8. Exportação **3MF** simplificada ZIP/Core com corpos e cores separadas, além de STL e GLB existentes.

## Testes executados

- `test_server_v7.py`: **9 de 9** verificações do mural da comunidade aprovadas.
- `test_v73_server_projects.py`: criação, listagem, leitura, atualização, reinício do servidor, exclusão e controles de origem/formato recusados quando inválidos; rotas do Studio, Calculadora, Comunidade e Mesh Doctor retornaram HTTP 200.
- `test_v73_browser_saved.py`: criação de coração + estrela, salvamento automático com simulação de respostas da API, alteração de posição X para 10 mm, salvamento novamente, abertura do documento e recuperação da edição; **zero erros de página** nos fluxos testados. Layout 390 px **sem rolagem horizontal**.
- `test_v73_browser.py`: biblioteca de formas, serialização/reabertura de `.exarte`, exportações `.3mf`, conversão da foto fornecida em base e três camadas editáveis, exemplo do Mesh Doctor; **zero erros JavaScript**.
- `test_v73_large_doctor.py`: arquivo `ornaments(1).stl` de **253.440 triângulos** diagnosticado, com 0 arestas abertas e 0 não-manifold, em ~1,4–1,7 segundo na execução de teste. Reparo da malha inteira intencionalmente bloqueado pelo limite de segurança.
- `mesh_core.test.cjs` e `mesh_doctor.test.cjs` do histórico: **18/18** aprovações.
- Trimesh (análise independente) nos arquivos 3MF produzidos: **2 objetos fechados** (coração e estrela); **4 objetos fechados** (base + três regiões de cor), com orientação consistente.
- Sintaxe JS principal e do Mesh Doctor `node --check`: aprovada.
- Links locais das páginas principais: sem destinos ausentes.

## Limitações e garantias que NÃO foram testadas

- O navegador automatizado usa a alternativa de Canvas porque a GPU WebGL não está disponível neste ambiente; renderização WebGL em sua máquina ainda exige validação.
- Não foi possível abrir diretamente o `127.0.0.1:8765` do computador do usuário. Os testes HTTP foram realizados no servidor local da cópia, com portas temporárias.
- A API do Studio foi testada via HTTP real; a interface foi exercitada em Chromium com simulação da resposta da API porque a navegação local do navegador do laboratório é bloqueada pela política de ambiente.
- O separador de cores é aproximado: pode criar pequenas ilhas; verifique continuidade, peças soltas e resistência antes de imprimir.
- O exportador 3MF permite cores por objetos no arquivo, mas **não configura automaticamente AMS ou filamentos no Bambu Studio**, nem substitui fatiamento ou análise de colisões/booleans.
- Salvar a cena preserva geometria e objetos editáveis, mas não mantém todas as ações históricas de edição raster nem foto original como camada autônoma.
- A auto-gravação depende do servidor ativo e da operação HTTP concluir; feche/alterne após o aviso de projeto salvo, e faça backup `.exarte` de trabalhos importantes.
- Chaveiros compostos por formas sobrepostas não são automaticamente unidos em uma única malha booleana.
- GitHub Copilot e IA foto→escultura neural ainda não foram conectados.

**Nenhum recurso experimental é tratado como prova de impressão física ou de execução no Blender Windows.**
