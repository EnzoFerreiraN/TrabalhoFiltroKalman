"""
Experimento 2 - Trajetória bruta do detector x trajetória filtrada.

(a) Sensor real: detector HSV como está.
(b) Sensor degradado: ruído gaussiano de 3 px somado a cada medição. A
    referência passa a ser a detecção limpa, então dá para medir de verdade
    quanto ruído o filtro remove.
(c) Variância da posição com a bola parada.

Vídeos: movimento_mao (movimento irregular com a mão) e
oclusao_pequeno_1 (bola rolando, movimento suave).
Modelo: velocidade constante, Σd intermediário.
"""
import os

import numpy as np

from comum import (deteccoes, bruto, referencia, pasta_saida, tabela_md, plt,
                   com_ruido, erro_medio, rugosidade, atraso, rejeicoes_indevidas,
                   SIGMA_D_CV, SIGMA_M)
from src.pipeline import rodar_rastreador, fabrica, serie

saida = pasta_saida("2_bruto_vs_filtrado")
md = os.path.join(saida, "tabela.md")
if os.path.exists(md):
    os.remove(md)

VIDEOS = ["movimento_mao", "oclusao_pequeno_1"]
RUIDO = 3.0
SD = SIGMA_D_CV["intermediario"]
CAB = ["video", "sensor", "trajetoria", "erro medio (px)", "rugosidade (px/q^2)",
       "atraso (quadros)", "bola rejeitada (quadros)"]


def rodar(dets, sigma_m):
    res = rodar_rastreador(dets, fabrica("cv", SD, sigma_m))
    f = serie(res, "estimativa")
    f[[r.estado != "rastreando" for r in res]] = np.nan  # só quadros com medição
    return res, f


linhas, guardado = [], {}
for v in VIDEOS:
    d, _, _ = deteccoes(v)
    b = bruto(d)
    ref, tipo = referencia(v, b)
    # (a) sensor real
    res, f = rodar(d, SIGMA_M)
    linhas += [[v, "real", "bruta", erro_medio(b, ref), rugosidade(b), atraso(b, ref), "-"],
               [v, "real", "filtrada", erro_medio(f, ref), rugosidade(f), atraso(f, ref),
                rejeicoes_indevidas(res, d)]]
    # (b) sensor degradado: referência = detecção limpa
    dr = com_ruido(d, RUIDO)
    br = bruto(dr)
    resr, fr = rodar(dr, RUIDO)
    linhas += [[v, f"+{RUIDO:.0f}px", "bruta", erro_medio(br, b), rugosidade(br), atraso(br, b), "-"],
               [v, f"+{RUIDO:.0f}px", "filtrada", erro_medio(fr, b), rugosidade(fr), atraso(fr, b),
                rejeicoes_indevidas(resr, dr)]]
    guardado[v] = (b, f, br, fr, ref)

tabela_md(CAB, linhas, md, "Bruta x filtrada (sensor real: referencia = "
          + tipo + "; sensor degradado: referencia = deteccao limpa)")

# (c) bola parada
dp, _, _ = deteccoes("bola_parada")
lc = []
for nome, dets, sm in [("real", dp, SIGMA_M),
                       (f"+{RUIDO:.0f}px", com_ruido(dp, RUIDO), RUIDO)]:
    bp = bruto(dets)[20:]
    fp = serie(rodar_rastreador(dets, fabrica("cv", SD, sm)), "estimativa")[20:]
    lc += [[nome, "bruta", np.nanvar(bp[:, 0]), np.nanvar(bp[:, 1])],
           [nome, "filtrada", np.nanvar(fp[:, 0]), np.nanvar(fp[:, 1])]]
tabela_md(["sensor", "trajetoria", "var x (px^2)", "var y (px^2)"], lc, md,
          "Bola parada (bola_parada) - variancia da posicao")

