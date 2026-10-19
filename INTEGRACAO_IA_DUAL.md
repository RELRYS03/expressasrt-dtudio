# Integração de IA Dual — Express'Arte Studio V7.4

## Visão Geral

O Express'Arte Studio agora suporta **dois provedores de IA** integrados ao servidor local:

| Provedor | ID | Requer Chave? | Processamento | Melhor Para |
|---|---|---|---|---|
| **GitHub Copilot** | `github-copilot` | Sim (login CLI) | Nuvem (GitHub) | Sugestões de código, orientação técnica |
| **Ollama Local** | `ollama-local` | Não | 100% local | Privacidade total, uso offline, modelos customizados |

Ambos os provedores compartilham a mesma interface de chat e respeitam as mesmas regras de segurança: nenhum deles executa comandos, edita malhas ou acessa arquivos sem consentimento explícito.

---

## Endpoints da API

### Listar provedores disponíveis
```
GET /api/ai/providers
```
Retorna status de ambos os provedores em uma única chamada.

### Status do GitHub Copilot
```
GET /api/ai/copilot/status
```

### Status do Ollama Local
```
GET /api/ai/ollama/status
```

### Chat com GitHub Copilot
```
POST /api/ai/copilot/chat
Content-Type: application/json

{
  "message": "Como otimizar esta malha para impressão FDM?",
  "context": "Malha com 12k vértices, 2 buracos não-manifold",
  "history": [
    {"role": "user", "text": "Preciso reduzir polígonos"},
    {"role": "assistant", "text": "Use Decimate modifier..."}
  ]
}
```

### Chat com Ollama Local
```
POST /api/ai/ollama/chat
Content-Type: application/json

{
  "message": "Qual a melhor orientação de suporte para esta peça?",
  "context": "Peça com overhangs de 65°, PLA",
  "model": "llama3.2",
  "history": []
}
```

---

## Configuração do Ollama

### Instalação
1. Baixe o Ollama em https://ollama.com
2. Instale e execute `ollama serve` (ou inicie o serviço)
3. Baixe um modelo: `ollama pull llama3.2`

### Modelos recomendados
- `llama3.2` — leve, bom para perguntas rápidas (padrão)
- `llama3.1:8b` — mais capaz, requer ~8GB RAM
- `qwen2.5:7b` — excelente em português
- `mistral:7b` — bom equilíbrio velocidade/qualidade

### Variáveis de ambiente opcionais
- `EXPRESSARTE_COPILOT_MODEL` — modelo do Copilot (padrão: `auto`)

---

## Segurança e Privacidade

- Todas as rotas de IA exigem origem local (`check_local_origin()`)
- Ollama processa tudo localmente — **nenhum dado sai do computador**
- Copilot envia apenas pergunta + contexto opcional (nunca malhas brutas)
- Nenhum token, senha ou chave deve ser hardcoded no código
- Tokens `gcli_` devem ser gerenciados exclusivamente via `gh auth login`

---

## Arquivos modificados/adicionados na V7.4

| Arquivo | Descrição |
|---|---|
| `ollama_bridge.py` | **NOVO** — Bridge para Ollama local com validação, system prompt e tratamento de erros |
| `server.py` | Adicionado import, rotas GET `/api/ai/ollama/status`, `/api/ai/providers` e POST `/api/ai/ollama/chat` |
| `INTEGRACAO_IA_DUAL.md` | **NOVO** — Esta documentação |