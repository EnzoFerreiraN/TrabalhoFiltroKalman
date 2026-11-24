"""
Sobreposições no vídeo, com o código de cores da aula:
    medição            -> azul
    predição           -> vermelho
    estimativa corrig. -> laranja
Também desenha a região de busca (elipse derivada de S), a trajetória
estimada e um aviso quando o filtro está "no escuro" (sem medição).
"""
import cv2
import numpy as np

from .rastreador import NO_ESCURO, INATIVO

# Cores em BGR (OpenCV)
AZUL = (255, 0, 0)
VERMELHO = (0, 0, 255)
LARANJA = (0, 140, 255)
CINZA = (150, 150, 150)
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)

FONTE = cv2.FONT_HERSHEY_SIMPLEX


def _pt(v):
    return int(round(v[0])), int(round(v[1]))


def desenhar_elipse_busca(img, centro, S, limiar, cor=VERMELHO):
    """Elipse {z : (z-c)ᵀ S⁻¹ (z-c) = limiar} -> eixos = sqrt(autovalor·limiar)."""
    autoval, autovet = np.linalg.eigh(S)
    autoval = np.maximum(autoval, 1e-9)
    eixos = np.sqrt(autoval * limiar)
    ang = np.degrees(np.arctan2(autovet[1, 1], autovet[0, 1]))
    eixos_int = (int(min(eixos[1], 5000)), int(min(eixos[0], 5000)))
    cv2.ellipse(img, _pt(centro), eixos_int, ang, 0, 360, cor, 1, cv2.LINE_AA)


def _texto(img, txt, org, escala=0.45, cor=BRANCO, esp=1):
    cv2.putText(img, txt, org, FONTE, escala, PRETO, esp + 2, cv2.LINE_AA)
    cv2.putText(img, txt, org, FONTE, escala, cor, esp, cv2.LINE_AA)


def desenhar(frame, res, trajetoria, limiar_gate, max_sem_medicao,
             fps=None, rotulo=None, raio_min=0):
    """
    frame      : imagem BGR (é copiada)
    res        : Resultado do Rastreador para este quadro
    trajetoria : lista de estimativas (laranja) da trilha atual
    """
    img = frame.copy()
    h, w = img.shape[:2]

    # trajetória estimada
    if len(trajetoria) >= 2:
        pts = np.array([_pt(p) for p in trajetoria], np.int32)
        cv2.polylines(img, [pts], False, LARANJA, 2, cv2.LINE_AA)

    # região de busca
    if res.S is not None and res.predicao is not None:
        desenhar_elipse_busca(img, res.predicao, res.S, limiar_gate)
        if raio_min > 0:  # piso da região de busca (círculo tracejado claro)
            cv2.circle(img, _pt(res.predicao), int(raio_min), (180, 180, 255),
                       1, cv2.LINE_AA)

    # detecções rejeitadas pelo gating (medições espúrias)
    for z in res.rejeitadas:
        p = _pt(z)
        cv2.drawMarker(img, p, CINZA, cv2.MARKER_TILTED_CROSS, 12, 2)

    # predição (vermelho), medição (azul), estimativa (laranja)
    if res.predicao is not None:
        cv2.drawMarker(img, _pt(res.predicao), VERMELHO, cv2.MARKER_CROSS,
                       14, 2, cv2.LINE_AA)
    if res.medicao is not None:
        cv2.circle(img, _pt(res.medicao), 5, AZUL, -1, cv2.LINE_AA)
    if res.estimativa is not None and res.estado != INATIVO:
        cv2.circle(img, _pt(res.estimativa), 8, LARANJA, 2, cv2.LINE_AA)

    # aviso "no escuro"
    if res.estado == NO_ESCURO:
        cv2.rectangle(img, (0, 0), (w - 1, h - 1), VERMELHO, 6)
        _texto(img, f"NO ESCURO: sem medicao {res.sem_medicao}/{max_sem_medicao}",
               (10, 50), 0.5, VERMELHO, 1)
    elif res.saiu:
        _texto(img, "SAIU DO QUADRO - fim da trilha", (10, 50), 0.5, VERMELHO)
    elif res.perdeu:
        _texto(img, "TRILHA PERDIDA - reiniciando", (10, 50), 0.5, VERMELHO)

    # legenda
    y0 = h - 12
    _texto(img, "medicao", (10, y0), 0.42, AZUL)
    _texto(img, "predicao", (80, y0), 0.42, VERMELHO)
    _texto(img, "estimativa", (160, y0), 0.42, LARANJA)

    # cabeçalho
    cab = f"quadro {res.quadro}"
    if fps is not None:
        cab += f" | {fps:.0f} fps"
    if rotulo:
        cab = rotulo + " | " + cab
    _texto(img, cab, (10, 22), 0.45)
    return img
