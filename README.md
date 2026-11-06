# Transcritor gratuito em CPU

Protótipo Python sem API de transcrição, conta de provedor ou servidor persistente. Usa `faster-whisper` localmente e `youtube-transcript-api` apenas para legendas acessíveis. Não baixa áudio do YouTube nem tenta contornar bloqueios, autenticação ou DRM.

**Estado verificado:** instalação e testes unitários passaram; a transcrição real e as legendas do YouTube ficaram bloqueadas pela política de rede do Codex Cloud. Consulte [o relatório](reports/viabilidade.md). Exemplos são sintéticos, não transcrições obtidas.

## Instalação

Validado em Debian 13, Python 3.12, CPU x86_64. A instalação pode baixar centenas de MB. O modelo tiny requer um download adicional da ordem de dezenas de MB; base é maior. Recursos e franquias do ChatGPT não são ilimitados.

```bash
cd /workspace/apoien
python -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -s tests -v
```

`requirements.txt` declara as duas dependências principais gratuitas; `requirements.lock` registra todas as versões efetivamente instaladas. Em outras plataformas, a disponibilidade de wheels pode variar. O PyAV incluído nas dependências decodifica mídia; o programa não exige um processo FFmpeg separado.

## Execução

Use somente mídia cuja utilização seja autorizada. Para o primeiro teste, forneça até 60 segundos. Há limite de 25 MiB por download direto; arquivos com duração desconhecida são recusados. O limite de duração configurável vai até 300 segundos, mas não é uma garantia de memória nem de tempo máximo de execução.

```bash
cd /workspace/apoien
timeout 120 .venv/bin/python -m transcritor samples/jfk.wav --authorized --model tiny --threads 2 --output outputs/jfk
timeout 30 .venv/bin/python -m transcritor 'https://www.youtube.com/watch?v=nkjymufhKpU' --languages pt en --output outputs/youtube
```

O primeiro comando requer o áudio de demonstração. Para obtê-lo pela origem pública usada no teste:

```bash
mkdir -p samples
.venv/bin/python - <<'PY'
from transcritor.sources import download
download('https://raw.githubusercontent.com/ggerganov/whisper.cpp/master/samples/jfk.wav', 'samples/jfk.wav')
PY
```

Esse trecho de discurso presidencial de John F. Kennedy está disponível no projeto whisper.cpp e é usado como demonstração; a gravação de fala governamental é de domínio público nos EUA. Verifique regras locais para redistribuição. O download é opcional e não faz parte da instalação.

Também é possível passar caminho de vídeo ou URL HTTPS direta de mídia autorizada com `--authorized`. URLs do YouTube tentam somente recuperar legendas; se indisponíveis, o programa termina com erro. Forneça separadamente um arquivo autorizado para usar reconhecimento local. `--model base` é opcional e não foi validado aqui.

O modelo é executado em CPU, `int8`, duas threads por padrão, um worker e beam size 1. A primeira execução precisa baixar o modelo do Hugging Face. O cache fica em `.cache/models`. Não existe fallback para serviço pago. A língua é detectada automaticamente no reconhecimento; `--languages` seleciona idiomas de legendas do YouTube.

Se já tiver um modelo CTranslate2 tiny/base oficial transferido por via autorizada, use `--model-dir /caminho/do/modelo` para carregá-lo localmente. Esse caminho alternativo ainda não foi validado com um modelo nesta sessão.

Em sucesso são criados `<output>.txt`, `.srt` e `.json` com timestamps em segundos no JSON e milissegundos no SRT. O TXT contém apenas o texto. A origem identifica `youtube_captions` ou `local_faster_whisper`; legendas automáticas são identificadas pelo campo `generated`. A execução escreve status, tempo e pico de RSS do processo em stderr e retorna 0 em sucesso ou 1 em falha. `timeout` pode retornar 124 se interromper o processo; nesse caso a medição final pode não existir. Escolha uma saída nova: arquivos existentes com o mesmo nome serão substituídos em sucesso.

