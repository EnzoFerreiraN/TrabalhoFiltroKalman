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


linhas = []
for video in ["movimento_mao", "oclusao_grande", "lancamento_horizontal"]:
    d, _, _ = deteccoes(video)
    for nome, fab in [("CV", fabrica("cv", SIGMA_D_CV["intermediario"], SIGMA_M)),
                      ("CA", fabrica("ca", SIGMA_D_CA, SIGMA_M))]:
        # sequência de medições aceitas pelo rastreador (None = sem medição)
        res = rodar_rastreador(d, fab)
        nosso = ocv = None
        dx = dp = 0.0
        n = 0
        for r in res:
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
            dx = max(dx, np.abs(nosso.x - xo).max() / (1 + np.abs(xo).max()))
            dp = max(dp, np.abs(nosso.P - Po).max() / (1 + np.abs(Po).max()))
            n += 1
            if r.perdeu:
                nosso = ocv = None
        linhas.append([video, nome, n, f"{dx:.2e}", f"{dp:.2e}",
                       "OK" if dx < 1e-9 and dp < 1e-9 else "DIFERENTE"])

tabela_md(["video", "modelo", "quadros comparados", "dif. relativa max em x",
           "dif. relativa max em P", "resultado (tol. 1e-9)"], linhas, md,
          "Validacao contra cv2.KalmanFilter")
