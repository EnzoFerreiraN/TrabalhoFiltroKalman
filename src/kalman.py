"""
Filtro de Kalman implementado pela equipe (NumPy puro).

Notação da aula:
    modelo dinâmico     x_k = D x_{k-1} + w_k ,   w_k ~ N(0, Σd)
    modelo de medição   z_k = M x_k     + v_k ,   v_k ~ N(0, Σm)

Predição:
    x⁻ = D x
    P⁻ = D P Dᵀ + Σd
Correção:
    S  = M P⁻ Mᵀ + Σm            (covariância da inovação)
    K  = P⁻ Mᵀ S⁻¹               (ganho de Kalman)
    x  = x⁻ + K (z − M x⁻)
    P  = (I − K M) P⁻

A unidade de tempo é o QUADRO (dt = 1): posições em pixels, velocidades em
pixels/quadro e acelerações em pixels/quadro². Para converter para segundos,
multiplique a velocidade pelo fps e a aceleração por fps².
"""
from dataclasses import dataclass

import numpy as np

# Limiar da distância de Mahalanobis ao quadrado para 2 graus de liberdade
# (qui-quadrado): 9.21 -> 99% das medições verdadeiras caem dentro da região.
LIMIAR_GATE_99 = 9.21


# --------------------------------------------------------------------------
# Modelos dinâmicos
# --------------------------------------------------------------------------
@dataclass
class Modelo:
    nome: str
    D: np.ndarray        # matriz de transição de estado
    M: np.ndarray        # matriz de medição
    Sd: np.ndarray       # Σd: covariância do ruído do processo (modelo)
    Sm: np.ndarray       # Σm: covariância do ruído de medição (detector)
    P0_diag: np.ndarray  # variâncias iniciais do estado

    @property
    def dim(self):
        return self.D.shape[0]


def _por_eixo(A1):
    """
    Monta a matriz para (x, y) a partir da matriz de um eixo só.
    Estado ordenado como [px, py, vx, vy, (ax, ay)] -> kron(A1, I2).
    """
    return np.kron(A1, np.eye(2))


def modelo_velocidade_constante(sigma_d=0.5, sigma_m=2.0, dt=1.0,
                                sigma_v0=30.0):
    """
    Estado x = [px, py, vx, vy]ᵀ, medição z = [px, py]ᵀ.

    Σd vem do modelo de "aceleração aleatória": entre dois quadros o objeto
    sofre uma aceleração desconhecida a ~ N(0, sigma_d²), que altera a posição
    em a·dt²/2 e a velocidade em a·dt. Logo Σd = sigma_d² · g gᵀ, g = [dt²/2, dt].
    sigma_d pequeno -> filtro "teimoso" (elefante: confia no modelo);
    sigma_d grande  -> filtro "nervoso" (peixinho-dourado: segue a medição).
    """
    D1 = np.array([[1, dt],
                   [0, 1]], dtype=float)
    g = np.array([[dt**2 / 2], [dt]])
    M = np.hstack([np.eye(2), np.zeros((2, 2))])
    return Modelo(
        nome="velocidade constante",
        D=_por_eixo(D1),
        M=M,
        Sd=_por_eixo(sigma_d**2 * (g @ g.T)),
        Sm=sigma_m**2 * np.eye(2),
        P0_diag=np.array([sigma_m**2] * 2 + [sigma_v0**2] * 2),
    )


def modelo_aceleracao_constante(sigma_d=0.05, sigma_m=2.0, dt=1.0,
                                sigma_v0=60.0, sigma_a0=5.0):
    """
    Estado x = [px, py, vx, vy, ax, ay]ᵀ, medição z = [px, py]ᵀ.

    A aceleração faz parte do estado; para um objeto lançado, a gravidade
    aparece como ay constante (positiva, pois o eixo y da imagem aponta
    para baixo). Aqui sigma_d é o desvio do "jerk" (variação da aceleração
    por quadro): Σd = sigma_d² · g gᵀ, g = [dt³/6, dt²/2, dt].
    """
    D1 = np.array([[1, dt, dt**2 / 2],
                   [0, 1, dt],
                   [0, 0, 1]], dtype=float)
    g = np.array([[dt**3 / 6], [dt**2 / 2], [dt]])
    M = np.hstack([np.eye(2), np.zeros((2, 4))])
    return Modelo(
        nome="aceleracao constante",
        D=_por_eixo(D1),
        M=M,
        Sd=_por_eixo(sigma_d**2 * (g @ g.T)),
        Sm=sigma_m**2 * np.eye(2),
        P0_diag=np.array([sigma_m**2] * 2 + [sigma_v0**2] * 2
                         + [sigma_a0**2] * 2),
    )


# --------------------------------------------------------------------------
# Filtro
# --------------------------------------------------------------------------
class FiltroKalman:
    def __init__(self, modelo, z0):
        """Inicializa o estado com a primeira medição (velocidade etc. = 0,
        mas com variância grande em P, para que o filtro aprenda rápido)."""
        self.mod = modelo
        n = modelo.dim
        self.x = np.zeros(n)
        self.x[:2] = z0
        self.P = np.diag(modelo.P0_diag).astype(float)
        self.I = np.eye(n)

    # ---------------- predição ----------------
    def predizer(self):
        D, Sd = self.mod.D, self.mod.Sd
        self.x = D @ self.x
        self.P = D @ self.P @ D.T + Sd
        return self.x.copy()

    # ---------------- região de busca ----------------
    def cov_inovacao(self):
        """S = M P Mᵀ + Σm: incerteza esperada da próxima medição.
        É ela que define a elipse da região de busca."""
        M = self.mod.M
        return M @ self.P @ M.T + self.mod.Sm

    def mahalanobis2(self, z):
        """Distância de Mahalanobis ao quadrado entre z e a medição prevista."""
        y = z - self.mod.M @ self.x
        S = self.cov_inovacao()
        return float(y @ np.linalg.solve(S, y))

    # ---------------- correção ----------------
    def corrigir(self, z):
        M = self.mod.M
        S = self.cov_inovacao()
        K = self.P @ M.T @ np.linalg.inv(S)
        inovacao = z - M @ self.x
        self.x = self.x + K @ inovacao
        self.P = (self.I - K @ M) @ self.P
        return self.x.copy()

    # ---------------- utilidades ----------------
    @property
    def posicao(self):
        return self.x[:2].copy()

    def prever_k_passos(self, k):
        """Posição prevista k quadros à frente, sem alterar o filtro."""
        x = self.x.copy()
        for _ in range(k):
            x = self.mod.D @ x
        return x[:2]
