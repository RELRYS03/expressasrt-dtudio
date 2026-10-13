# Auditoria de entrega — Express’Arte Studio V7.1

## Evidência validada nesta versão

- **Navegador Chromium automatizado (com modo Canvas):** criação de cubo e cilindro, aplicação de posição X=15 mm, rotação Z=45°, escala Z=1,4, duplicação, desfazer/refazer, salvamento `.exarte`, abertura do arquivo, exportação STL/GLB. Nenhum erro JavaScript registrado nesses fluxos. Evidências em `TESTES_V7_1/results.json`.
- **STL real do usuário:** carregamento de 253.440 triângulos, identificação de 15 corpos, preservação dos 253.440 triângulos após separação; evidência em `results.json`.
- **Imagem real das duas personagens:** carregamento/preview e criação de modelo 2,5D com 39.416 triângulos; isso não é escultura 360°.
- **Geometria das quatro formas:** cubo, cilindro, esfera e anel — todas watertight, orientação consistente e um corpo na verificação Trimesh (`geometry_shapes.json`).
- **Exportação STL e GLB:** reabertos pela biblioteca independente Trimesh: STL com 524 triângulos, 3 componentes fechados e orientação consistente; GLB com 3 objetos e medidas em metros.
- **Layout responsivo:** telas de 1500, 1080 e 390 px, sem overflow horizontal e sem erros JS (`layout_results.json`). Em desktop os painéis têm rolagem interna; em mobile, páginas empilhadas.
- **Servidor local Python/SQLite:** 9/9 testes de API passaram, com banco temporário isolado. Mural salva/lista/devolve modelo e foto, bloqueia entrada inválida e origem externa.
- **Mesh Doctor histórico:** 18/18 testes geométricos existentes passaram. O núcleo desta versão não foi expandido para reparar qualquer malha automaticamente.
- **Amostra 360° procedural separada:** 146 componentes volumétricos fechados, GLB colorido e STL importáveis, 21.936 triângulos. Esta amostra é manual e não implementa geração automática por imagem nem união booleana, portanto não é peça de impressão pronta.

## Limitações e pendências

- WebGL de GPU do navegador **não foi comprovado neste ambiente**: o Chromium usou fallback Canvas. Validar WebGL ativo no Chrome do Windows.
- Não foi testada impressão física, nem integração com impressora/fatiador além da leitura independente da geometria.
- O projeto `.exarte` preserva objetos/transformações/materiais e geometria, mas **não preserva o mapa de pixels da fotografia** usado na prévia 2,5D. A malha gerada continua presente.
- Controles no editor clássico funcionam como arquivo histórico separado, não há sincronização de materiais/edição entre motores antigos.
- Copilot SDK e serviços generativos **não estão conectados**. Os controles indicam essa limitação.
- Normais e materiais procedurais são aproximados. Não há sistema UV/texturas externas nem plugin marketplace executável nesta entrega.
- A malha de cena STL pode incluir corpos sobrepostos. Para impressão, validar o slicer e fazer boolean union quando necessário.

## Próximas etapas de engenharia

1. Validar WebGL com GPU no Windows real e registrar logs/screenshot.
2. Substituir seleção aproximada de objetos por raycasting de triângulos/`three-mesh-bvh`.
3. Integrar Manifold com testes de união/diferença, validação manifold e desfazer.
4. Implementar formato editável persistente versionado, cenas com componentes e geometria incremental para reduzir memória.
5. Para escultura neural: instalar um modelo gerativo adequado com hardware compatível e teste objetivo de identidade/qualidade/volume; depois integração autenticada com provedor, consentimento e revisão do usuário.
