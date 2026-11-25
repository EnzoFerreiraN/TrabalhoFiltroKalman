"""
Experimento 7 - Desempenho: quadros por segundo do pipeline completo
(detecção HSV + rastreador + desenho das sobreposições), com cada quadro
redimensionado para 640x480 como pede o enunciado (>= 15 fps).
"""
import glob
import os
import platform
import time

import cv2

from comum import VIDEOS, pasta_saida, tabela_md
from src.detector import DetectorHSV
from src.kalman import LIMIAR_GATE_99
from src.pipeline import fabrica
from src.rastreador import Rastreador
from src.visualizacao import desenhar

saida = pasta_saida("7_desempenho_fps")
md = os.path.join(saida, "tabela.md")
if os.path.exists(md):
    os.remove(md)

linhas = []
for caminho in sorted(glob.glob(os.path.join(VIDEOS, "*.mp4"))):
    for modelo in ("cv", "ca"):
        cap = cv2.VideoCapture(caminho)
        quadros = []
        while True:
            ok, f = cap.read()
            if not ok:
                break
            quadros.append(cv2.resize(f, (640, 480)))
        cap.release()
        det = DetectorHSV()
        r = Rastreador(fabrica(modelo), raio_min=20, frac_area_min=0.5)
        traj = []
        t0 = time.perf_counter()
        for f in quadros:
            res = r.passo(det.detectar(f))
            if res.estimativa is not None:
                traj.append(res.estimativa)
            desenhar(f, res, traj[-200:], LIMIAR_GATE_99, 30)
        dt = time.perf_counter() - t0
        linhas.append([os.path.basename(caminho), modelo.upper(), len(quadros),
                       1000 * dt / len(quadros), len(quadros) / dt])

tabela_md(["video", "modelo", "quadros", "ms por quadro", "fps"], linhas, md,
          f"Desempenho a 640x480 ({platform.processor() or platform.machine()})")

# =========================== figura ===========================
from comum import plt  # noqa: E402
import numpy as np  # noqa: E402

nomes = sorted({l[0][:-4] for l in linhas})
fps_cv = [next(l[4] for l in linhas if l[0][:-4] == n and l[1] == "CV") for n in nomes]
fps_ca = [next(l[4] for l in linhas if l[0][:-4] == n and l[1] == "CA") for n in nomes]
fig, ax = plt.subplots(figsize=(11, 5))
y = np.arange(len(nomes))
ax.barh(y - 0.2, fps_cv, 0.4, label="velocidade constante (CV)", color="tab:orange")
ax.barh(y + 0.2, fps_ca, 0.4, label="aceleração constante (CA)", color="tab:purple")
ax.axvline(15, color="red", lw=2, label="mínimo exigido (15 fps)")
ax.set_yticks(y)
ax.set_yticklabels(nomes)
ax.set_xlabel("quadros por segundo (pipeline completo, 640×480)")
ax.set_title("Desempenho: todos os vídeos ficam muito acima de 15 fps")
ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(saida, "desempenho.png"), dpi=130)
plt.close(fig)

# =========================== vídeo ===========================
from video_util import (gerar_videos, Gravador, tela, lado_a_lado, ler_quadros,  # noqa: E402
                        painel_curvas, escrever, encaixar, LARANJA, VERMELHO)

if gerar_videos():
    g = Gravador(os.path.join(saida, "video_desempenho_fps.mp4"))
    TIT = "Experimento 7 – Desempenho (≥ 15 fps a 640×480)"
    det = DetectorHSV()
    r = Rastreador(fabrica("cv"), raio_min=20, frac_area_min=0.5)
    qs = ler_quadros(os.path.join(VIDEOS, "movimento_mao.mp4"))
    traj, fps_hist, q = [], [], None
    for i, f in enumerate(qs[:420]):
        f640 = encaixar(f, 640, 480, fundo=(0, 0, 0))       # imagem 640x480
        t0 = time.perf_counter()
        res = r.passo(det.detectar(f640))
        if res.estimativa is not None:
            traj.append(res.estimativa)
        img = desenhar(f640, res, traj[-60:], LIMIAR_GATE_99, 30)
        dt = time.perf_counter() - t0
        fps_hist.append(1.0 / dt)
        if i < 90:          # pula o começo sem bola
            continue
        media = len(fps_hist) / sum(1 / v for v in fps_hist)
        graf = painel_curvas([("fps de processamento", fps_hist[-150:], LARANJA)],
                             max(100, 100 * np.ceil(max(fps_hist) / 100)),
                             "quadros por segundo (últimos 150 quadros)", larg=560, alt=420,
                             nx=150, xrot="quadro", linha_h=(15, VERMELHO, "mínimo exigido: 15 fps"))
        faixa = np.full((60, 560, 3), 250, np.uint8)
        faixa = escrever(faixa, [(f"{1000 * dt:.1f} ms neste quadro · média {media:.0f} fps "
                                  f"({media / 15:.0f}× o mínimo)".replace(".", ","),
                                  (14, 18), 18, (40, 40, 40), True)])
        conteudo = lado_a_lado([img, np.vstack([graf, faixa])],
                               [f"quadro processado (640×480) · {i}", "velocidade do programa"])
        q = tela(conteudo, TIT, f"Medido nesta máquina ({platform.machine()}); no notebook de vocês o número muda, mas a folga é grande.")
        g.add(q)
    g.pausa(q, 2)
    g.fechar()
