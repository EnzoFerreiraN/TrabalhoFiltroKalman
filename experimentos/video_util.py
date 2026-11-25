"""
Ferramentas para montar os vídeos de explicação dos experimentos.

Todos os vídeos usam a mesma tela de 1280x720:
    - faixa de título no topo (nome do experimento)
    - área de conteúdo no meio (o vídeo, lado a lado, gráficos...)
    - faixa de legenda embaixo (o que observar)
e começam com um cartão de título que explica o que olhar.
Assim os vídeos podem ser emendados direto no vídeo de entrega.

Para pular a geração dos vídeos (mais rápido): python rodar_tudo.py --sem-video
(ou defina a variável de ambiente SEM_VIDEO=1 antes de rodar um experimento).
"""
import os
import shutil
import subprocess
import unicodedata

import cv2
import numpy as np

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # sem Pillow: textos sem acento com o OpenCV
    Image = None

from src.kalman import LIMIAR_GATE_99
from src.pipeline import avisar_caminho
from src.rastreador import INATIVO
from src.visualizacao import desenhar

LARG, ALT = 1280, 720
TOPO, RODAPE = 56, 48
AREA = (LARG, ALT - TOPO - RODAPE)       # área de conteúdo: 1280 x 616
FUNDO = (32, 32, 32)
FPS = 30

# cores BGR (as mesmas da visualização)
AZUL, VERMELHO, LARANJA = (255, 0, 0), (0, 0, 255), (0, 140, 255)
BRANCO, PRETO, CINZA = (255, 255, 255), (0, 0, 0), (160, 160, 160)
VERDE, MAGENTA = (60, 200, 60), (255, 0, 255)


def gerar_videos():
    return os.environ.get("SEM_VIDEO", "") not in ("1", "true", "sim")


# ------------------------------------------------------------------ texto
def _fonte(tam, negrito=False):
    nomes = ["DejaVuSans-Bold.ttf" if negrito else "DejaVuSans.ttf",
             "LiberationSans-Bold.ttf" if negrito else "LiberationSans-Regular.ttf",
             "Arial Bold.ttf" if negrito else "Arial.ttf", "arial.ttf"]
    pastas = ["/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/TTF",       # Linux
              "/usr/share/fonts/dejavu", "/usr/share/fonts/truetype/liberation",
              "/System/Library/Fonts/Supplemental", "/Library/Fonts",          # macOS
              os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts"),   # Windows
              ""]
    for p in pastas:
        for n in nomes:
            try:
                return ImageFont.truetype(os.path.join(p, n) if p else n, tam)
            except (OSError, IOError):
                pass
    return ImageFont.load_default()


_cache_fontes = {}


def escrever(img, itens):
    """
    Escreve vários textos de uma vez (com acentos, se o Pillow existir).
    itens: lista de (texto, (x, y), tamanho, cor_bgr, negrito)
    Devolve a nova imagem.
    """
    if Image is None:
        for txt, (x, y), tam, cor, neg in itens:
            t = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
            cv2.putText(img, t, (x, y + tam), cv2.FONT_HERSHEY_SIMPLEX, tam / 30,
                        cor, 2 if neg else 1, cv2.LINE_AA)
        return img
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(pil)
    for txt, (x, y), tam, cor, neg in itens:
        chave = (tam, neg)
        if chave not in _cache_fontes:
            _cache_fontes[chave] = _fonte(tam, neg)
        d.text((x, y), txt, font=_cache_fontes[chave], fill=(cor[2], cor[1], cor[0]))
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)


# ------------------------------------------------------------------ tela
def encaixar(img, larg, alt, fundo=FUNDO):
    """Redimensiona mantendo a proporção e centraliza numa tela larg x alt."""
    h, w = img.shape[:2]
    e = min(larg / w, alt / h)
    nova = cv2.resize(img, (int(w * e), int(h * e)), interpolation=cv2.INTER_AREA if e < 1
                      else cv2.INTER_LINEAR)
    tela = np.full((alt, larg, 3), fundo, np.uint8)
    y0, x0 = (alt - nova.shape[0]) // 2, (larg - nova.shape[1]) // 2
    tela[y0:y0 + nova.shape[0], x0:x0 + nova.shape[1]] = nova
    return tela


def tela(conteudo, titulo, legenda="", canto=""):
    """Monta o quadro final 1280x720: título + conteúdo + legenda."""
    q = np.full((ALT, LARG, 3), FUNDO, np.uint8)
    q[:TOPO] = (70, 45, 20)
    q[TOPO:TOPO + AREA[1]] = encaixar(conteudo, *AREA)
    itens = [(titulo, (20, 14), 24, BRANCO, True)]
    if canto:
        itens.append((canto, (LARG - 20 - 11 * len(canto), 18), 18, (200, 220, 255), False))
    if legenda:
        itens.append((legenda, (20, ALT - RODAPE + 12), 19, (230, 230, 230), False))
    return escrever(q, itens)


