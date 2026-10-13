# Express’Arte Studio V7.0 — Auditoria, entregas e testes

**Natureza da versão:** atualização integrada com servidor pessoal, identidade visual única e reforço da visualização 3D. **Não é** uma plataforma pública multiusuário ou um gerador de esculturas 360° por IA.

## O que foi preservado

- Catálogo original de **602 ideias** de impressão e seu painel de produção, datas comemorativas, pesquisa e favoritos.
- Calculadora com **8 marketplaces**, faixas e taxas editáveis, cálculo de preço, lucro, comparações e histórico do navegador/CSV.
- Comunidade original de biblioteca **IndexedDB** (dados locais ao navegador), com visualizador e importação de STL.
- Editor clássico de modelagem Three.js e Mesh Doctor offline; arquivos do backup V6.1.1 preservados inteiros em `historico/`.
- Criação de STL por imagem **2,5D** e separação de componentes no Studio offline.

## O que foi acrescentado na V7

1. **Identidade visual transversal:** cores creme, marrom café, caramelo e dourado, baseada na imagem enviada da marca Express’Arte. A imagem original foi incluída em `site/assets/marca_expressarte.png` sem modificação.
2. **Página inicial profissional**, navegação compartilhada em todas as ferramentas e remoção dos menus duplicados mais visíveis.
3. **Servidor local em Python** (`server.py` e `INICIAR_EXPRESSARTE_WINDOWS.bat`), sem dependências Python externas, restrito a `127.0.0.1` por padrão.
4. **Comunidade com dois modos explícitos:** biblioteca IndexedDB anterior e novo mural **SQLite no PC**. Envia STL/3MF/ZIP até 25 MB e capa raster até 5 MB; lista e baixa publicações locais. O mural não é uma rede social pública e não sincroniza na internet.
5. **Studio com renderizador WebGL sem CDN** para desenhar malhas sólidas completas quando o navegador permitir; fallback Canvas de compatibilidade. Seu arquivo de 15 componentes passa a exibir a primeira peça em foco após a separação, com opção “Mostrar todas”.
6. **Modo de modelagem avançada acessível dentro do Studio**, preservando o editor clássico. A transferência de arquivos entre ambos depende de exportar e reabrir STL — não há sincronização de estado.
7. **Assistente contextual por regras:** alerta sobre muitos triângulos, dimensões fora da mesa A1, número de componentes e fluxo para Mesh Doctor.

## Verificações realmente executadas

| Verificação | Resultado |
|---|---|
| API local: saúde, listagem, upload, persistência SQLite, download STL, capa, inválidos, origem externa, 404 | **9/9 passaram** |
| Regressão da geometria Mesh Doctor anterior | **18/18 passaram** |
| STL de teste `ornamentos_15_pecas_original.stl` | **253.440 triângulos, 15 peças detectadas** |
| Upload da foto real | **Prévia apareceu antes da geração** |
| Geração de STL de silhueta com nome | **39.988 triângulos, 95,38 × 145 × 3,2 mm** |
| Reabertura do STL gerado via Trimesh (`process=True`) | **Malha fechada, orientação consistente, 1 corpo** |
| Navegação catálogo | **602 resultados** |
| Calculadora | **8 marketplaces**, cálculo de margem e de lucro executados |
| Modo avançado (abrir/fechar painel) | **Passou**, sem erro JavaScript na interação |
| Layout 390 px | **Sem transbordamento horizontal** no Studio testado |
| Auditoria de caminhos locais e sintaxe JavaScript | **8 páginas sem referências literais ausentes ou erros de sintaxe** |
| Erros JavaScript nos testes de interface | **0 nos fluxos executados** |

Capturas e dados automáticos em `TESTES/`. Os testes de interface usaram `page.set_content` no Chromium porque este ambiente **bloqueia a navegação do navegador para `file://` e `localhost`**. A API foi exercitada separadamente através de requisições HTTP reais a um servidor local temporário.

### Limitações comprovadas da validação

- O Chromium automatizado deste ambiente **não disponibilizou WebGL**; a prévia Canvas de compatibilidade foi testada visualmente e por interação, mas a execução efetiva do novo renderizador WebGL deve ser verificada no Chrome do usuário.
- O editor clássico V6 importa módulos Three.js por CDN, portanto requer internet. Não foi possível validar todas as ferramentas clássicas de modelagem ponta a ponta nesta execução.
- O mural foi validado por API HTTP em testes isolados; não houve teste final da página da comunidade navegando contra o servidor real no Chrome por causa do bloqueio de navegação acima.
- Não há geração de figuras colecionáveis volumétricas em 360° a partir de uma única fotografia. O Studio produz formas e relevos **2,5D**.
- O assistente atual **não é IA generativa/LLM**: fornece regras e alertas determinísticos baseados nos dados que o editor consegue medir.
- Não foi realizada impressão física. Todo STL ainda deve ser aberto, fatiado e verificado no Bambu Studio ou fatiador equivalente.
- Taxas comerciais e fretes são simulações editáveis; confirmar os valores reais em cada marketplace.
- O armazenamento antigo do navegador (`file://`) não migra automaticamente para o novo endereço HTTP local.

## Melhorias de prioridade seguinte

1. Executar teste real de WebGL e do editor clássico no Chrome do Windows com internet, cobrindo booleans, STL, texto e seleção por clique.
2. Migrar ferramentas do editor clássico para um núcleo de cena compartilhado com o Studio, eliminando a exportação/reimportação manual entre modos.
3. Integrar diagnósticos topológicos do Mesh Doctor diretamente na seleção do Studio, com proposta/confirmacão de reparos.
4. Consolidar o histórico local da calculadora e os dados do catálogo em backups exportáveis pelo servidor, com migração consentida.
5. Integrar geração volumétrica foto→3D real somente após definir serviço de GPU, licenças, privacidade de fotos e testes da malha para impressão.

## Regras para próximas entregas

- Um único ZIP completo e um arquivo `INICIAR_EXPRESSARTE_WINDOWS.bat`.
- Preservar `dados/` e todas as funcionalidades dos quatro pilares antes de modificar a interface.
- Não chamar de implementado o que é só interface, protótipo ou roadmap.
- Antes de publicar novas versões, repetir os testes de API, STL, navegação, cálculos, responsividade e exportação.