# ---------------- figuras ----------------
for v, (b, f, br, fr, ref) in guardado.items():
    t = np.arange(len(b))
    fig, ax = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
    for i, eixo in enumerate("xy"):
        ax[i].plot(t, br[:, i], ".", ms=3, color="tab:blue", alpha=.6,
                   label=f"bruta (+{RUIDO:.0f} px)")
        ax[i].plot(t, fr[:, i], "-", lw=1.4, color="tab:orange", label="filtrada")
        ax[i].plot(t, b[:, i], "-", lw=.8, color="k", label="deteccao limpa")
        ax[i].set_ylabel(f"{eixo} (px)")
    ax[0].legend(ncol=3)
    ax[1].set_xlabel("quadro")
    fig.suptitle(f"Bruta x filtrada - {v} - sensor degradado")
    fig.tight_layout()
    fig.savefig(os.path.join(saida, f"{v}_tempo.png"), dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(9, 7))
    for k, (tb, tf, tit) in enumerate([(b, f, "sensor real"),
                                        (br, fr, f"sensor +{RUIDO:.0f} px")]):
        ax[k].plot(tb[:, 0], tb[:, 1], ".", ms=2, color="tab:blue", label="bruta")
        ax[k].plot(tf[:, 0], tf[:, 1], "-", lw=1, color="tab:orange", label="filtrada")
        ax[k].invert_yaxis()
        ax[k].set_aspect("equal")
        ax[k].set_title(tit)
    ax[0].legend()
    fig.suptitle(v)
    fig.tight_layout()
    fig.savefig(os.path.join(saida, f"{v}_xy.png"), dpi=130)
    plt.close(fig)
print("figuras e tabela em", saida)

# =========================== vídeo ===========================
from video_util import (gerar_videos, Gravador, tela, lado_a_lado, ler_quadros,
                        painel_curvas, trilha, AZUL, PRETO, LARANJA)
from comum import VIDEOS as PASTA_VIDEOS
import cv2

if gerar_videos():
    g = Gravador(os.path.join(saida, "video_bruto_vs_filtrado.mp4"))
    TIT = "Experimento 2 – Trajetória bruta × filtrada"
    RASTRO = 25
    partes = [("movimento_mao", range(120, 480), 1, "bola movida com a mão"),
              ("oclusao_pequeno_1", range(61, 156), 2, "bola rolando (câmera lenta 2x)")]
    for k, (v, quadros, lento, desc) in enumerate(partes):
        qs = ler_quadros(os.path.join(PASTA_VIDEOS, v + ".mp4"))
        b, f, br, fr, ref = guardado[v]
        eb = np.linalg.norm(br - b, axis=1)
        ef = np.linalg.norm(fr - b, axis=1)

        def media_movel(e, n=15):
            out = np.full_like(e, np.nan)
            for j in range(len(e)):
                w = e[max(0, j - n + 1):j + 1]
                if np.isfinite(w).sum() >= 3:
                    out[j] = np.nanmean(w)
            return out
        mmb, mmf = media_movel(eb), media_movel(ef)
        ini = quadros[0]
        for i in quadros:
            a = max(ini, i - RASTRO)
            esq, meio = qs[i].copy(), qs[i].copy()
            for im in (esq, meio):
                trilha(im, b[a:i + 1], PRETO, 1)
            trilha(esq, br[a:i + 1], AZUL, 1)
            for p in br[a:i + 1]:
                if not np.isnan(p).any():
                    cv2.circle(esq, (int(p[0]), int(p[1])), 3, AZUL, -1, cv2.LINE_AA)
            trilha(meio, fr[a:i + 1], LARANJA, 3)
            if not np.isnan(fr[i]).any():
                cv2.circle(meio, (int(fr[i][0]), int(fr[i][1])), 7, LARANJA, 2, cv2.LINE_AA)
            mb, mf = np.nanmean(eb[ini:i + 1]), np.nanmean(ef[ini:i + 1])
            j0 = max(ini, i - 90)
            graf = painel_curvas([("bruta", mmb[j0:i + 1], AZUL),
                                  ("filtrada", mmf[j0:i + 1], LARANJA)],
                                 6, "erro médio móvel (15 quadros), em px", larg=440, alt=600,
                                 nx=91, xrot="últimos 90 quadros")
            conteudo = lado_a_lado([cv2.resize(esq, (338, 600)), cv2.resize(meio, (338, 600)), graf],
                                   [f"detector +{RUIDO:.0f} px · erro {mb:.1f}".replace(".", ","),
                                    f"Kalman · erro {mf:.1f}".replace(".", ","), "erro (média móvel)"],
                                   cores=[(255, 160, 120), (80, 180, 255), (255, 255, 255)])
            nums = f"bruta {mb:.2f} px, filtrada {mf:.2f} px".replace(".", ",")
            q = tela(conteudo, TIT, f"{v}: {desc}. Erro médio até aqui: {nums}.",
                     f"parte {k + 1}/2")
            g.add(q, lento)
        g.pausa(q, 1.5)
    g.fechar()
