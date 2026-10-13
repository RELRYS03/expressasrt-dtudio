# Express’Arte Studio V7.1.1 — edição de imagem e ações de cena

## Entregas concluídas
- **Excluir peça** acessível no inspetor, além da aba Modelar. Exclusão com **Desfazer/Refazer** também disponíveis no inspetor.
- **Excluir imagem original da área de edição**, sem apagar modelos 3D existentes.
- **Mesclar uma segunda imagem** (PNG/JPG/WebP) sobre a imagem principal com opacidade, posição e tamanho ajustáveis.
- **Recortar imagem** com X/Y/largura/altura percentuais; botão que fixa o recorte sem perder o arquivo original.
- **Colorir e ajustar imagem:** brilho, contraste, saturação, tom e intensidade; resultado efetivamente usado na próxima conversão foto→2,5D.
- **Salvar PNG editado** no computador; **Restaurar original** preserva a imagem antes da edição.
- Conteúdo salvo em PNG, sem upload para servidor. Nenhuma integração paga foi ativada.
- Todos os pilares existentes — site/catálogo, Studio, comunidade, calculadora, editor clássico e Mesh Doctor — continuam no pacote com o histórico preservado.

## Testes realmente executados
- Navegador Chromium automatizado via Playwright com código HTML/JS injetado em ambiente de testes; navegação `file://` ou localhost estava bloqueada no ambiente. **Isto não é um teste WebGL final no PC do usuário.**
- Foto real da dupla: abertura **1024×1536 px**; mesclagem de uma camada PNG, opacidade 83%, brilho 112%, contraste 115%, coloração 33%, recorte para **768×1106 px**; download de PNG conferido no Pillow.
- Conversão 2,5D da **imagem editada** e download STL: **72.124 triângulos**.
- Reabertura do STL exportado no Trimesh: **fechado, orientação consistente, volume positivo, 1 corpo**, dimensões aproximadas **100,7 × 145 × 3,2 mm**.
- Excluir único objeto e desfazer **0→1**; imagem excluída mantendo o objeto existente; restaurar foto original **1024×1536 px**.
- STL real de ornamentos: **253.440 faces**, **15 componentes**, exclusão **15→14** e desfazer **14→15**, contagem de faces preservada na separação.
- Teste complementar no celular **390 px**: recorte fixado **512×768**, campos zerados após fixação, imagem original restaurada **1024×1536**, sem rolagem horizontal nem erros JavaScript.
- Nenhum erro de JavaScript nos fluxos exercitados.
- Servidor local: bateria preservada **9/9** aprovada, executada em pasta temporária sem alterar dados reais.
- Verificação de sintaxe `node --check` dos scripts novos aprovada.

## Limitações honestas
- **Mesclar imagens** é sobrepor camadas 2D: não é união booleana de sólidos 3D.
- **Recortar** refere-se à imagem em pixels, não a cortar a malha STL por plano.
- A criação a partir de imagem produz relevo/silhueta **2,5D**, não escultura neural fiel em 360°.
- **Colorir imagem** altera o PNG de entrada. STL continua sem textura/cor; GLB da cena utiliza materiais simples, não incorpora automaticamente o mapa da foto.
- A V7.1.1 não chama Meshy, Tripo ou Copilot. Uma integração por API externa exige conta, credencial, autorização de envio e consumo de créditos, além de testes.
- A visualização WebGL ainda requer teste com a GPU do computador Windows do usuário.

## Como testar no Windows
1. Extrair todo o ZIP (não abrir o HTML de dentro do compactador).
2. Executar `INICIAR_EXPRESSARTE_WINDOWS.bat` com Python 3 instalado.
3. Abrir `http://127.0.0.1:8765/studio.html` no Chrome.
4. Aba **Imagem 3D** → enviar foto → seção **Editar imagens** → mesclar, recortar, colorir e baixar PNG.
5. Clicar **Gerar peça 3D imprimível** e conferir dimensões, STL e visualização no Bambu Studio.
6. Selecionar objeto no inspetor → **Excluir peça selecionada** → **Desfazer** para restaurar.
7. Aba **Importar STL** → usar arquivo `site/exemplos/ornamentos_15_pecas_original.stl` → separar e editar.

Detalhes de API: `INTEGRACAO_FOTO_3D_API.md`. Resultados automatizados: pasta `TESTES_V7_1_1/`.
