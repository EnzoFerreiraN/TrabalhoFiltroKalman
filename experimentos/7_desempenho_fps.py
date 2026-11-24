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
