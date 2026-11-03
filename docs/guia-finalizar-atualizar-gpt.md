# Guia para salvar o piloto e atualizar o GPT Transcritor

## Estado atual

- O vídeo `meia-entrada.mp4` foi processado localmente no ambiente do Codex com Whisper `base` e pyannote. Os arquivos TXT, SRT e JSON estão em `outputs/meia-entrada-base-pt-diarizado.*`.
- A saída contém 51 segmentos, timestamps e rótulos de quatro vozes. Os rótulos são estimativas (“Pessoa N”); a transcrição em português precisa de revisão antes de ser tratada como literal.
- Os arquivos de código estão na branch `feat/multimodal-pilot`, com alterações ainda não commitadas. Os arquivos em `outputs/` são resultados locais e não fazem parte do commit.
- O GPT personalizado usa uma Action HTTP para o Worker Cloudflare, que chama Gemini. O piloto Whisper + pyannote executado no Codex não foi implantado no Worker e não passa a funcionar no GPT só por salvar os arquivos neste repositório.
- Nesta sessão não foi feita publicação, deploy, alteração de secret ou chamada Gemini.

## 1. Salvar o trabalho no GitHub

No terminal do checkout `/workspace/apoien`, revise primeiro as alterações:

```bash
git status --short
git diff
```

Se estiver tudo correto, salve o código na branch de trabalho:

```bash
git add README.md docs/multimodal-pilot.md docs/guia-finalizar-atualizar-gpt.md \
  requirements-diarization.txt \
  tests/test_exports.py tests/test_diarization.py tests/test_sources.py tests/test_visual.py \
  transcritor/__main__.py transcritor/export.py transcritor/sources.py \
  transcritor/diarization.py transcritor/visual.py
git commit -m "Add local Portuguese diarization pilot"
git push -u origin feat/multimodal-pilot
```

Depois, no GitHub, abra um Pull Request de `feat/multimodal-pilot` para `main` e revise-o antes de fazer merge. Não adicione `.venv/`, `.cache/`, `.env`, secrets ou mídia enviada. As saídas em `outputs/` não são incluídas nesses comandos; mantenha-as como artefatos privados, se precisar guardá-las.

## 2. Entender o que o GPT pode usar hoje

O GPT só chama o que estiver publicado por sua Action. A Action atual aponta para o Worker Cloudflare; ela não enxerga o checkout do Codex, os modelos locais do Hugging Face nem o `HF_TOKEN` do ambiente.

O processamento local com pyannote usa PyTorch e arquivos de modelo. Não é possível ativá-lo apenas alterando as instruções do GPT ou importando novamente o OpenAPI do Worker. O Worker JavaScript atual também não contém esse pipeline Python.

Portanto, o piloto local está encerrado e os resultados estão salvos, mas **a diarização ainda não está disponível no GPT personalizado**.

## 3. Opções para levar diarização ao GPT

### Opção A — manter o GPT como está (sem novos custos)

Não faça deploy. Continue usando o GPT para a função que o Worker já oferece e rode diarização localmente no ambiente Codex quando necessário. As duas etapas permanecem separadas.

### Opção B — integrar uma implementação de diarização ao GPT

Será necessário criar e operar um endpoint de processamento que o GPT Action possa chamar. Esse endpoint precisa receber o vídeo/áudio de forma autorizada, executar ASR e diarização e devolver o resultado em JSON. O código Python local e os modelos pyannote precisam estar presentes nesse executor; o Worker atual não os executa.

Antes de escolher infraestrutura, valide custo, limites de execução, memória/CPU, tamanho de upload, privacidade e autenticação. Não publique `HF_TOKEN`, `GEMINI_API_KEY` ou o token da Action em arquivos ou mensagens. Se uma opção sem custo não comportar os modelos, mantenha o fluxo local em vez de publicar algo que não funciona.

Quando houver uma implementação pronta e validada:

1. Atualize e teste o serviço em uma branch; testes devem usar mocks e não gastar cota Gemini.
2. Publique o serviço e configure secrets somente no painel seguro do provedor.
3. Teste `/health` e a especificação OpenAPI. Faça uma única chamada real autorizada após confirmar modelo, cotas e custo; informe claramente qualquer consumo Gemini.
4. No editor do GPT, abra **Configurar → Ações**. Se a URL ou o schema da API mudou, atualize/import a especificação OpenAPI. Se só a implementação mudou e a URL/schema permaneceram iguais, normalmente não é necessário recriar a Action.
5. Confira a autenticação Bearer da Action sem copiar o token para o chat; teste primeiro com uma mídia curta e autorizada.
6. Ajuste as instruções do GPT para chamar a Action quando pedirem transcrição/diarização e para não inventar rótulos. Salve e atualize/publice o GPT.
7. Faça um teste de ponta a ponta no GPT e confira o log/retorno do Worker e o consumo no painel Gemini. Só então considere a função integrada.

Os nomes dos menus podem variar entre web e aplicativo móvel; a edição de Actions costuma ser mais completa na interface web para computador. Não compartilhe o GPT como público enquanto estiver usando credenciais ou conteúdo de teste privado.

## 4. O que falta para considerar a integração concluída

- Decidir se quer manter a diarização apenas no Codex ou investir tempo em adaptar uma API para executá-la.
- Se optar pela API, preparar e testar o executor Python, sem presumir que Cloudflare Workers Free suporta pyannote.
- Atualizar a Action/instruções somente se o endpoint ou o comportamento exposto mudar.
- Testar um vídeo curto autorizado de ponta a ponta e revisar os rótulos e a transcrição.

Não é necessário atualizar a Action atual apenas para preservar os resultados deste vídeo: os artefatos já estão salvos no checkout local.
