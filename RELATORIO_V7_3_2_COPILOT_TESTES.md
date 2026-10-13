# Express’Arte V7.3.2 — GitHub Copilot SDK oficial

## Escopo entregue

A partir da V7.3.1, sem remover Studio, catálogo, comunidade, calculadora, Blender Bridge, 30 formas ou projetos persistentes, implementamos uma segunda opção no painel **IA Express’Arte**: `GitHub Copilot · SDK oficial`.

Componentes novos:
- `copilot_bridge.py`: cliente oficial `github-copilot-sdk`, modo sem ferramentas e validação das mensagens
- `server.py`: rotas `GET /api/ai/copilot/status` e `POST /api/ai/copilot/chat`
- `site/studio.html`: pergunta, resposta, informação de conexão e opt-in para compartilhar resumo da cena
- `site/copilot.html`: instruções de ativação no próprio site
- `INSTALAR_COPILOT_WINDOWS.bat`: instalação do pacote SDK Python e download do runtime
- `COPILOT_COMO_CONECTAR.md`: passos de login oficiais e limitações
- Testes novos em `TESTES_V7_3_2/`

## Arquitetura e privacidade

Fluxo: clique explícito no Studio → POST local `127.0.0.1` → SDK Python no servidor → GitHub Copilot remoto → texto ao Studio. O servidor não encaminha geometria completa, imagens, STL, tokens ou senhas. A opção **Compartilhar resumo da cena** começa desmarcada; quando marcada, envia apenas o diagnóstico textual e medidas (máximo de 2.500 caracteres). Últimas mensagens da conversa podem ser incluídas para contexto, com tamanho limitado. O navegador apenas chama o servidor local, sem guardar token.

- `CopilotClient(mode='empty')`, `available_tools=[]`, `enable_session_store=False` e mensagem de sistema em modo `append` (preserva proteções do SDK).
- Não há ferramentas do agente para shell, leitura de arquivos, escrita, rede auxiliar ou alterações de geometria.
- Limites: pergunta 1.600 caracteres, contexto 2.500, histórico 4 mensagens, corpo HTTP 6.500 bytes, uma pergunta por vez.
- Proteção de origem/Host local; não permite POST de páginas externas em navegadores normais.
- Respostas renderizadas com `textContent`, sem executar HTML retornado pelo modelo.
- Dados do Studio no Windows continuam em `%LOCALAPPDATA%\ExpressArteStudio\dados`.
- Nenhuma chamada ao serviço GitHub é feita ao apenas selecionar Copilot ou abrir a página; as chamadas são explícitas.

## Testes executados nesta rodada

| Teste | Resultado |
|---|---|
| Backend Copilot + servidor local + bloqueio de origem/limites | 9 verificações aprovadas |
| Mock do SDK Python validando `mode='empty'`, sem ferramentas, modelo/resposta | 1 verificação aprovada |
| Interface desktop 1440px / mobile 390px em Chromium | 2 resoluções aprovadas, sem JS errors ou rolagem horizontal |
| Envio apenas após clicar em Perguntar; contexto ausente quando opt-in desmarcado | Aprovado no Chromium simulado |
| Contexto aparece somente quando checkbox é marcado | Aprovado no Chromium simulado |
| Comunidade `test_server_v7.py` | 9/9 aprovados |
| Mesh Doctor regressão `mesh_doctor.test.cjs` | 12/12 aprovados |
| Malhas core `mesh_core.test.cjs` | 6/6 aprovados |
| JavaScript `node --check`: Studio, página Copilot, barra de navegação | Aprovado |
| Rotas HTTP básicas: Studio, catálogo, comunidade, calculadora, Mesh Doctor, Copilot | HTTP 200 |

**Limitação crítica de teste:** o SDK/autenticação do GitHub Copilot NÃO foram executados com uma conta real aqui. A comunicação foi testada no limite com um simulador do SDK. O primeiro teste real exige Python 3.11+, instalar `github-copilot-sdk` e runtime, fazer login no Copilot CLI oficial e possuir acesso ao GitHub Copilot. Não foram consumidos créditos nem efetuadas requisições pagas nesta rodada.

## O que NÃO foi implementado

- Copilot não altera malhas STL/GLB/3MF/BLEND ou arquivos locais. Não há ferramentas do SDK que possam executar comandos da IA.
- Não existe geração de figuras 360° por foto; é outro motor e serviço.
- Não há login OAuth GitHub embutido no navegador; o usuário deve autenticar pelo GitHub Copilot CLI oficial.
- Não foram avaliadas cotas específicas da conta, que dependem do plano GitHub.
- A comunicação depende de internet; assistência local por regras permanece offline.

## Fontes oficiais consultadas

- https://docs.github.com/en/copilot/how-tos/copilot-sdk
- https://docs.github.com/en/copilot/how-tos/copilot-sdk/setup/bundled-cli
- https://docs.github.com/en/copilot/how-tos/copilot-sdk/auth/authenticate
- https://github.com/github/copilot-sdk/blob/main/python/README.md

## Como validar no Windows

1. Extraia tudo, inicie Express’Arte pelo BAT; confirme V7.3.2 no servidor (porta de preferência 8774).
2. Execute `INSTALAR_COPILOT_WINDOWS.bat` com internet; se falhar, consulte `COPILOT_COMO_CONECTAR.md`.
3. Autentique GitHub Copilot CLI usando sua própria conta, sem fornecer senha/token à Express’Arte.
4. Volte ao Studio, painel direito IA Express’Arte, escolha Copilot.
5. Clique Verificar conexão, digite uma pergunta e clique Perguntar ao GitHub Copilot.
6. Se funcionar, faça novo teste com checkbox Compartilhar resumo da cena e confira que a resposta usa o contexto.
7. Confirme que os projetos originais, catálogo, calculadora e comunidade continuam acessíveis.