## Rede, segurança e limites

- PyPI e arquivos do GitHub estavam acessíveis. Hugging Face e YouTube foram negados pelo proxy com 403.
- Os domínios necessários foram salvos no rascunho do ambiente; salvar o rascunho não altera automaticamente a máquina atual. Revise e salve as configurações de rede e publique o ambiente quando apropriado. Depois, refaça os testes. A liberação não garante que o YouTube permita acesso.
- Não forneça chaves de API. Não é necessário usar OpenAI API, VPN ou serviço pago.
- A execução pode ter erros de acesso, rede, decoder, dependências ou memória; a mensagem mantém o tipo da falha. O RSS mede somente este processo, não o ambiente inteiro. O limite preventivo de duração não torna seguro processar arquivos hostis ou arbitrariamente grandes.
- Não há garantia observada de prazo máximo da sessão, armazenamento durável ou restauração em uma nova tarefa. Não confie na sobrevivência de processos. Preserve fontes e resultados pelo fluxo de publicação ou exportação da plataforma.

## Organização

`transcritor/sources.py`: obtenção de legendas, download limitado e inferência; `export.py`: TXT/SRT/JSON; `__main__.py`: CLI, erros e medições. `tests/` contém testes sem rede. `examples/` mostra apenas formatos. `reports/` registra evidências e limitações.

## Próxima skill reutilizável

Crie uma skill com diagnóstico de CPU/RAM/disco/rede, checagem do ambiente virtual e cache, confirmação da autorização da mídia, preferência por legendas, teste tiny de até 60 segundos e execução sob `timeout`. Registre proveniência, tempos, RSS e erros, e nunca trate um teste de formato como transcrição real. Reutilize o checkout existente; não crie worktrees. Mantenha instalação separada da execução, sem daemon e sem baixar modelos novamente quando o cache estiver válido. Só amplie modelo e duração após uma transcrição real bem-sucedida. Uma skill não altera a política de rede nem garante recursos gratuitos ilimitados.

## Ajuste de cache no Codex Cloud após publicação

Antes da inferência, configure um cache gravável:

```bash
export HF_HOME=/workspace/apoien/.cache/huggingface
export HF_XET_CACHE=/workspace/apoien/.cache/huggingface/xet
```

O reteste publicado liberou huggingface.co, mas os pesos redirecionam para `us.aws.cdn.hf.co`, ainda bloqueado. Esse domínio foi acrescentado ao novo rascunho. YouTube continuou com 403 apesar de constar na configuração publicada. Veja os detalhes no fim do relatório; ainda não há transcrição real validada.

## Transferir o modelo para execução local no Codex

Em computador próprio com acesso permitido ao Hugging Face, execute `tools/preparar_modelo.py` após instalar `huggingface-hub` em um ambiente virtual. Ele baixa apenas o modelo tiny oficial, fixa a revisão resolvida, registra SHA-256 dos arquivos e cria `faster-whisper-tiny.tar.gz`, sem conta paga ou API de transcrição. O script foi preparado, mas seu download externo ainda não foi executado/validado nesta sessão.

Transfira o arquivo pelo mecanismo de upload autorizado da plataforma, se disponível e compatível com o tamanho do arquivo. Antes de extrair, valide os caminhos do arquivo compactado; depois confira os hashes do manifesto. O manifesto detecta corrupção de transferência, não substitui a confiança na origem oficial.

Com o diretório validado no Codex, o teste será:

```bash
HF_HUB_OFFLINE=1 timeout 120 .venv/bin/python -m transcritor samples/jfk.wav --authorized --model-dir /workspace/apoien/models/faster-whisper-tiny --threads 2 --output outputs/jfk-offline
```

O modelo completo ainda é um requisito pendente; o comando offline não foi validado com inferência real.

## Resultado atualizado: transcrição real aprovada