def cartao(titulo, linhas, subtitulo=""):
    """Cartão de abertura: título grande e algumas linhas do que observar."""
    q = np.full((ALT, LARG, 3), (60, 38, 18), np.uint8)
    itens = [(titulo, (80, 150), 40, BRANCO, True)]
    if subtitulo:
        itens.append((subtitulo, (80, 210), 24, (200, 220, 255), False))
    for i, l in enumerate(linhas):
        itens.append((l, (80, 290 + 46 * i), 25, (235, 235, 235), False))
    return escrever(q, itens)


def lado_a_lado(imgs, rotulos, cores=None, larg_total=None, espaco=8):
    """Junta imagens da mesma altura lado a lado, com um rótulo em cima de cada."""
    h = max(i.shape[0] for i in imgs)
    duas = any("\n" in r for r in rotulos)     # rótulo de duas linhas
    hf = 62 if duas else 40
    cols = []
    for k, im in enumerate(imgs):
        if im.shape[0] != h:
            im = cv2.resize(im, (int(im.shape[1] * h / im.shape[0]), h))
        faixa = np.full((hf, im.shape[1], 3), (50, 50, 50), np.uint8)
        cor = cores[k] if cores else BRANCO
        l1, _, l2 = rotulos[k].partition("\n")
        itens = [(l1, (10, 8), 20, cor, True)]
        if l2:
            itens.append((l2, (10, 35), 16, (225, 225, 225), False))
        faixa = escrever(faixa, itens)
        cols.append(np.vstack([faixa, im]))
        if k < len(imgs) - 1:
            cols.append(np.full((h + hf, espaco, 3), FUNDO, np.uint8))
    return np.hstack(cols)


# ------------------------------------------------------------------ desenho
def ler_quadros(caminho):
    cap = cv2.VideoCapture(caminho)
    out = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        out.append(f)
    cap.release()
    return out


def trilha(img, pts, cor, esp=2, escala=1.0):
    """Polilinha que ignora pontos NaN (quebra a linha nos buracos)."""
    seg = []
    for p in list(pts) + [None]:
        if p is None or np.isnan(p).any():
            if len(seg) >= 2:
                cv2.polylines(img, [np.int32(np.array(seg) * escala)], False, cor, esp,
                              cv2.LINE_AA)
            seg = []
        else:
            seg.append(p)


def desenhar_resultado(frame, res, traj, escala=2.0, rotulo=None, raio_min=20,
                       max_sem_medicao=30):
    """Desenha o Resultado do rastreador (cores da aula) num quadro ampliado."""
    import copy
    grande = cv2.resize(frame, None, fx=escala, fy=escala, interpolation=cv2.INTER_LINEAR)
    r = copy.copy(res)

    def sc(v):
        return None if v is None else np.asarray(v) * escala
    r.medicao, r.predicao, r.estimativa = sc(res.medicao), sc(res.predicao), sc(res.estimativa)
    r.S = None if res.S is None else res.S * escala ** 2
    r.rejeitadas = [np.asarray(z) * escala for z in res.rejeitadas]
    t = [np.asarray(p) * escala for p in traj] if res.estado != INATIVO else []
    return desenhar(grande, r, t, LIMIAR_GATE_99, max_sem_medicao, rotulo=rotulo,
                    raio_min=raio_min * escala)


# ------------------------------------------------------------------ gravação
class Gravador:
    """Grava quadros 1280x720 a 30 fps. No final converte para H.264 com o
    ffmpeg (se existir), para o vídeo abrir em qualquer player."""

    def __init__(self, caminho):
        self.final = caminho
        self.tmp = caminho[:-4] + "_tmp.mp4"
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        avisar_caminho(caminho)
        self.w = cv2.VideoWriter(self.tmp, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (LARG, ALT))
        self.n = 0

    def add(self, q, repetir=1):
        for _ in range(repetir):
            self.w.write(q)
            self.n += 1

    def pausa(self, q, segundos):
        self.add(q, int(segundos * FPS))

    def fechar(self):
        self.w.release()
        if shutil.which("ffmpeg"):
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", self.tmp, "-c:v", "libx264",
                            "-crf", "23", "-pix_fmt", "yuv420p", self.final], check=True)
            os.remove(self.tmp)
        else:
            print("AVISO: ffmpeg não encontrado; o vídeo fica em mp4v (alguns players não abrem)")
            os.replace(self.tmp, self.final)
        print(f"video: {self.final} ({self.n / FPS:.0f} s)")


def emendar_videos(entradas, saida, recodificar=False):
    """
    Junta vídeos de mesmo formato com o ffmpeg (demuxer concat).
    Os caminhos vão para a lista com barras normais e aspas escapadas, o que
    funciona no Windows (C:/...), no Linux e no macOS, inclusive com espaços.
    """
    if not shutil.which("ffmpeg"):
        print("AVISO: ffmpeg não encontrado; não foi possível criar", saida)
        return False
    lista = saida + ".lista.txt"
    with open(lista, "w", encoding="utf-8") as f:
        for p in entradas:
            p = os.path.abspath(p).replace("\\", "/").replace("'", "'\\''")
            f.write(f"file '{p}'\n")
    cod = (["-c:v", "libx264", "-crf", "21", "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-movflags", "+faststart"] if recodificar else ["-c", "copy"])
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                        "-i", lista] + cod + [saida], check=True)
    finally:
        os.remove(lista)
    return True


