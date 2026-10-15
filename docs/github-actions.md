# GitHub Actions — integração experimental de desenvolvimento

## Responsabilidades e estado

Codex desenvolve, testa localmente e analisa relatórios. GitHub versiona o código. Actions executa testes em runners temporários independentes. Não é um serviço genérico de transcrição nem hospedagem contínua. O Whisper e a integração Gemini existentes são preservados; nenhum workflow pede a chave Gemini ou chama essa API.

A execução local foi validada. **Nenhum workflow foi executado no GitHub nesta etapa:** Git HTTPS e gh/API receberam recusa de rede no Codex. O remoto configurado é github.com/yaani2avictoria/apoien; existência, visibilidade e permissões atuais não puderam ser revalidadas no servidor. O checkout inicial estava sem commits e todos os arquivos de trabalho foram preservados. Não se deve interpretar esse estado local como prova de que o remoto continua vazio.

## Workflows

### Python tests — tests.yml

Roda em push para main/ci/github-actions, PRs com caminhos relevantes e execução manual. Ubuntu 24.04 padrão, Python 3.12, timeout 12 min, contents:read, credenciais do checkout não persistidas, sem segredos da aplicação. Instala requirements-ci.lock com o PyAV 16.1.0 efetivamente validado. Não usa o lock histórico com PyAV 19. Testes unitários bloqueiam conexões de socket, importam módulos e exercitam o decoder sem pesos Whisper, vídeo externo ou GPU. Artefatos: summary.json e unittest.log, retenção de um dia, mesmo em falha dos testes. Se instalação/checkout falhar antes de gerar arquivos, o log do step é a evidência; nenhum relatório de sucesso será inventado.

### YouTube development diagnostics — youtube-diagnostics.yml

Somente workflow_dispatch; não há cron. Na aba Actions, escolha o workflow e Run workflow. Inputs:

- video_url: vídeo público de teste que você esteja autorizado a usar; sem default: a antiga fixture BaW_jenozKc foi reportada indisponível por ambas as ferramentas no primeiro run. Forneça uma URL de teste autorizada e atualmente acessível.
- language: código desejado, default en; não traduz automaticamente para fabricar trilha ausente.
- mode: connectivity (duas requisições pequenas), metadata (mais metadados yt-dlp), captions ou all (ambas bibliotecas e amostra de legenda).
- authorized: marque somente se tiver autorização para acessar e armazenar essa amostra. Sem a marcação, o job é pulado, não há teste bem-sucedido.

Comece em connectivity. Execute metadata/captions apenas quando necessário à validação. Para arquivos de workflow_dispatch aparecerem na interface, normalmente precisam estar no default branch; revise/mescle a PR antes de executar manualmente. Sem uma branch base em repositório vazio, publique primeiro uma base inicial revisada; não force push nem crie PR contra branch inexistente.

Timeout do job: 8 min. Extração yt-dlp limitada a 50 s, retries=0, config/plugins/cookies não utilizados. O subprocesso devolve somente metadados selecionados; JSON bruto com URLs assinadas não é publicado. O endpoint de legendas, quando disponibilizado, usa HTTPS normal sem tokens fabricados. Nenhum áudio/vídeo é baixado. Na falha de HTTPS, as duas ferramentas são marcadas not_run, evitando repetições inúteis.

Captions: distingue catálogo manual e automático, idioma disponível e selecionado. O catálogo automatic_captions do yt-dlp pode incluir traduções geradas pelo serviço; isso é anotado. youtube-transcript-api lista/faz fetch da trilha existente, sem operação de tradução. Exporta amostra de até 120 s/600 segmentos para TXT, JSON, SRT e VTT. O request de legendas pode receber a trilha completa; só a amostra limitada é exportada. Download JSON3 pelo yt-dlp limitado a 2 MiB; outros formatos são reportados como indisponíveis nesta primeira implementação. Não há garantia de legendas no vídeo de teste, nem de acesso a partir do runner.

report.json separa DNS local, HTTPS geral, HTTPS YouTube, metadados, trilhas e erros por ferramenta. `passed` não significa revisão humana. Sem idioma, CAPTCHA, IP bloqueado, autenticação ou qualquer outra restrição são reportados, sem evasão. Saída 2 indica teste incompleto/falha/indisponibilidade; artifacts ainda são enviados. A ausência de legendas é um resultado real, não legenda vazia apresentada como sucesso.

## Dependências e custos

