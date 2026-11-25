"""
Funções de apoio: abrir vídeo/webcam, rodar o detector em todos os quadros
e rodar o rastreador sobre uma lista de detecções já pronta (os experimentos
usam isso para testar vários Σd sem repetir a segmentação).
"""
import csv
import os

import cv2
import numpy as np

from .detector import DetectorHSV
from .kalman import (modelo_velocidade_constante, modelo_aceleracao_constante,
                     LIMIAR_GATE_99)
from .rastreador import Rastreador


def avisar_caminho(caminho):
    """No Windows o OpenCV não abre/grava vídeos em caminhos com acento ou ç."""
    if os.name == "nt" and not os.path.abspath(caminho).isascii():
        print(f"AVISO: o caminho '{os.path.abspath(caminho)}' tem acento ou caractere especial. "
              "No Windows o OpenCV costuma falhar nesses caminhos; coloque o projeto numa "
              "pasta sem acentos, por exemplo C:\\projetos\\Visao.")


def abrir_fonte(fonte, largura=None, altura=None):
    """fonte: caminho de vídeo ou índice da webcam ("0", "1"...)."""
    if isinstance(fonte, str) and fonte.isdigit():
        cap = cv2.VideoCapture(int(fonte))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, largura or 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, altura or 480)
    else:
        if not os.path.exists(fonte):
            raise FileNotFoundError(fonte)
        avisar_caminho(fonte)
        cap = cv2.VideoCapture(fonte)
    if not cap.isOpened():
        raise RuntimeError(f"nao consegui abrir {fonte}")
    return cap


def fabrica(modelo="cv", sigma_d=None, sigma_m=2.0):
    """Devolve uma função que cria o Modelo pedido ('cv' ou 'ca')."""
    if modelo == "cv":
        sd = 2.0 if sigma_d is None else sigma_d
        return lambda: modelo_velocidade_constante(sd, sigma_m)
    if modelo == "ca":
        sd = 0.2 if sigma_d is None else sigma_d
        return lambda: modelo_aceleracao_constante(sd, sigma_m)
    raise ValueError("modelo deve ser 'cv' ou 'ca'")


def detectar_video(caminho, detector=None):
    """Roda o detector em todos os quadros. Devolve (deteccoes, fps, (w, h))."""
    detector = detector or DetectorHSV()
    cap = abrir_fonte(caminho)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    todas = []
    w = h = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        h, w = frame.shape[:2]
        todas.append(detector.detectar(frame))
    cap.release()
    return todas, fps, (w, h)


def rodar_rastreador(deteccoes, fab, max_sem_medicao=30,
                     quadros_sem_medicao=None, raio_min=20.0,
                     limiar_gate=LIMIAR_GATE_99, frac_area_min=0.5):
    """
    Roda o rastreador sobre detecções já calculadas.
    quadros_sem_medicao: conjunto de índices de quadros em que a medição é
    apagada de propósito (oclusão sintética).
    """
    quadros_sem_medicao = quadros_sem_medicao or set()
    r = Rastreador(fab, max_sem_medicao=max_sem_medicao, raio_min=raio_min,
                   limiar_gate=limiar_gate, frac_area_min=frac_area_min)
    return [r.passo(d, forcar_sem_medicao=(i in quadros_sem_medicao))
            for i, d in enumerate(deteccoes)]


def bruto(deteccoes):
    """Trajetória bruta do detector: maior componente de cada quadro (ou NaN)."""
    out = np.full((len(deteccoes), 2), np.nan)
    for i, d in enumerate(deteccoes):
        if d:
            out[i] = d[0].z
    return out


def serie(resultados, campo):
    """Extrai um campo (medicao, predicao, estimativa) como array Nx2 com NaN."""
    out = np.full((len(resultados), 2), np.nan)
    for i, r in enumerate(resultados):
        v = getattr(r, campo)
        if v is not None and r.estado != "inativo":
            out[i] = v[:2]
    return out


def salvar_csv(resultados, caminho):
    os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        n = max((len(r.estado_vetor) for r in resultados
                 if r.estado_vetor is not None), default=4)
        nomes = ["px", "py", "vx", "vy", "ax", "ay"][:n]
        wr.writerow(["quadro", "estado", "med_x", "med_y", "pred_x", "pred_y",
                     "est_x", "est_y"] + nomes + ["sem_medicao", "d2"])

        def f2(v):
            return ["", ""] if v is None else [f"{v[0]:.3f}", f"{v[1]:.3f}"]
        for r in resultados:
            ev = ([""] * n if r.estado_vetor is None
                  else [f"{v:.4f}" for v in r.estado_vetor])
            wr.writerow([r.quadro, r.estado] + f2(r.medicao) + f2(r.predicao)
                        + f2(r.estimativa) + ev
                        + [r.sem_medicao, "" if r.d2 is None else f"{r.d2:.3f}"])