O download do modelo foi liberado e a amostra de 11 segundos foi transcrita aqui no Codex, em CPU int8, sem API paga. Execução offline: 1,306 s, pico RSS 250,83 MiB. Resultados reais: examples/jfk-real.txt, .srt e .json. O YouTube ainda retorna 403.

**Correção de compatibilidade necessária:** após instalar requirements.lock, execute `.venv/bin/python -m pip install av==16.1.0`. O PyAV 19 fixado no lock original é incompatível com o argumento metadata_errors usado por faster-whisper 1.2.1. As versões efetivamente validadas estão em reports/dependencies-validado.txt.

Para o primeiro download oficial, use HF_HUB_DISABLE_XET=1 junto com os caminhos de cache descritos acima. Após o modelo estar completo no cache, use HF_HUB_OFFLINE=1 para inferência sem rede.

## Skill reutilizável no Codex

A skill está em `.agents/skills/transcritor/SKILL.md`, dentro deste repositório. Abra uma tarefa no ambiente associado ao projeto. Se a skill aparecer no catálogo, invoque `$transcritor`. Caso não apareça, use uma instrução explícita:

> Leia e siga `.agents/skills/transcritor/SKILL.md`. Transcreva de 04:30 a 04:50 do vídeo https://www.youtube.com/watch?v=nkjymufhKpU. Use o segredo configurado; meu projeto Gemini está no Free Tier, sem faturamento habilitado.

Para mídia anexada:

> Leia e siga `.agents/skills/transcritor/SKILL.md` e transcreva o arquivo anexado com Whisper local, exportando TXT, SRT e JSON.

A skill é um arquivo versionável com instruções para o Codex. Não instala um plugin global no ChatGPT; a descoberta automática deve ser conferida em uma nova tarefa. Ela depende do código deste repositório e do ambiente preparado; credenciais não são incluídas nos arquivos. O diretório global `/workspace/.agents` é somente leitura nesta máquina; a instalação foi feita no escopo gravável do repositório.

O script Gemini agora aceita `--url`, `--start-seconds` e `--duration-seconds` (até 300 s por chamada). Exporta TXT e JSON em respostas completas; respostas truncadas ou vazias mantêm apenas JSON diagnóstico e status de falha. Não gera SRT sem timestamps confiáveis. Os testes de CLI usam respostas simuladas, sem API e sem consumo da cota.

## Pacote de plugin

Foi preparado `plugins/transcritor/` com `.codex-plugin/plugin.json`, skill, scripts e dependências fixadas. O marketplace local está em `.agents/plugins/marketplace.json`. Para gerar novamente o ZIP, execute `.venv/bin/python tools/empacotar_plugin.py`; o artefato é `dist/transcritor-plugin.zip`.

O formato segue exemplos de plugins e marketplaces presentes no runtime instalado. Os comandos `codex plugin marketplace add` e `codex plugin add` existem neste CLI, mas o cadastro neste ambiente falhou porque `/run/codex-environment/codex-home` é somente leitura. A tentativa de leitura pelo app-server também não iniciou por falta de escrita no estado SQLite desse diretório. Assim, o pacote foi criado e verificado estruturalmente, mas não foi instalado no catálogo da conta e o parsing completo pelo Codex continua pendente.

Em cliente compatível com configuração gravável, os comandos de instalação estão em `plugins/transcritor/README.md`. Não é necessário executar no computador pessoal para continuar usando a ferramenta neste ambiente: a leitura explícita da skill continua disponível. A interface web pode ter um fluxo próprio de plugins, que precisa ser confirmado pelas opções realmente exibidas. Não há garantia de que aceite importar ZIP.

## Vídeo inteiro pela API Gemini

Com projeto Free Tier confirmado, é possível solicitar o vídeo inteiro em uma única chamada usando `--full-video`. O script omite o recorte, limita a saída em 32.768 tokens, usa timeout interno de 240 s e não faz retries. Exemplo:

