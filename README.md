# Rastreamento de objeto colorido com filtro de Kalman

**Equipe:** Antônio Enzo Ferreira do Nascimento e João Felipe Garcia Morais

Trabalho final de Visão Computacional (UFPI, 2026.2), **Opção 01**: rastrear
uma bola verde com segmentação HSV e filtro de Kalman, mantendo a estimativa
durante oclusões, e comparar os modelos de velocidade constante (CV) e de
aceleração constante (CA) em lançamentos.

O filtro de Kalman (predição, correção e região de busca) foi implementado
com NumPy em `src/kalman.py`. A classe `cv2.KalmanFilter` aparece apenas em
`experimentos/6_validacao_opencv.py`, para conferir que os resultados coincidem.

## Estrutura

```
.
├── rastrear.py                 # programa principal (vídeo gravado ou webcam)
├── rodar_tudo.py               # roda todos os experimentos e gera os vídeos de saída
├── requirements.txt
├── src/
│   ├── detector.py             # HSV + abertura/fechamento + componentes conectados
│   ├── kalman.py               # modelos CV e CA e o filtro de Kalman
│   ├── rastreador.py           # gating, "no escuro", perda e reinício da trilha
│   ├── visualizacao.py         # sobreposições (azul/vermelho/laranja)
│   └── pipeline.py             # funções de apoio (abrir vídeo, rodar em lote, CSV)
├── experimentos/               # um script por pergunta do relatório (ver tabela abaixo)
│   ├── 1_ruido_do_detector.py
│   ├── 2_bruto_vs_filtrado.py
│   ├── 3_teimoso_vs_nervoso.py
│   ├── 4_oclusao.py
│   ├── 5_lancamento_cv_vs_ca.py
│   ├── 6_validacao_opencv.py
│   ├── 7_desempenho_fps.py
│   ├── comum.py                # métricas e funções usadas por todos
│   └── video_util.py           # montagem dos vídeos explicativos (1280x720)
├── ferramentas/
│   ├── converter_videos.py     # celular -> H.264, 30 fps constantes, 360x640
│   ├── calibrar_hsv.py         # barras deslizantes para ajustar a cor
│   ├── montar_video_entrega.py # monta resultados/video_entrega.mp4
│   └── marcar_referencia.py    # marcação manual da referência (ground truth)
├── videos/                     # vídeos gravados pela equipe (já convertidos)
├── videos_originais/           # vídeos do celular, sem conversão (fora do git)
├── docs/                       # guia_conceitos_kalman.pdf (fora do git)
├── referencias/                # referências marcadas à mão (criadas pela ferramenta)
└── resultados/                 # uma pasta por experimento (mesmo nome do script),
                                # com tabela.md, figuras e video_*.mp4; mais videos/,
                                # logs/ e video_todos_os_experimentos.mp4
```

## Instalação

Funciona no **Windows, Linux e macOS** com **Python 3.8 ou mais novo**. Todos os
scripts são Python; não é preciso bash.

**1. Ambiente virtual e dependências**

| sistema | comandos |
|---|---|
| Linux / macOS | `python3 -m venv .venv` → `source .venv/bin/activate` → `pip install -r requirements.txt` |
| Windows (PowerShell) | `py -m venv .venv` → `.venv\Scripts\Activate.ps1` → `pip install -r requirements.txt` |
| Windows (cmd) | `py -m venv .venv` → `.venv\Scripts\activate.bat` → `pip install -r requirements.txt` |

Com o ambiente ativado, o comando é `python` nos três sistemas. No PowerShell,
se a ativação for bloqueada, rode uma vez
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

**2. ffmpeg** (opcional, mas recomendado)

| sistema | instalação |
|---|---|
| Linux (Debian/Ubuntu) | `sudo apt install ffmpeg` |
| macOS | `brew install ffmpeg` |
| Windows | `winget install ffmpeg` (depois feche e abra o terminal) |

Sem o ffmpeg tudo funciona, exceto: os vídeos dos experimentos ficam em mp4v
(alguns players não abrem), o vídeo único e o vídeo de entrega não são montados
e não dá para converter vídeos novos do celular.

**Cuidados por sistema**

- **Windows:** coloque o projeto numa pasta **sem acentos nem ç** no caminho
  (ex.: `C:\projetos\Visao`). O OpenCV não abre nem grava vídeos em caminhos
  como `C:\Users\João\...`; o programa avisa se detectar isso.
