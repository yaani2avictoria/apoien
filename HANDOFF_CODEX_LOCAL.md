# Handoff para continuar no Codex local

Atualizado em 3 de novembro de 2026. Este arquivo resume o contexto útil desta conversa para continuar em outro chat do Codex. Não é a exportação literal da conversa.

## Comece por aqui

Abra esta pasta do repositório no Codex local e envie:

> Leia `HANDOFF_CODEX_LOCAL.md`, `README.md` e `docs/guia-finalizar-atualizar-gpt.md`. Use esse handoff como contexto. Preserve o estado atual e não rode testes que baixem modelos, não chame Gemini/Cloudflare nem altere o código até eu pedir. Primeiro confirme o que está disponível neste computador e explique como retomar o projeto.

## Projeto e preferências

- Projeto: transcritor experimental em Python, repositório `yaani2avictoria/apoien`.
- O usuário quer executar no próprio Codex e, mais tarde, no desktop, priorizando software open source e custo adicional zero.
- Não contratar API, proxy, servidor ou infraestrutura paga. Não habilitar cobrança.
- Não contornar bloqueios, autenticação, CAPTCHA, DRM ou políticas de sites. Processar apenas mídia que o usuário possa usar.
- Proteger `GEMINI_API_KEY`, `TRANSCRITOR_TOKEN` e `HF_TOKEN`; nunca pedir que sejam colados em chat, log ou repositório.
- Não fazer chamadas Gemini automaticamente: podem gastar a cota gratuita. O usuário deve autorizar qualquer chamada real.
- Preferência recente: o piloto já está bom para o objetivo de distinguir vozes. O usuário disse que não quer novos ajustes agora e quer encerrar. Não retome melhorias sem pedido explícito.

## Estado do GitHub

- Branch: `feat/multimodal-pilot`.
- Último commit no momento deste handoff: `44a6c200fecdd0781474d13ab3b6fe0ede8f45a6` (`Add local Portuguese diarization pilot`).
- Branch publicada em `origin`; `main` não foi alterada. Não há Pull Request criado.
- Para obter a versão no desktop:

  ```bash
  git clone --branch feat/multimodal-pilot https://github.com/yaani2avictoria/apoien.git
  ```

- O ZIP pelo GitHub também pode ser baixado em `https://github.com/yaani2avictoria/apoien/archive/refs/heads/feat/multimodal-pilot.zip`.
- `.venv/`, `.cache/`, mídia enviada, credenciais e `outputs/` não estão versionados. A transcrição do teste precisa ser transferida separadamente se o usuário quiser mantê-la no computador.

## O que o programa faz

- `faster-whisper` transcreve arquivos locais na CPU; `youtube-transcript-api` tenta obter legendas acessíveis de URLs do YouTube.
- O acesso direto do Codex ao YouTube já retornou proxy CONNECT `403`; isso não deve ser contornado.
- `--diarize` usa pyannote localmente para estimar rótulos cronológicos “Pessoa N”. Rótulos não são nomes nem identificação real.
- `--visual-ocr` é um piloto experimental e não prova que a pessoa em quadro é a pessoa que fala.
- GitHub Actions tem workflows para testes offline e diagnóstico manual. Actions não é uma API de transcrição nem executor de produção.
- Ver `README.md`, `docs/multimodal-pilot.md` e `docs/github-actions.md` para detalhes.

## Piloto do vídeo enviado

- Arquivo fornecido pelo usuário: `meia-entrada.mp4`, aproximadamente 115 segundos. O vídeo não foi incluído no repositório.
- Processamento reportado: Whisper `base`, idioma português, CPU int8; diarização com pyannote `speaker-diarization-3.1`.
- Foram salvos no workspace original:
  - `outputs/meia-entrada-base-pt-diarizado.txt`
  - `outputs/meia-entrada-base-pt-diarizado.srt`
  - `outputs/meia-entrada-base-pt-diarizado.json`
- JSON: 51 segmentos com timestamps e quatro rótulos de voz; “Pessoa 4” aparece em dois segmentos. A transcrição tem erros de português e deve ser revista se for usada como citação literal.
- O usuário considerou a distinção de vozes suficiente para o objetivo e não quis mais refinamento.
- A suíte local reportada passou com 42 testes.
- Importante para reprodução: a primeira execução teve incompatibilidades de dependência, cache e configuração de modelo. Foi fixado `huggingface-hub==0.27.1` e adicionado WAV temporário ao adaptador. A obtenção daqueles resultados exigiu ajustes/cache locais; reprodução limpa em outro desktop não foi comprovada. Não afirme que basta instalar e que o modelo funcionará sem conferir README, termos de acesso do Hugging Face, dependências e `HF_TOKEN` local.

## GPT personalizado, Worker e Gemini

- O GPT personalizado chamado “Transcritor” usa uma GPT Action HTTP para um Cloudflare Worker, separado deste repositório.
- O Worker foi criado como ponte autenticada para Gemini e tem `/health`, `/openapi.json` e `/transcribe`. O usuário relatou ter configurado secrets e confirmado `/health` pelo navegador em uma etapa anterior.
- Foram observados erros Cloudflare 403/1010 para alguns clientes automatizados; o estado atual do Worker não foi verificado neste handoff.
- O Worker JavaScript/Gemini não usa automaticamente o código Python/Whisper/pyannote deste repositório. O piloto local não está disponível no GPT.
- Para oferecer diarização no GPT seria necessário um endpoint acessível pelo GPT Action capaz de executar Python/pyannote. Não presuma que Cloudflare Workers Free consegue rodar PyTorch/pyannote. Avalie custo, CPU, RAM, tempo, upload e privacidade antes de propor implantação.
- Não tente editar ou publicar o GPT/Worker sem acesso explícito às ferramentas adequadas e sem o pedido do usuário. A importação do OpenAPI só atualiza o contrato da Action; não transporta código local.

## Histórico curto de decisões

1. Meta original: transcrever YouTube gratuitamente no Codex Cloud. A saída de rede do Codex bloqueou YouTube com 403; foi escolhido preservar políticas de acesso.
2. Gemini via AI Studio foi explorado como fallback; cotas Free Tier não são ilimitadas e chamadas podem consumir a franquia.
3. Foi criado GitHub Actions para testes e diagnóstico, sem tratar runner como serviço de produção.
4. O usuário optou por executar Whisper e diarização local no projeto e forneceu mídia para um teste curto.
5. Após o resultado, o usuário aceitou a qualidade de separação de vozes e pediu encerrar, salvar e depois transferir o contexto para o Codex local.

## Limites deste handoff

O arquivo não leva a conversa literal, vídeo, arquivos de saída, caches, modelos ou secrets. Se esses resultados forem necessários no desktop, transfira-os por um canal privado separado. Não os envie para repositório público.
