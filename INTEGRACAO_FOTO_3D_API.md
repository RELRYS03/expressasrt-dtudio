# Express’Arte — Integração segura Foto → Escultura 3D por API

## Situação nesta versão
**Planejado, não conectado.** A V7.1.1 continua processando as imagens **localmente** e gera modelos 2,5D. Este documento especifica a próxima integração de serviço generativo externo, sem criar cobranças nem enviar fotografias automaticamente.

## Validação da proposta
A sequência **POST de tarefa → ID → acompanhamento via GET/SSE → links de saída → importação e diagnóstico** existe em serviços reais. A documentação oficial do Meshy contém `POST /openapi/v1/image-to-3d`, `GET /openapi/v1/image-to-3d/:id`, streaming SSE e retornos GLB/STL/OBJ/3MF quando solicitados.

Fonte oficial: https://docs.meshy.ai/en/api/image-to-3d e https://docs.meshy.ai/en/api/quick-start

Importante: **não suponha que um campo arbitrário `prompt` seja aceito por qualquer API imagem-para-3D.** Na documentação atual do Meshy, `texture_prompt` orienta **a texturização**, não necessariamente a geometria ou estilização da malha. Para transformar fotos em personagens estilizados, talvez seja preciso usar **etapa de imagem-para-imagem** antes de enviar a imagem para geração 3D, ou usar um provedor/modelo que aceite essas instruções.

## Pipeline proposto (com confirmação explícita do usuário)
1. **Entrada e prévia local:** PNG/JPG/WebP, tamanho máximo, confirmação de direitos sobre a fotografia.
2. **Preparação 2D:** remover fundo, separar pessoas quando houver duas ou mais; opção de estilização prévia com consentimento. Preservar uma cópia original.
3. **Escolher o serviço e custo:** mostrar provedor, limites, custo estimado e aviso de que a foto sairá do computador. Nunca gerar enquanto o usuário não confirmar.
4. **Serviço local faz POST:** guarda chave de API somente em variável de ambiente no servidor local (nunca no HTML ou `.exarte`). A imagem é enviada por HTTPS em data URI Base64 ou URL pública autorizada.
5. **Status assíncrono:** guardar `task_id` e aguardar por `GET` ou SSE; respeitar cabeçalho `Retry-After`, tratar `FAILED` / `CANCELED` / `SUCCEEDED`. **Não criar outra tarefa automaticamente depois de timeout** para não duplicar cobrança.
6. **Importação de arquivos:** baixar GLB para visualização/texturas, STL/3MF quando solicitados e suportados. Verificar domínios, extensão, tamanho e formato do retorno. URLs assinadas podem expirar.
7. **Mesh Doctor antes da impressão:** analisar malha fechada, orientação, dimensão, paredes, ilhas, espessura e componentes. Reparo opcional, antes/depois e desfazer.
8. **Preparação de peças:** separar base, corpo, cabeça e acessórios; configurar tolerâncias e imprimir um encaixe de teste antes do produto final.

### Solicitação ilustrativa para um serviço Meshy

```http
POST https://api.meshy.ai/openapi/v1/image-to-3d
Authorization: Bearer <TOKEN_NO_SERVIDOR>
Content-Type: application/json

{
  "image_url": "data:image/png;base64,<IMAGEM_DO_USUARIO_CONSENTIDA>",
  "target_formats": ["glb", "stl", "3mf"],
  "should_texture": true
}
```

**Somente exemplo documental, não executado nem testado contra uma conta real.** Confirmar sempre a versão atual da API, os campos, limites e consumo de créditos. A documentação do Meshy exige solicitar `3mf` explicitamente em `target_formats` para que essa saída apareça.

## Atenções sobre formatos
- **GLB:** ótimo para prévia 360°, cenas e materiais; malha pode não ser fechada/imprimível.
- **STL:** geometria apenas, sem cores, unidades não declaradas pelo formato; validar dimensões.
- **3MF:** suporta metadados e materiais/cores via especificação/extensões. Não é garantia automática de solidez/manifold, correspondência dos filamentos AMS nem impressibilidade. A validação do modelo e o fatiamento continuam obrigatórios.

Especificação: https://3mf.io/spec/

## Segurança e custo — requisitos inegociáveis
- Chave somente no servidor local e fora do ZIP; nenhuma senha de terceiros embutida nos arquivos do site.
- Consentimento por tarefa para upload de imagens e eventual cobrança de créditos.
- Limite de requisições, tempo máximo de espera e cancelamento seguro; exibir status e erro sem criar tarefas duplicadas.
- Validação estrita das URLs retornadas e das mídias; não aceitar URLs externas arbitrárias enviadas pelo navegador para que o servidor as busque.
- Política de privacidade e retenção do provedor: fotografias poderão sair do PC quando o modo externo for ativado.
- Testes com provedor simulado (gratuitos) antes de qualquer teste pago.
- Gerador deve tratar múltiplas pessoas, inclusive duas na mesma imagem, com fluxo apropriado em vez de presumir reconstrução individual perfeita.

## Recomendação de implementação posterior
Separar um adaptador Python `ProviderImage3D` com métodos `create_task`, `get_status`, `download_model`, `validate_output`, e manter a interface do Studio com estados `configuração necessária`, `confirmar custo`, `enviando`, `processando`, `concluído`, `falhou`. Só habilitar botão de criação externa depois de autenticação e testes completos.
