"""
Rastreador: junta o detector e o filtro de Kalman, quadro a quadro.

Ciclo de cada quadro:
    1. predição do filtro
    2. região de busca (gating): só aceita detecções com distância de
       Mahalanobis² < limiar. A região cresce sozinha quando o filtro fica
       sem medição, porque P (e portanto S) cresce a cada predição.
    3. se houver detecção aceita -> correção; senão o filtro segue
       "no escuro" só com a predição
    4. depois de `max_sem_medicao` quadros seguidos no escuro, a trilha é
       considerada perdida e o filtro é reiniciado na próxima detecção.
"""
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

from .kalman import FiltroKalman, LIMIAR_GATE_99

INATIVO = "inativo"          # ainda não há trilha (bola nunca vista ou perdida)
RASTREANDO = "rastreando"    # houve medição neste quadro
NO_ESCURO = "no_escuro"      # sem medição: só predição


@dataclass
class Resultado:
    quadro: int
    estado: str
    medicao: Optional[np.ndarray] = None       # detecção aceita (azul)
    predicao: Optional[np.ndarray] = None      # x⁻ (vermelho)
    estimativa: Optional[np.ndarray] = None    # x corrigido (laranja)
    estado_vetor: Optional[np.ndarray] = None  # vetor de estado completo
    S: Optional[np.ndarray] = None             # cov. da inovação (região de busca)
    rejeitadas: List[np.ndarray] = field(default_factory=list)
    sem_medicao: int = 0                       # quadros seguidos no escuro
    d2: Optional[float] = None                 # Mahalanobis² da medição aceita
    iniciou: bool = False                      # trilha (re)iniciada neste quadro
    perdeu: bool = False                       # trilha perdida neste quadro
    saiu: bool = False                         # perdida porque saiu do quadro


class Rastreador:
    def __init__(self, fabrica_modelo, max_sem_medicao=30,
                 limiar_gate=LIMIAR_GATE_99, raio_min=0.0, frac_area_min=0.0,
                 limites=None, margem_saida=40):
        """
        fabrica_modelo : função sem argumentos que devolve um Modelo
                         (ex.: lambda: modelo_velocidade_constante(2.0, 2.0))
        limiar_gate    : limiar da distância de Mahalanobis² (9.21 = 99%)
        raio_min       : raio mínimo da região de busca, em pixels. Com Σd
                         muito pequeno a elipse fica minúscula e o filtro
                         rejeitaria a própria bola num movimento brusco;
                         o piso evita isso. 0 = só Mahalanobis.
        frac_area_min  : descarta detecções com área menor que esta fração da
                         área típica da bola (mediana das últimas medições).
                         Quando a bola entra atrás do obstáculo só uma parte
                         dela aparece e o centroide fica "para trás", o que
                         ensina ao filtro uma desaceleração que não existe.
                         0 = desligado.
        limites        : (largura, altura) da imagem. Se informado, a trilha
                         termina quando o filtro está no escuro e a estimativa
                         sai da imagem (mais que margem_saida px): a bola
                         saiu do quadro e não adianta seguir prevendo.
        """
        self.fabrica = fabrica_modelo
        self.max_sem_medicao = max_sem_medicao
        self.limiar_gate = limiar_gate
        self.raio_min = raio_min
        self.frac_area_min = frac_area_min
        self.limites = limites
        self.margem_saida = margem_saida
        self.areas = []          # áreas das últimas medições aceitas
        self.kf = None
        self.sem_medicao = 0
        self.quadro = -1

    @property
    def ativo(self):
        return self.kf is not None

    def _area_ok(self, det):
        if self.frac_area_min <= 0 or len(self.areas) < 5:
            return True
        return det.area >= self.frac_area_min * np.median(self.areas[-15:])

    def _iniciar(self, det, res):
        self.kf = FiltroKalman(self.fabrica(), det.z)
        self.sem_medicao = 0
        self.areas = [det.area]
        res.estado = RASTREANDO
        res.medicao = det.z
        res.estimativa = self.kf.posicao
        res.estado_vetor = self.kf.x.copy()
        res.iniciou = True

    def passo(self, deteccoes, forcar_sem_medicao=False):
        """
        Processa um quadro.
        deteccoes          : lista de Deteccao do detector
        forcar_sem_medicao : ignora as detecções (usado nos experimentos de
                             oclusão sintética)
        """
        self.quadro += 1
        res = Resultado(quadro=self.quadro, estado=INATIVO)
        if forcar_sem_medicao:
            deteccoes = []

        # ---- sem trilha: inicia com a maior detecção ----
        if not self.ativo:
            if deteccoes:
                self._iniciar(deteccoes[0], res)
            return res

        # ---- 1. predição ----
        res.predicao = self.kf.predizer()[:2]
        res.S = self.kf.cov_inovacao()

        # ---- 2. gating: a candidata mais próxima dentro da região ----
        melhor, melhor_d2 = None, np.inf
        for det in deteccoes:
            d2 = self.kf.mahalanobis2(det.z)
            dist = np.linalg.norm(det.z - res.predicao)
            dentro = d2 < self.limiar_gate or dist < self.raio_min
            if dentro and self._area_ok(det) and d2 < melhor_d2:
                melhor, melhor_d2 = det, d2
        res.rejeitadas = [d.z for d in deteccoes if d is not melhor]

        # ---- 3. correção ou "no escuro" ----
        if melhor is not None:
            self.kf.corrigir(melhor.z)
            self.sem_medicao = 0
            self.areas.append(melhor.area)
            res.estado = RASTREANDO
            res.medicao = melhor.z
            res.d2 = melhor_d2
        else:
            self.sem_medicao += 1
            res.estado = NO_ESCURO

        res.estimativa = self.kf.posicao
        res.estado_vetor = self.kf.x.copy()
        res.sem_medicao = self.sem_medicao

        # ---- 4. trilha perdida ----
        if self.limites is not None and res.estado == NO_ESCURO:
            w, h = self.limites
            px, py = res.estimativa
            m = self.margem_saida
            res.saiu = not (-m <= px <= w + m and -m <= py <= h + m)
        if self.sem_medicao > self.max_sem_medicao or res.saiu:
            self.kf = None
            res.perdeu = True
            res.estado = INATIVO
        return res
