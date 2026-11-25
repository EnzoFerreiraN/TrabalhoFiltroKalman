"""
Experimento 6 - Validação: nosso filtro de Kalman dá o mesmo resultado
que o cv2.KalmanFilter?

O enunciado permite usar cv2.KalmanFilter só para validar: os resultados
devem coincidir. Aqui as duas implementações recebem exatamente as mesmas
matrizes (D, M, Σd, Σm), o mesmo estado inicial e a mesma sequência de
medições (com os quadros sem medição), e comparamos estado e covariância
quadro a quadro.
"""
import os

import cv2
import numpy as np

from comum import deteccoes, pasta_saida, tabela_md, SIGMA_D_CA, SIGMA_D_CV, SIGMA_M
from src.kalman import FiltroKalman
from src.pipeline import rodar_rastreador, fabrica

saida = pasta_saida("6_validacao_opencv")
md = os.path.join(saida, "tabela.md")
if os.path.exists(md):
    os.remove(md)


def kf_opencv(mod, z0):
    n = mod.dim
    kf = cv2.KalmanFilter(n, 2, 0, cv2.CV_64F)
    kf.transitionMatrix = mod.D.copy()
    kf.measurementMatrix = mod.M.copy()
    kf.processNoiseCov = mod.Sd.copy()
    kf.measurementNoiseCov = mod.Sm.copy()
    x0 = np.zeros((n, 1))
    x0[:2, 0] = z0
    kf.statePost = x0
    kf.errorCovPost = np.diag(mod.P0_diag).astype(np.float64)
    return kf


linhas, registro = [], {}
for video in ["movimento_mao", "oclusao_grande", "lancamento_horizontal"]:
    d, _, _ = deteccoes(video)
    for nome, fab in [("CV", fabrica("cv", SIGMA_D_CV["intermediario"], SIGMA_M)),
                      ("CA", fabrica("ca", SIGMA_D_CA, SIGMA_M))]:
        # sequência de medições aceitas pelo rastreador (None = sem medição)
        res = rodar_rastreador(d, fab)
        reg = {"nosso": np.full((len(res), 2), np.nan), "ocv": np.full((len(res), 2), np.nan),
               "dx": np.full(len(res), np.nan), "dp": np.full(len(res), np.nan)}
        registro[(video, nome)] = reg
        nosso = ocv = None
        dx = dp = 0.0
        n = 0
        for i, r in enumerate(res):
            if r.iniciou:
                mod = fab()
                nosso = FiltroKalman(mod, r.medicao)
                ocv = kf_opencv(mod, r.medicao)
                continue
            if nosso is None or r.predicao is None:
                if r.perdeu:
                    nosso = ocv = None
                continue
            nosso.predizer()
            ocv.predict()
            if r.medicao is not None:
                nosso.corrigir(r.medicao)
                ocv.correct(r.medicao.reshape(2, 1).astype(np.float64))
            # diferença relativa (P chega a valores grandes no escuro)
            xo, Po = ocv.statePost.ravel(), ocv.errorCovPost
            rx = np.abs(nosso.x - xo).max() / (1 + np.abs(xo).max())
            rp = np.abs(nosso.P - Po).max() / (1 + np.abs(Po).max())
            dx, dp = max(dx, rx), max(dp, rp)
            reg["nosso"][i], reg["ocv"][i] = nosso.x[:2], xo[:2]
            reg["dx"][i], reg["dp"][i] = rx, rp
            n += 1
            if r.perdeu:
                nosso = ocv = None
        linhas.append([video, nome, n, f"{dx:.2e}", f"{dp:.2e}",
                       "OK" if dx < 1e-9 and dp < 1e-9 else "DIFERENTE"])

tabela_md(["video", "modelo", "quadros comparados", "dif. relativa max em x",
           "dif. relativa max em P", "resultado (tol. 1e-9)"], linhas, md,
          "Validacao contra cv2.KalmanFilter")

# =========================== figura ===========================
from comum import plt  # noqa: E402

fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
r = registro[("oclusao_grande", "CV")]
t = np.arange(len(r["nosso"]))
ax[0].plot(t, r["nosso"][:, 1], "-", color="tab:orange", lw=3, label="nossa implementação")
ax[0].plot(t, r["ocv"][:, 1], "--", color="tab:green", lw=1.5, label="cv2.KalmanFilter")
ax[0].set_xlim(90, 175)
ax[0].invert_yaxis()
ax[0].set_xlabel("quadro")
ax[0].set_ylabel("y estimado (px)")
ax[0].set_title("oclusao_grande (CV): as duas curvas se sobrepõem")
ax[0].legend()
for (v, n), rr in registro.items():
    ax[1].semilogy(np.where(rr["dx"] > 0, rr["dx"], 1e-18), ".", ms=2, label=f"{v} {n}")
ax[1].axhline(1e-9, color="r", lw=1.5, label="tolerância 1e-9")
ax[1].set_ylim(1e-18, 1e-6)
ax[1].set_xlabel("quadro")
ax[1].set_ylabel("diferença relativa no estado\n(1e-18 = idênticos)")
ax[1].set_title("Diferença em cada quadro (escala log)")
ax[1].legend(fontsize=7, ncol=2)
fig.tight_layout()
fig.savefig(os.path.join(saida, "validacao.png"), dpi=130)
plt.close(fig)

# =========================== vídeo ===========================
from video_util import (gerar_videos, Gravador, tela, lado_a_lado, ler_quadros,  # noqa: E402
                        painel_curvas, escrever, trilha, LARANJA, VERDE, VERMELHO)
from comum import VIDEOS as PASTA_VIDEOS  # noqa: E402

if gerar_videos():
    g = Gravador(os.path.join(saida, "video_validacao_opencv.mp4"))
    TIT = "Experimento 6 – Validação com o cv2.KalmanFilter"
    r = registro[("oclusao_grande", "CV")]
    qs = ler_quadros(os.path.join(PASTA_VIDEOS, "oclusao_grande.mp4"))
    ini, fim = 94, 172
    for i in range(ini, fim + 1):
        im = cv2.resize(qs[i], None, fx=1.6, fy=1.6)
        trilha(im, r["nosso"][ini:i + 1], LARANJA, 5, 1.6)
        trilha(im, r["ocv"][ini:i + 1], VERDE, 1, 1.6)
        if not np.isnan(r["nosso"][i]).any():
            p, o = r["nosso"][i] * 1.6, r["ocv"][i] * 1.6
            cv2.circle(im, (int(p[0]), int(p[1])), 14, LARANJA, 3, cv2.LINE_AA)
            cv2.drawMarker(im, (int(o[0]), int(o[1])), VERDE, cv2.MARKER_CROSS, 22, 2)
        faixa = np.full((70, 520, 3), 250, np.uint8)
        if not np.isnan(r["nosso"][i]).any():
            faixa = escrever(faixa, [
                (f"nosso:   x = {r['nosso'][i][0]:.6f}   y = {r['nosso'][i][1]:.6f}", (14, 10), 17, (0, 110, 230), True),
                (f"OpenCV: x = {r['ocv'][i][0]:.6f}   y = {r['ocv'][i][1]:.6f}", (14, 38), 17, (20, 140, 20), True)])
        dx = np.where(r["dx"] > 0, r["dx"], 1e-17)
        graf = painel_curvas([("diferença relativa (estado)", dx[ini:i + 1], VERMELHO)], 1e-6,
                             "nosso − OpenCV, a cada quadro", larg=520, alt=570, ymin=1e-17,
                             log=True, nx=fim - ini + 1, xrot="quadro",
                             linha_h=(1e-9, (0, 0, 200), "tolerância 1e-9"))
        graf = np.vstack([graf, faixa])
        conteudo = lado_a_lado([cv2.resize(im, (360, 640)), graf],
                               [f"oclusao_grande · quadro {i}", "diferença (escala log)"])
        q = tela(conteudo, TIT, "As estimativas coincidem até a 6ª casa decimal; a diferença é só arredondamento (≈1e-15).",
                 "câmera lenta 2x")
        g.add(q, 2)
    g.pausa(q, 2)
    g.fechar()
