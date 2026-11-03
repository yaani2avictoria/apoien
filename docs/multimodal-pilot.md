# Piloto multimodal local — resultado inicial

Data: 2026-10-21. Este piloto usa um MP4 enviado pelo usuário, com cerca de 65 segundos. O arquivo foi inspecionado localmente; não houve chamada ao YouTube, ao Worker ou ao Gemini.

## Áudio

O ambiente atual confirma a política de rede como `enforced`, com `huggingface.co` e `us.aws.cdn.hf.co` permitidos. Os modelos Whisper tiny e base foram baixados do Hugging Face e o áudio foi processado localmente em CPU `int8`, com idioma português forçado. Nenhuma chamada ao Gemini/Worker foi feita.

- Duração do vídeo: aproximadamente 65 s; 10 segmentos exportados.
- Tempo total do processo, incluindo carregamento do modelo: 17,054 s.
- Pico de RSS do processo: 269,86 MiB.
- Whisper tiny: 17,054 s no primeiro carregamento, pico RSS de 269,86 MiB; resultado com muitos erros em nomes próprios e palavras regionais.
- Whisper base: 19,462 s, pico RSS de 409,25 MiB; melhora perceptível em frases comuns, mas ainda erra nomes/localidades e expressões regionais. Tratar como rascunho, não como texto revisado.
- TXT, SRT e JSON do base: `outputs/ne1netv-base-pt.*`; saídas tiny permanecem em `outputs/ne1netv-tiny-pt.*` e `outputs/ne1netv-repeat-tiny-pt.*`.

## Imagem e OCR

O vídeo tem faixa de vídeo VP9 e faixa de áudio AAC. O Tesseract disponível possui apenas os idiomas `eng` e `osd`; `por` não está instalado.

- Amostragem a cada 10 s: 7 quadros, nenhuma observação OCR.
- Amostragem a cada 5 s: 13 quadros, nenhuma observação OCR.
- Revisão visual do quadro em 00:30 mostra a tarja “MÁRCIO BONFIM” e “Bairro do Pina”. O Tesseract, mesmo com recorte ampliado, não leu o texto de forma confiável; esta identificação veio de inspeção visual, não do OCR.
- Smoke test sintético do Tesseract confundiu “HELLO” com “HELLU”.

Resultado: o modo OCR está funcionando tecnicamente, mas a precisão não foi suficiente para este vídeo. A tarja identifica visualmente o repórter em quadro, mas isso não é diarização acústica e não comprova que toda fala no trecho, inclusive a fala em off, seja dele. A transcrição de áudio foi gerada separadamente; as observações visuais não foram misturadas à fala.

## Próximos passos

1. Revisar manualmente nomes próprios e palavras regionais no rascunho do modelo base.
2. Instalar dados `por` do Tesseract e avaliar pré-processamento/crop da tarja; manter texto OCR separado da fala.
3. Se OCR tradicional continuar falhando, avaliar um modelo visual local separadamente, medindo download, memória e tempo.

Este piloto validou áudio local com Whisper em português, mas não a leitura OCR nem uma transcrição final revisada. Foi preparado um caminho opcional de diarização via pyannote com rótulos Pessoa N; ele tem testes unitários, mas ainda depende de instalar o modelo gated, configurar HF_TOKEN e executar validação real. O status do ambiente observado nesta tarefa informa `network_policy.state: unknown`, então não fiz downloads nesta etapa.