- **macOS:** na primeira vez que usar a webcam (`--video 0`), autorize o
  Terminal em *Ajustes do Sistema → Privacidade e Segurança → Câmera*.
- **Linux sem interface gráfica** (servidor/WSL sem display): use `--sem-janela`
  no `rastrear.py`; os experimentos não abrem janelas.

## Como executar

```
# rastrear um vídeo gravado (janela com as sobreposições; q = sair, espaço = pausa)
python rastrear.py --video videos/oclusao_grande.mp4

# lançamento com o modelo de aceleração constante
python rastrear.py --video videos/lancamento_horizontal.mp4 --modelo ca

# webcam
python rastrear.py --video 0

# salvar o vídeo com as sobreposições e o log quadro a quadro, sem abrir janela
python rastrear.py --video videos/movimento_mao.mp4 --sem-janela --salvar resultados/videos/teste.mp4 --csv resultados/logs/teste.csv

# câmera lenta 4x, guardando só os trechos em que a bola é rastreada
python rastrear.py --video videos/oclusao_medio_1.mp4 --sem-janela --camera-lenta 4 --so-trechos-com-bola --salvar resultados/videos/lento.mp4

# todos os experimentos e todos os vídeos de saída (~3 min)
python rodar_tudo.py

# só tabelas e figuras, sem os vídeos (mais rápido)
python rodar_tudo.py --sem-video
```

Principais opções de `rastrear.py`:

| opção | padrão | o que faz |
|---|---|---|
| `--modelo cv\|ca` | `cv` | velocidade constante ou aceleração constante |
| `--sigma-d` | 2.0 (cv) / 0.2 (ca) | desvio do ruído do processo, que gera Σd |
| `--sigma-m` | 2.0 | desvio do ruído de medição em px, que gera Σm |
| `--max-sem-medicao` | 30 | quadros só com predição antes de perder a trilha |
| `--raio-min` | 20 | raio mínimo da região de busca (px) |
| `--frac-area-min` | 0.5 | descarta a bola parcialmente escondida (área < 50% da típica) |
| `--hsv-min/--hsv-max` | 35 80 60 / 85 255 255 | limites da cor (use `ferramentas/calibrar_hsv.py`) |
| `--mascara` | — | mostra a máscara HSV ao lado |
| `--camera-lenta N` | 1 | vídeo salvo (e janela) N vezes mais lento; repete cada quadro N vezes e mantém 30 fps |
| `--so-trechos-com-bola` | — | no vídeo salvo, mantém só os trechos com a trilha ativa (+15 quadros antes e depois) |
| `--seguir-fora-do-quadro` | — | não encerra a trilha quando a estimativa sai da imagem |

Para uma cena ou cor diferentes, calibre primeiro:
`python ferramentas/calibrar_hsv.py --video videos/movimento_mao.mp4`.

## Modelo

A unidade de tempo é **o quadro** (dt = 1, vídeos a 30 fps constantes):
posições em px, velocidades em px/quadro, acelerações em px/quadro².

**Velocidade constante (CV):** estado `x = [px, py, vx, vy]ᵀ`, medição `z = [px, py]ᵀ`

```
D = | 1 0 1 0 |     M = | 1 0 0 0 |
    | 0 1 0 1 |         | 0 1 0 0 |
    | 0 0 1 0 |
    | 0 0 0 1 |
```

**Aceleração constante (CA):** estado `x = [px, py, vx, vy, ax, ay]ᵀ`. Em cada
eixo, `p += v + a/2`, `v += a`, `a = a`. A gravidade aparece como `ay`
constante e positiva, porque o eixo y da imagem aponta para baixo.

**Σd (ruído do processo):** modela uma perturbação aleatória entre quadros.
No CV é uma aceleração `a ~ N(0, σd²)`, que gera `Σd = σd² g gᵀ` com
`g = [1/2, 1]` por eixo. No CA é uma variação da aceleração ("jerk"), com
`g = [1/6, 1/2, 1]`. Um σd pequeno gera um filtro **teimoso** (elefante:
confia no modelo, suaviza, mas atrasa); um σd grande gera um filtro
**nervoso** (peixinho-dourado: segue a última medição).

**Σm (ruído de medição):** `Σm = σm² I`, com σm = 2 px. O experimento 1 mede 0,07 px
com a bola parada e uns 0,5 px em movimento; o valor adotado inclui margem
para borrão e oclusão parcial.