def painel_dispersao(pontos, lim, titulo, tam=560, cor=AZUL, circulo=None, unidade="px",
                     subtitulo=""):
    """
    Gráfico de dispersão desenhado com OpenCV (rápido, para vídeo).
    pontos: Nx2 em px (já centrados em 0); lim: meio-lado do gráfico em px.
    circulo: raio (px) de um círculo de referência, desenhado em laranja.
    """
    img = np.full((tam, tam, 3), 250, np.uint8)
    m = 50                                   # margem para os rótulos
    e = (tam - 2 * m) / (2 * lim)            # pixels de tela por px de imagem
    c = tam // 2
    passo = lim / 2
    rot = []
    for k in range(-2, 3):
        v = k * passo
        p = int(c + v * e)
        cv2.line(img, (p, m), (p, tam - m), (215, 215, 215), 1)
        cv2.line(img, (m, p), (tam - m, p), (215, 215, 215), 1)
        txt = f"{v:+.2f}".replace(".", ",") if lim < 1 else f"{v:+.1f}".replace(".", ",")
        rot.append((txt, (p - 22, tam - m + 6), 13, (90, 90, 90), False))
        rot.append((txt, (4, p - 8), 13, (90, 90, 90), False))
    cv2.rectangle(img, (m, m), (tam - m, tam - m), (120, 120, 120), 1)
    if circulo:
        cv2.circle(img, (c, c), int(circulo * e), LARANJA, 2, cv2.LINE_AA)
    for x, y in pontos:
        if np.isnan(x):
            continue
        cv2.circle(img, (int(c + x * e), int(c + y * e)), 3, cor, -1, cv2.LINE_AA)
    rot.append((titulo, (m, 6), 16, (40, 40, 40), True))
    if subtitulo:
        rot.append((subtitulo, (m, 26), 14, (60, 60, 60), False))
    rot.append((f"desvio x ({unidade})", (c - 45, tam - 22), 13, (90, 90, 90), False))
    return escrever(img, rot)


def painel_curvas(series, ymax, titulo, larg=480, alt=600, ymin=0.0, rot_y="",
                  xrot="quadros", linha_h=None, log=False, nx=None):
    """
    Gráfico de linhas desenhado com OpenCV (para vídeo).
    series: lista de (nome, valores 1D, cor_bgr). NaN quebra a linha.
    linha_h: (valor, cor, texto) para uma linha horizontal de referência.
    log: eixo y logarítmico (ymin e ymax > 0).
    nx: número de posições no eixo x (padrão: maior série).
    """
    img = np.full((alt, larg, 3), 250, np.uint8)
    ml, mr, mt, mb = 62, 14, 58, 44
    W, H = larg - ml - mr, alt - mt - mb
    nx = nx or max(len(v) for _, v, _ in series) or 1

    def ty(v):
        if log:
            v = np.log10(np.clip(v, ymin, ymax))
            a, b = np.log10(ymin), np.log10(ymax)
        else:
            a, b = ymin, ymax
        return mt + H - (v - a) / (b - a) * H

    rot = [(titulo, (ml - 50, 8), 16, (40, 40, 40), True)]
    ticks = ([10 ** k for k in range(int(np.ceil(np.log10(ymin))), int(np.floor(np.log10(ymax))) + 1)]
             if log else np.linspace(ymin, ymax, 5))
    for v in ticks:
        y = int(ty(v))
        cv2.line(img, (ml, y), (ml + W, y), (220, 220, 220), 1)
        txt = (f"1e{int(np.log10(v))}" if log else
               (f"{v:.0f}" if ymax >= 10 else f"{v:.1f}").replace(".", ","))
        rot.append((txt, (4, y - 8), 13, (90, 90, 90), False))
    cv2.rectangle(img, (ml, mt), (ml + W, mt + H), (130, 130, 130), 1)
    if linha_h:
        v, cor, txt = linha_h
        y = int(ty(v))
        cv2.line(img, (ml, y), (ml + W, y), cor, 2, cv2.LINE_AA)
        rot.append((txt, (ml + 6, y - 22), 14, cor, True))
    for k, (nome, vals, cor) in enumerate(series):
        vals = np.clip(np.asarray(vals, float), ymin, ymax)
        pts = [(ml + i / max(nx - 1, 1) * W, ty(v)) for i, v in enumerate(vals)]
        seg = []
        for (x, y), v in zip(pts + [(0, 0)], list(vals) + [np.nan]):
            if np.isnan(v):
                if len(seg) >= 2:
                    cv2.polylines(img, [np.int32(seg)], False, cor, 2, cv2.LINE_AA)
                seg = []
            else:
                seg.append((x, y))
        rot.append((nome, (ml + 8 + 150 * k, 32), 14, cor, True))
    rot.append((xrot, (ml + W // 2 - 30, alt - mb + 18), 13, (90, 90, 90), False))
    if rot_y:
        rot.append((rot_y, (4, mt - 22), 13, (90, 90, 90), False))
    return escrever(img, rot)
