"""
Detector (o "sensor" do sistema).

Segmentação por cor no espaço HSV + operações morfológicas + componentes
conectados. Cada componente verde com área suficiente vira uma "detecção"
(medição candidata) com o seu centroide (px, py).

O detector devolve TODAS as candidatas, ordenadas da maior para a menor.
Quem decide qual delas é a bola é o rastreador, usando a região de busca
(gating) derivada da covariância prevista pelo filtro de Kalman.
"""
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class Deteccao:
    x: float          # centroide (pixels)
    y: float
    area: float       # área do componente conectado (pixels)
    bbox: tuple       # (x, y, largura, altura)

    @property
    def z(self):
        """Vetor de medição z = [px, py]^T."""
        return np.array([self.x, self.y], dtype=float)


class DetectorHSV:
    def __init__(self,
                 hsv_min=(35, 80, 60),
                 hsv_max=(85, 255, 255),
                 tam_abertura=3,
                 tam_fechamento=7,
                 area_min=20):
        """
        hsv_min, hsv_max : limites da cor no espaço HSV do OpenCV
                           (H vai de 0 a 179; verde fica por volta de 35-85).
        tam_abertura     : elemento estruturante da abertura (remove pontinhos).
        tam_fechamento   : elemento estruturante do fechamento (tapa buracos,
                           como o reflexo de luz em cima da bola).
        area_min         : componentes menores que isso são descartados.
        """
        self.hsv_min = np.array(hsv_min, dtype=np.uint8)
        self.hsv_max = np.array(hsv_max, dtype=np.uint8)
        self.k_abertura = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (tam_abertura, tam_abertura))
        self.k_fechamento = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (tam_fechamento, tam_fechamento))
        self.area_min = area_min

    def mascara(self, frame_bgr):
        """Máscara binária da cor, já com abertura e fechamento."""
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        m = cv2.inRange(hsv, self.hsv_min, self.hsv_max)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, self.k_abertura)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, self.k_fechamento)
        return m

    def detectar(self, frame_bgr):
        """Lista de Deteccao, da maior área para a menor (pode ser vazia)."""
        m = self.mascara(frame_bgr)
        n, _, stats, centroides = cv2.connectedComponentsWithStats(m)
        dets = []
        for i in range(1, n):  # rótulo 0 é o fundo
            area = stats[i, cv2.CC_STAT_AREA]
            if area < self.area_min:
                continue
            x, y, w, h = stats[i, :4]
            cx, cy = centroides[i]
            dets.append(Deteccao(float(cx), float(cy), float(area),
                                 (int(x), int(y), int(w), int(h))))
        dets.sort(key=lambda d: d.area, reverse=True)
        return dets