**Região de busca (gating):** `S = M P⁻ Mᵀ + Σm`. Uma detecção é aceita se
`d² = (z − M x⁻)ᵀ S⁻¹ (z − M x⁻) < 9,21`, que é o qui-quadrado de 99% com 2
graus de liberdade, ou se estiver a menos de 20 px da predição. Sem medição,
P cresce a cada predição e a elipse cresce com ela, como aparece no vídeo.

**Falhas de detecção:** sem medição aceita, o filtro segue só com a predição
(borda vermelha e "NO ESCURO" no vídeo). Depois de 30 quadros a trilha é
perdida e o filtro é reiniciado na próxima detecção. A trilha também termina
quando o filtro está no escuro e a estimativa sai da imagem ("SAIU DO
QUADRO"), porque não adianta seguir prevendo uma bola que foi embora. Esse
corte só vale no `rastrear.py`; os experimentos não usam. Detecções com menos de
50% da área típica da bola são tratadas como "sem medição": quando a bola
entra atrás do obstáculo só uma parte dela aparece e o centroide fica para
trás, o que ensinaria ao filtro uma desaceleração falsa.

**Cores no vídeo:** medição em **azul**, predição em **vermelho** (cruz), estimativa
corrigida em **laranja** (círculo e trajetória). A elipse vermelha é a região
de busca, e o X cinza marca uma detecção rejeitada pelo gating.

## Experimentos e resultados

Cada experimento é um script em `experimentos/` e grava, numa pasta de
`resultados/` com o mesmo nome do script:

- `tabela.md`: os números, prontos para copiar para o relatório;
- figuras `.png`;
- `video_*.mp4`: um vídeo de 8 a 28 s (1280×720, H.264) que mostra o conceito
  em ação, sem introdução, para ser narrado na apresentação.

O `rodar_tudo.py` também emenda os 7 vídeos em
`resultados/video_todos_os_experimentos.mp4` (~2 min, material complementar) e
monta o **vídeo de entrega** `resultados/video_entrega.mp4` (1 min 49 s):
tela com título e nomes, o sistema rastreando a bola em velocidade normal ao
lado da máscara HSV, e depois os experimentos 4 (oclusões), 5 (CV × CA),
3 (Σd) e 2 (bruto × filtrado). Para montar só ele:
`python ferramentas/montar_video_entrega.py`.

Para rodar só um experimento: `python experimentos/4_oclusao.py`. Para pular os
vídeos de todos os experimentos: `python rodar_tudo.py --sem-video`.

| # | script | pergunta que responde | resultado nos nossos vídeos | o que o vídeo mostra |
|---|---|---|---|---|
| 1 | `1_ruido_do_detector` | Quanto o centroide do detector treme? (é daí que sai Σm) | 0,07 px com a bola parada e ~0,5 px em movimento; adotamos σm = 2 px. | O centroide quadro a quadro e a dispersão ampliada, parada e em movimento, com o círculo de σm. |
| 2 | `2_bruto_vs_filtrado` | O filtro deixa a trajetória mais limpa que a do detector? | Com +3 px de ruído, o erro cai de 3,73 para 3,09 px e a rugosidade de 10,5 para 5,4 px/q²; a variância com a bola parada cai de 9,3 para 5,7 px². | O rastro do detector (tremido) ao lado do rastro do filtro (suave) e o erro de cada um. |
| 3 | `3_teimoso_vs_nervoso` | O que muda quando Σd é pequeno (elefante) ou grande (peixinho-dourado)? | O teimoso (0,3) é o mais suave, mas atrasa e rejeita a bola 195 vezes nos movimentos bruscos; o nervoso (10) copia o ruído; o intermediário (2) é o melhor compromisso. | Os três filtros lado a lado no mesmo vídeo: o teimoso perde a bola na mão e vai melhor na bola rolando. |
| 4 | `4_oclusao` | O filtro acompanha a bola enquanto ela está escondida? | Descartar a bola parcial reduz o erro no reaparecimento de 128 para 48 px (oclusão de 24–27 quadros) e de 59 para 11 px (15–17 quadros). Com limite de 10 quadros, as oclusões longas perdem a trilha. | Três oclusões reais com o gráfico da região de busca crescendo, e uma oclusão sintética com a bola real escondida do filtro. |
| 5 | `5_lancamento_cv_vs_ca` | No lançamento, qual modelo prevê melhor: velocidade ou aceleração constante? | O CA estima ay = 5,41 px/q², contra 5,22 da parábola. A 3 quadros à frente, erra 15,0 px contra 42,6 do CV; no cruzamento da linha previsto 2,7 quadros antes, erra 8 px contra 37. | CV e CA lado a lado, com o caminho futuro previsto por cada um e o ponto em que cada modelo acha que a bola vai cruzar a linha. |
| 6 | `6_validacao_opencv` | Nosso filtro dá o mesmo resultado que o `cv2.KalmanFilter`? | Sim: diferença relativa ≤ 3·10⁻¹⁰ no estado e na covariância (CV e CA). | As duas estimativas uma em cima da outra, com os valores até a 6ª casa decimal e o gráfico da diferença. |
| 7 | `7_desempenho_fps` | Roda a pelo menos 15 fps em 640×480? | Sim: ~400–600 fps aqui, no pipeline completo. | O programa rodando em 640×480 com os fps medidos ao vivo contra a linha dos 15 fps. |

Observações para a discussão:

- O detector HSV desta cena é **muito preciso** (0,07 px parado). Por isso os
  experimentos 2 e 3 também usam um "sensor degradado" (+3 px de ruído
  gaussiano), em que a detecção limpa serve de referência verdadeira. Nesse
  caso o efeito de Σd fica bem visível.
- Na bola rolando, o **CA é pior que o CV** durante a oclusão (experimento 4,
  parte B): ele precisa estimar mais um parâmetro e extrapola o ruído de forma
  quadrática. Já no lançamento, onde a aceleração é real e constante, o CA
  ganha com folga (experimento 5).
- `5_lancamento_cv_vs_ca.py --diametro-bola-cm D` converte a gravidade para m/s² usando o
  diâmetro da bola como escala. Espere um valor diferente de 9,8, por causa
  do borrão, da perspectiva e do arrasto do ar numa bola de isopor. Isso
  também é um bom ponto para discutir.

### Referência marcada à mão (falta fazer)

O enunciado sugere medir o erro contra uma referência marcada à mão. Enquanto
`referencias/` estiver vazia, os experimentos 2 e 3 usam como referência a
trajetória suavizada sem atraso (Savitzky-Golay centrado). Para usar a
referência manual:

```
python ferramentas/marcar_referencia.py --video videos/movimento_mao.mp4 --passo 5
python ferramentas/marcar_referencia.py --video videos/oclusao_pequeno_1.mp4 --passo 2
python experimentos/2_bruto_vs_filtrado.py
python experimentos/3_teimoso_vs_nervoso.py
```

## Vídeos

Todos foram gravados pela equipe com celular, a 30 fps, e convertidos com
`ferramentas/converter_videos.py` para H.264, 30 fps constantes e 360×640
(vertical) ou 640×360 (horizontal). A conversão mantém a proporção e usa
menos pixels que 640×480.

| vídeo | conteúdo | uso |
|---|---|---|
| `bola_parada` | bola parada na mesa | Σm, variância |
| `movimento_mao` | bola movida com a mão (~27 s) | bruto × filtrado, Σd, oclusão sintética |
| `oclusao_pequeno_1/2` | bola rolando, oclusão de 1–3 quadros (até 6 com bola parcial) | oclusão curta |
| `oclusao_medio_1/2` | oclusão de 9–15 quadros | oclusão de 10 a 30 quadros |
| `oclusao_grande` | oclusão de 24 quadros | oclusão de 10 a 30 quadros, perda da trilha |
| `lancamento_horizontal`, `lancamento_1/2` | lançamento parabólico | CV × CA, gravidade, predição |
| `lancamento_quique` | primeiro lançamento (a bola quica na mesa e sai borrada) | não entra nos experimentos; só gera vídeo de saída |

Os vídeos de saída ficam em `resultados/videos/`, em velocidade normal. Em
`resultados/videos/camera_lenta/` estão as versões em câmera lenta, só com os
trechos em que a bola aparece: 4x nas oclusões e 8x nos lançamentos. Esses
usam o codec mp4v; se algum player não abrir, converta para H.264 com
`ffmpeg -i entrada.mp4 -c:v libx264 -crf 20 saida.mp4`. Os vídeos explicativos
de cada experimento (`resultados/<experimento>/video_*.mp4`) já saem em H.264.

## Para estudar o código

Os dois integrantes precisam conseguir explicar qualquer parte. Ordem de leitura sugerida:

1. `src/kalman.py`: as equações da aula, linha a linha.
2. `src/detector.py`: o "sensor".
3. `src/rastreador.py`: o ciclo predição → gating → correção / no escuro → perda.
4. `rastrear.py`: o laço principal.
5. `experimentos/comum.py`: como cada métrica é calculada.
