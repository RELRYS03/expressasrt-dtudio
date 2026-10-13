# Express’Arte Studio V7.3 — Formas, 3MF e projetos salvos no Windows

## Instalação e início

1. Extraia **todo** o ZIP para uma pasta normal (por exemplo, `Documentos\ExpressArte_V7_3`). Não execute o programa dentro do ZIP.
2. Abra `INICIAR_EXPRESSARTE_WINDOWS.bat` com duplo clique. Instale Python 3 se necessário.
3. O navegador abrirá o site local. Se a porta 8765 estiver ocupada, o iniciador selecionará outra porta e abrirá a URL correta automaticamente.
4. Para abrir diretamente: `ABRIR_CALCULADORA_WINDOWS.bat`, `ABRIR_MESH_DOCTOR_WINDOWS.bat`, `ABRIR_MEUS_PROJETOS_WINDOWS.bat` (após iniciar o servidor).
5. Mantenha a janela do servidor aberta durante o uso.

**Importante:** `127.0.0.1` pertence ao seu próprio computador. Este servidor é local, não um site público acessível na internet.

## Como criar e continuar editando um chaveiro

1. Entre em **Studio 3D → Modelar** e selecione **Coração** ou outra forma.
2. Ajuste largura, profundidade e altura antes de criar a forma. Use o inspetor para mudar cor, posição, rotação e escala, adicionar mais formas e duplicar.
3. Clique em **Meus projetos** na barra acima do palco 3D.
4. Dê um nome ao projeto e clique em **Salvar neste PC**. A versão também tenta salvar automaticamente após alterações, enquanto o servidor estiver ativo.
5. Navegue para a **Calculadora**, **Comunidade** ou **Catálogo**. O Studio tenta finalizar um salvamento antes de sair.
6. Ao voltar ao Studio, o último projeto salvo será retomado quando possível; para outros trabalhos, escolha na lista **Projetos no computador → Continuar editando**.
7. Para backup portátil, use **Salvar projeto** e guarde o arquivo `.exarte` separadamente.

### Onde estão os arquivos salvos?

No Windows: `%LOCALAPPDATA%\ExpressArteStudio\dados\`.
- `expressarte.sqlite3` — metadados dos projetos e mural da comunidade.
- `projetos\` — documentos `.exarte` do Studio.
- `arquivos\` — publicações da comunidade.

**Isso evita perder dados apenas por extrair uma versão nova em outra pasta.** Não apague essa pasta e mantenha backups periódicos. O servidor não substitui backup externo.

### Migrando dados de uma versão anterior

Se você tem publicações em `dados\` da V7.2.1, feche servidores e execute `MIGRAR_COMUNIDADE_WINDOWS.bat`. Escolha a pasta **principal** da versão anterior. O script recusa substituir dados existentes no destino; nunca apague o banco antigo para tentar forçar uma migração. Confira em `dados/` da versão anterior e faça uma cópia de segurança antes.

## Formas e edição de imagens

O Studio inclui 20 formas: cubo, cilindro, esfera, anel, estrela, coração, seta, nuvem, pensamento, balão de fala, flor, raio, gota, escudo, losango, hexágono, octógono, cantos arredondados, plaquinha e medalha-base.

**Imagem 3D → Gerar camadas 3D editáveis:** separa uma arte em até quatro grupos de cores por algoritmo local. Cria uma base e regiões de relevo separadas e permite editar materiais, cores e dimensões como objetos distintos. Funciona melhor com logotipos e artes planas; a separação de fotografias é aproximada, não segmentação por objeto com IA.

**Exportações:**
- `.exarte` — projeto editável da Express’Arte (geometria, objetos, transformações e cores; **não** preserva automaticamente a foto fonte original ou todas as etapas do editor de imagens).
- `.stl` — geometria sem cor para impressão.
- `.glb` — objetos e materiais básicos para visualização/GameDev.
- `.3mf` — objetos separados e cores básicas; até 125 mil triângulos na exportação simplificada. **Exige revisão no fatiador e atribuição de filamentos.**

A **importação de 3MF** e a edição semântica de malhas já fundidas **não** estão implementadas nesta versão. A união booleana real de sobreposições ainda está pendente. Um chaveiro criado com coração e anel separados pode precisar de união e verificação de resistência no Blender/Bambu Studio antes de imprimir.

## Mesh Doctor

`mesh-doctor.html` abre no servidor local e aceita **diagnóstico** de STL até 300 mil triângulos. Reparos conservadores continuam limitados a 140 mil triângulos, por segurança. Seu arquivo `ornaments(1).stl` (253.440 triângulos) foi diagnosticado no Chromium de teste; para reparar, primeiro separe as peças menores em **Studio → Importar STL**.

O botão **Testar modelo com defeito** permite verificar o reparo sem depender de outros arquivos.

## O que não foi entregue nesta versão

- Escultura neural 360° a partir de fotografia.
- Copilot ou outros modelos de IA externa conectados automaticamente.
- Segmentação semântica de fotos, booleans completos ou 3MF com impressão multicolorida garantida.
- Validação na sua instalação específica do Blender ou no seu Bambu Studio.

## Quatro pilares preservados

**Studio** `studio.html` · **Catálogo** `catalogo.html` · **Comunidade** `comunidade.html` · **Calculadora** `calculadora.html`.

Veja `RELATORIO_V7_3_TESTES_E_LIMITACOES.md` para os testes realizados e as ressalvas.
