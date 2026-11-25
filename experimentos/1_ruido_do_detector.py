"""
Experimento 1 - Ruído do detector (de onde vem o valor de Σm).

1) Bola parada (bola_parada): a variação do centroide é puro ruído
   do detector -> limite INFERIOR de Σm (câmera parada, sem borrão).
2) Bola em movimento (movimento_mao): resíduo entre a trajetória
   bruta e uma versão suavizada -> ruído "real" durante o movimento
   (borrão, oclusão parcial pela mão, compressão do vídeo).
"""
import os

import numpy as np

from comum import (deteccoes, bruto, referencia, pasta_saida, tabela_md, plt,
                   SIGMA_M)

saida = pasta_saida("1_ruido_do_detector")
md = os.path.join(saida, "tabela.md")
if os.path.exists(md):
    os.remove(md)

# 1) parada
d, _, _ = deteccoes("bola_parada")
b = bruto(d)
b = b[~np.isnan(b).any(axis=1)]
std_parada = b.std(axis=0)

# 2) movimento
d2, _, _ = deteccoes("movimento_mao")
b2 = bruto(d2)
ref, _ = referencia("movimento_mao", b2)  # usa só a suavização
res = b2 - ref
res = res[~np.isnan(res).any(axis=1)]
std_mov = res.std(axis=0)

tabela_md(["situacao", "desvio x (px)", "desvio y (px)", "n quadros"],
          [["bola parada", std_parada[0], std_parada[1], len(b)],
           ["bola em movimento (residuo)", std_mov[0], std_mov[1], len(res)]],
          md, "Ruido de medicao do detector")

with open(md, "a", encoding="utf-8") as f:
    f.write(f"Valor adotado: sigma_m = {SIGMA_M} px (Sm = sigma_m^2 * I).\n\n"
            "A bola parada da o limite inferior. Em movimento o residuo e "
            "maior, e ainda subestima o ruido real, porque a suavizacao "
            "absorve parte dele e porque os quadros com oclusao parcial "
            "(centroide deslocado) sao poucos. Adotamos uma margem de ~4x o "
            "residuo. O comportamento do filtro depende da razao Sd/Sm, que "
            "e variada no experimento 3.\n")

fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ax[0].scatter(b[:, 0] - b[:, 0].mean(), b[:, 1] - b[:, 1].mean(), s=4)
ax[0].set_title("Bola parada: centroide - media (px)")
ax[0].set_aspect("equal")
ax[1].hist(res[:, 0], 60, alpha=.6, label="x")
ax[1].hist(res[:, 1], 60, alpha=.6, label="y")
ax[1].set_title("Bola em movimento: residuo bruto - suavizado (px)")
ax[1].legend()
fig.tight_layout()
fig.savefig(os.path.join(saida, "sigma_m.png"), dpi=130)
print("figuras e tabela em", saida)

# =========================== vídeo ===========================
from video_util import (gerar_videos, Gravador, tela, lado_a_lado, escrever,
                        ler_quadros, painel_dispersao, trilha, AZUL, PRETO, LARANJA)
from comum import VIDEOS
import cv2

if gerar_videos():
    g = Gravador(os.path.join(saida, "video_ruido_do_detector.mp4"))
    TIT = "Experimento 1 – Ruído do detector (Σm)"

    # ---- parte 1: bola parada
    qs = ler_quadros(os.path.join(VIDEOS, "bola_parada.mp4"))
    bp = bruto(d)
    media = np.nanmean(bp, axis=0)
    for i, q in enumerate(qs):
        if i % 2:          # metade dos quadros basta (vídeo mais curto)
            continue
        im = q.copy()
        if not np.isnan(bp[i]).any():
            x, y = bp[i]
            cv2.circle(im, (int(x), int(y)), 4, AZUL, -1, cv2.LINE_AA)
            # zoom 6x em volta da bola no canto do quadro
            x0, y0 = int(media[0]) - 30, int(media[1]) - 30
            z = cv2.resize(q[y0:y0 + 60, x0:x0 + 60], (180, 180), interpolation=cv2.INTER_NEAREST)
            cx, cy = (x - x0) * 3, (y - y0) * 3
            cv2.drawMarker(z, (int(cx), int(cy)), AZUL, cv2.MARKER_CROSS, 30, 2)
            im[10:190, im.shape[1] - 190:im.shape[1] - 10] = z
        pts = bp[:i + 1] - media
        dp = np.nanstd(pts, axis=0) if i > 2 else (0, 0)
        disp = painel_dispersao(pts, 0.25, "centroide − média (bola parada)",
                                subtitulo=f"desvio: x {dp[0]:.2f} px · y {dp[1]:.2f} px".replace(".", ","))
        conteudo = lado_a_lado([cv2.resize(im, (315, 560)), disp],
                               ["quadro %d" % i, "dispersão ampliada (±0,25 px)"])
        g.add(tela(conteudo, TIT, "Parada, o centroide varia só alguns centésimos de pixel.",
                   "parte 1/2"))

    # ---- parte 2: bola em movimento
    qs = ler_quadros(os.path.join(VIDEOS, "movimento_mao.mp4"))
    resid = b2 - ref
    for i in range(150, 450):
        im = qs[i].copy()
        trilha(im, ref[max(0, i - 40):i + 1], PRETO, 1)
        if not np.isnan(b2[i]).any():
            cv2.circle(im, (int(b2[i][0]), int(b2[i][1])), 5, AZUL, -1, cv2.LINE_AA)
        pts = resid[150:i + 1]
        dp = np.nanstd(pts, axis=0)
        disp = painel_dispersao(pts, 2.5, "medição − trajetória suavizada (em movimento)",
                                circulo=SIGMA_M,
                                subtitulo=f"desvio: x {dp[0]:.2f} px · y {dp[1]:.2f} px".replace(".", ","))
        conteudo = lado_a_lado([cv2.resize(im, (315, 560)), disp],
                               ["quadro %d" % i, "dispersão (±2,5 px)"])
        g.add(tela(conteudo, TIT, f"Em movimento o ruído cresce; o círculo laranja é σm = {SIGMA_M:.0f} px, a margem adotada.",
                   "parte 2/2"))
    g.pausa(tela(conteudo, TIT, f"Em movimento o ruído cresce; o círculo laranja é σm = {SIGMA_M:.0f} px, a margem adotada.",
                 "parte 2/2"), 2)
    g.fechar()
