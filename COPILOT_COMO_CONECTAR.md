# Express’Arte V7.3.2 — GitHub Copilot (opcional)

## O que esta integração faz

Permite conversar **de verdade** com o GitHub Copilot pelo SDK Python oficial do GitHub, a partir do painel **IA Express’Arte** do Studio. Você pode perguntar sobre materiais, medidas, reparo e como personalizar objetos. **Não** permite modificar a malha automaticamente. A IA local por regras permanece funcionando sem internet.

## 1. Instale o SDK no mesmo Python do servidor

- Extraia todo o ZIP da Express’Arte.
- Execute `INSTALAR_COPILOT_WINDOWS.bat` na pasta principal.
- Requer **Python 3.11 ou superior**, internet e acesso ao GitHub/PyPI.
- O script faz `python -m pip install --upgrade github-copilot-sdk` e `python -m copilot download-runtime` usando o mesmo Python escolhido pelo iniciador.
- O SDK não vem instalado nem autenticado dentro do ZIP.

A instalação é opcional; o resto do aplicativo continua funcionando normalmente.

## 2. Faça login **pela ferramenta oficial GitHub**

O SDK utiliza as credenciais GitHub Copilot CLI já autorizadas no computador. Faça autenticação interativa pelo **Copilot CLI oficial** seguindo a documentação:

- [Instalar e autenticar Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/authenticate-copilot-cli)
- [Autenticação SDK](https://docs.github.com/en/copilot/how-tos/copilot-sdk/auth/authenticate)

Em um terminal Windows onde `copilot` esteja instalado e no PATH, execute `copilot login` ou abra `copilot` e siga o fluxo de login conforme a versão instalada. O GitHub CLI autenticado (`gh auth login`) pode servir de fallback para o SDK quando sua conta possui acesso ao Copilot. Pode haver regras e cobrança/cotas associadas à sua assinatura GitHub Copilot.

**Nunca** informe sua senha ou token à Express’Arte, nem envie credenciais por mensagem. O login acontece na ferramenta oficial, fora do navegador do Studio. Não incluímos login falso.

## 3. Use no Studio

1. Inicie `INICIAR_EXPRESSARTE_WINDOWS.bat`.
2. Abra `Studio 3D`, painel direito **IA Express’Arte · Assistência guiada**.
3. Selecione `GitHub Copilot · SDK oficial`.
4. Clique em `Verificar conexão Copilot`. Isso verifica se o SDK está instalado, não valida a autenticação.
5. Escreva uma pergunta e clique em `Perguntar ao GitHub Copilot`.
6. A primeira pergunta confirma se a conta está realmente autorizada. Se não estiver, será exibida orientação para login.

**Privacidade:** clicar para enviar a pergunta a envia para os serviços do GitHub. A caixa **Compartilhar resumo da cena** vem desmarcada. Se você marcar, serão enviados somente texto do diagnóstico, nomes, dimensões e dados agregados; arquivos STL, fotos e modelos completos não são enviados. As últimas duas trocas da conversa podem ser incluídas para contextualizar novas perguntas. Nenhuma pergunta é enviada automaticamente ao selecionar Copilot.

## Segurança e limites reais

- O SDK usa `mode="empty"` e `available_tools=[]`: sem ferramentas do agente para executar comandos ou manipular arquivos da máquina.
- A Express’Arte não grava tokens, senhas ou chaves no banco do Studio nem no navegador.
- A rota HTTP só aceita requisições locais e implementa limite de tamanho e uma consulta por vez.
- O Copilot não modifica STL, BLEND, 3MF nem projetos salvos nesta versão.
- A comunicação depende de internet, credenciais da conta e da disponibilidade do GitHub Copilot.
- A conta ChatGPT não é uma assinatura Copilot: são serviços diferentes.
- O assistente local da Express’Arte pode ser usado normalmente sem SDK.

## Solução de problemas

**"SDK não instalado"**: rode `INSTALAR_COPILOT_WINDOWS.bat`; verifique se o Python 3.11+ usado é o mesmo do servidor.

**"Login necessário"**: autentique o Copilot CLI oficial e confirme que sua conta tem acesso.

**"Copilot indisponível"**: confira a conexão com a internet, o runtime instalado e limites/cotas da assinatura. Reinicie o servidor após configurar.

**"Servidor antigo"**: não use a aba 8765/8773 aberta anteriormente. Inicie esta nova pasta e verifique versão **7.3.2**; ela prefere a porta **8774** e escolhe outra se estiver ocupada.

## Referências oficiais

- https://docs.github.com/en/copilot/how-tos/copilot-sdk
- https://github.com/github/copilot-sdk/tree/main/python
- https://docs.github.com/en/copilot/how-tos/copilot-sdk/setup/bundled-cli