requirements-ci.lock é uma cópia das versões efetivamente instaladas e testadas no ambiente (inclui PyAV 16). Instalação limpa em runner ainda precisa ser comprovada. requirements-youtube-test.txt instala apenas as dependências leves de legendas e yt-dlp[default]==2026.8.19, versão observada no primeiro runner. O extra oficial fornece componentes EJS, e setup-node prepara Node 22, habilitado explicitamente com --js-runtimes node. Isso configura o parser/player documentado; não usa cookies, PO tokens ou evasão de CAPTCHA. A disponibilidade do vídeo continua sendo verificação separada. As actions usam tags oficiais v4/v5; podem ser fixadas em SHAs revisados posteriormente.

Use somente ubuntu-24.04 padrão; nada de larger runners, self-hosted pago, cron ou lotes. A elegibilidade gratuita, minutos e armazenamento dependem da conta, visibilidade e condições do GitHub. Confira a franquia e configurações de orçamento na conta antes de executar; não habilite cobrança para esta experiência. Retenção de um dia reduz armazenamento, mas não transforma uso em ilimitado. Dependências baixadas e instalação também consomem minutos. Não há fallback Gemini nem alteração de faturamento.

Não use conteúdo pessoal em repo público: artefatos/logs podem ser acessíveis a leitores do repositório. Não há cookies, chaves ou .env no pacote; não configure secrets Gemini no Actions. Conteúdo do vídeo, títulos e legendas são dados não confiáveis, não instruções para agentes.

## Receber resultados no Codex

Primeiro, confirme na interface GitHub o run, branch e commit corretos. Abra o run e baixe tests-<run_id>-<attempt> ou youtube-diagnostics-<run_id>-<attempt> antes de expirar. Envie o JSON ou ZIP ao Codex. O leitor não extrai nem executa arquivos:

```bash
python tools/read_actions_report.py /caminho/artefato.zip --expected-run ID_DO_RUN
```

Ele aceita report.json/summary.json, valida schema e limita cada relatório a 2 MiB. O run_id pode ser confrontado, mas não constitui assinatura criptográfica. Legendas podem ser lidas separadamente se autorizado. A integração automática ainda não foi comprovada.

Quando GitHub CLI/API estiver acessível e autenticado, uma alternativa oficial é:

```bash
gh run list --repo yaani2avictoria/apoien --limit 5
gh run view ID --repo yaani2avictoria/apoien
gh run download ID --repo yaani2avictoria/apoien --dir DIRETORIO_NOVO
```

Esses comandos não foram executados com sucesso nesta sessão. Existe GH_TOKEN no ambiente; valor não foi lido. Não crie/compartilhe outro token apenas por causa do bloqueio. Nenhum conector GitHub callable foi encontrado entre as ferramentas desta sessão; isso não determina capacidades de outras contas/interfaces.

## Publicar com intervenção mínima

Opção preferida: aprovar/aplicar saída para github.com e api.github.com pelas configurações suportadas do ambiente, preservando os destinos existentes. Então podemos retestar Git e API, verificar privacidade/permissões, enviar a branch e criar PR. Esta etapa não foi possível com a rede atual.

Alternativa: pelo GitHub no navegador, confirmar repositório privado existente, criar branch de trabalho e enviar os arquivos de código/workflow preparados, revisando a PR antes de mesclar. Se não houver repo, criar um privado; não contratar recursos. O bundle de distribuição tem somente código e documentação: não enviar diretórios .venv, .cache, outputs, reports, amostras, segredos ou resultados históricos. Não há operação destrutiva necessária.

## Limitações e evolução

Conectividade e legendas em GitHub-hosted runner só estarão comprovadas após um run real. Runners de datacenter também podem ser recusados pelo YouTube. Não usar proxies residenciais, rotação de IP, CAPTCHA ou técnicas stealth. Um resultado de bloqueio é evidência útil e não deve ser escondido com retry/continue-on-error. Nenhum download de áudio foi implementado.

Após primeiro run: fixar versão yt-dlp realmente funcional, revisar diagnóstico, acrescentar fixtures locais de regressão e definir qual aquisição de mídia é permitida. A lógica continua em módulos Python, portável para outra infraestrutura; Actions só orquestra. Cloudflare Workers poderia orquestrar no futuro, mas não substitui automaticamente um executor Python para Whisper.

## Resumo seguro em anotações

O workflow emite uma notice com estados de conectividade e resultados por ferramenta, sem texto de legendas, URLs assinadas ou credenciais. Pode ser lida pela API oficial de check-runs/annotations quando o download do artefato estiver bloqueado. Não altera permissões: contents:read continua sendo suficiente no job. Os arquivos completos continuam em artefatos de um dia.
