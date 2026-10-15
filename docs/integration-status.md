# Estado observado da primeira integração

Data: 15/10/2026, America/Sao_Paulo.

## Projeto preservado

Whisper para arquivos e Gemini explícito para URLs continuam implementados. Resultados históricos, caches, modelos, pacotes de skill e arquivos existentes permanecem no workspace. Não foram incluídos no bundle/commit de código os conteúdos de reports, outputs, amostras, .env, venv ou chaves. Não houve chamada Gemini nem download de mídia nesta etapa.

## GitHub

Há Git local e origin configurado como yaani2avictoria/apoien em github.com. O checkout inicial não tinha commits; o trabalho foi organizado na branch ci/github-actions. Um teste somente leitura de git ls-remote recebeu CONNECT 403. A consulta gh api repos/yaani2avictoria/apoien recebeu Forbidden. GH_TOKEN está presente, sem exposição; não foi solicitado outro token. Não existe conector GitHub callable nas ferramentas atualmente disponíveis.

Essas falhas não comprovam falta de permissões, inexistência do repositório ou indisponibilidade de integrações em outros clientes. Visibilidade, branch default e escrita no servidor ainda não foram verificadas. Não foi criado repositório, feito push ou aberta PR, pois a rede não permite essas operações e não seria seguro presumir visibilidade privada.

## Validação efetiva

- 29 testes locais executados, zero falhas, zero erros e zero skips.
- Importação de fontes, exportação, diagnóstico, faster-whisper, CTranslate2, youtube-transcript-api e PyAV passou.
- Decoder PyAV com metadata_errors=ignore validado com WAV sintético curto, sem modelo ou transcrição fictícia.
- CLI de diagnóstico inicializa em --help.
- YAMLs lidos e checados estruturalmente: runner Ubuntu padrão, contents:read, sem cron, sem secrets de aplicação e retenção de um dia.
- Leitor de relatórios validado com JSON local e testes de ZIP, limite de formato e run_id. O relatório local marca github_actions=false, não simula execução remota.
- pip check sem dependências quebradas.

Não houve validação de actionlint ou parser remoto do GitHub; a checagem YAML local não os substitui. Não foi feita instalação limpa de dependências em runner. yt-dlp continua ausente nesta máquina e seu comportamento real depende do primeiro run.

## Pendências externas

Os workflows estão prontos no código, mas nenhum run remoto aconteceu. Ainda não há evidência de conectividade YouTube ou extração de legendas em runner GitHub-hosted. A única forma de afirmar isso será examinar report.json e logs de uma execução real.

Proposta: autorizar github.com e api.github.com pelo fluxo de rede do ambiente, preservando regras atuais. A mudança em rascunho não aplica a política à máquina. Se não for possível, enviar os arquivos pelo GitHub no navegador em repo privado e branch de trabalho. Somente após verificar visibilidade/permissões e existência da base será possível publicar branch/PR. Actions continua opcional e vinculado ao desenvolvimento, sujeito à franquia da conta.