```bash
timeout 250 .venv/bin/python tools/testar_gemini_youtube.py --free-tier-confirmed --full-video --url 'https://www.youtube.com/watch?v=nkjymufhKpU' --output outputs/video-inteiro.json
```

Esse modo não pode ser combinado com parâmetros de recorte. O pedido de vídeo inteiro não garante completude: confira finishReason, conteúdo, consumo e eventuais omissões. A geração permanece não verificada até conferência do áudio; não cria SRT com timestamps inventados. Não use a conclusão STOP como prova isolada de que toda fala foi incluída. Se falhar por cota/demanda, preserve a resposta e pare, sem novas chamadas automáticas.

## Diagnóstico de acesso direto, sem Gemini

A auditoria atual está em `reports/auditoria-youtube-2026-10-15.md`. A política observada permite apenas o endpoint Gemini; YouTube/PyPI receberam CONNECT 403 e yt-dlp não estava instalado. Acesso direto ainda **não está resolvido**.

```bash
.venv/bin/python -m transcritor.diagnostico 'https://www.youtube.com/watch?v=nkjymufhKpU' --check-metadata
```

O comando não baixa áudio nem chama Gemini. Distingue DNS local, política do snapshot, proxy, HTTP/autenticação, cota e extração; omite URLs assinadas e credenciais. Se a política exclui YouTube ou o HTTPS falha, não executa yt-dlp. Se a rede estiver acessível e yt-dlp instalado, tenta somente metadados com config/plugins desabilitados, sem cookies e sem retries. O timeout externo do processo é de 45 s. O status de saída é 0 só se metadados forem obtidos; 2 significa acesso direto não demonstrado; 1 indica erro na própria execução.

O cache de diagnóstico fica em `.cache/diagnostico` por 600 s e leva em conta URL/ID, opção de metadados, política, Python e versão yt-dlp. Use `--refresh` para autorizar nova checagem após mudança real ou pedido explícito; sem isso, a mesma falha não gera novas requisições durante o TTL. Snapshot não equivale à política efetivamente aplicada: confirme environment_status e teste o acesso real quando permitido. DNS local não é usado como razão isolada para interromper HTTPS pelo proxy.

O yt-dlp é opcional e não foi adicionado às dependências principais. Com acesso permitido a PyPI/files.pythonhosted.org, instale a versão atual oficial no venv e registre a versão antes do teste real. Instalação, extração bem-sucedida e autorização de download são etapas distintas. O diagnóstico não implementa download de mídia YouTube.

### Reutilizar resposta Gemini já processada

A integração existente continua explícita. A opção `--reuse-result`, com o mesmo `--output` e parâmetros, só reutiliza resultados novos com fingerprint idêntico, STOP e texto não vazio. Não envia chamada de API nesse caso. Resultados antigos sem fingerprint, recusas ou truncamentos não viram cache de sucesso. O programa agora recusa sobrescrever saídas existentes: escolha um nome novo para uma nova tentativa autorizada. Nenhuma chamada Gemini é feita automaticamente quando a rede/legendas falham.

```bash
.venv/bin/python tools/testar_gemini_youtube.py --free-tier-confirmed --reuse-result --full-video --url 'https://www.youtube.com/watch?v=ID_DO_VIDEO' --output outputs/resultado.json
```

Cache evita requisições duplicadas idênticas; não verifica fidelidade ou cota da conta. TXT/SRT/JSON históricos permanecem preservados.

## Desenvolvimento com GitHub Actions

A primeira integração está em `.github/workflows/tests.yml` (unitários e smoke offline) e `.github/workflows/youtube-diagnostics.yml` (diagnóstico manual autorizado, sem áudio/vídeo e sem Gemini). Instruções, limites de uso e leitura de artefatos: [docs/github-actions.md](docs/github-actions.md). A execução real em runner ainda não foi realizada; não presuma acesso ao YouTube.
