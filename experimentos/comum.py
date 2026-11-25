"""Funções compartilhadas pelos experimentos: caminhos, cache, referência e métricas."""
import csv
import os
import pickle
import sys

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402,F401
from scipy.signal import savgol_filter  # noqa: E402

from src.pipeline import detectar_video, bruto  # noqa: E402,F401

VIDEOS = os.path.join(RAIZ, "videos")
RESULTADOS = os.path.join(RAIZ, "resultados")
REFERENCIAS = os.path.join(RAIZ, "referencias")

# Valores de Σd usados em todo o trabalho (desvio da aceleração, px/quadro²)
SIGMA_D_CV = {"teimoso": 0.3, "intermediario": 2.0, "nervoso": 10.0}
SIGMA_D_CA = 0.2      # desvio do "jerk" no modelo de aceleração constante
SIGMA_M = 2.0         # desvio da medição (px) - ver 1_ruido_do_detector.py


def pasta_saida(nome):
    p = os.path.join(RESULTADOS, nome)
    os.makedirs(p, exist_ok=True)
    return p


def deteccoes(nome_video):
    """Detecções de todos os quadros (com cache em resultados/cache)."""
    cache = os.path.join(pasta_saida("cache"), nome_video + ".pkl")
    caminho = os.path.join(VIDEOS, nome_video + ".mp4")
    if os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(caminho):
        with open(cache, "rb") as f:
            return pickle.load(f)
    dados = detectar_video(caminho)
    with open(cache, "wb") as f:
        pickle.dump(dados, f)
    return dados


def segmentos_validos(traj):
    """Intervalos [ini, fim) de quadros consecutivos sem NaN."""
    ok = ~np.isnan(traj).any(axis=1)
    segs, ini = [], None
    for i, v in enumerate(list(ok) + [False]):
        if v and ini is None:
            ini = i
        if not v and ini is not None:
            segs.append((ini, i))
            ini = None
    return segs


def referencia(nome_video, traj_bruta, janela=11, ordem=3):
    """
    Trajetória de referência para medir erro e atraso.
    - Se existir referencias/<video>.csv (marcada à mão com
      marcar_referencia.py), usa ela: é a referência "verdadeira".
    - Senão, usa a trajetória bruta suavizada por Savitzky-Golay CENTRADO
      (não causal: usa quadros do futuro, por isso não tem atraso).
    Devolve (ref Nx2 com NaN, descricao).
    """
    arq = os.path.join(REFERENCIAS, nome_video + ".csv")
    ref = np.full_like(traj_bruta, np.nan)
    if os.path.exists(arq):
        with open(arq, encoding="utf-8") as f:
            for linha in csv.DictReader(f):
                if linha["x"] != "":
                    ref[int(linha["quadro"])] = [float(linha["x"]), float(linha["y"])]
        return ref, "marcada a mao"
    for a, b in segmentos_validos(traj_bruta):
        if b - a >= janela:
            ref[a:b] = savgol_filter(traj_bruta[a:b], janela, ordem, axis=0)
    return ref, "Savitzky-Golay centrado (nao causal)"


def com_ruido(deteccoes_por_quadro, sigma, semente=0):
    """
    "Sensor degradado": soma ruído gaussiano N(0, sigma²) a cada centroide.
    O detector HSV desta cena é muito preciso (ver experimento 1), então o efeito de
    suavização do filtro quase não aparece. Com o ruído artificial temos uma
    referência verdadeira (a detecção limpa) e conseguimos medir o ganho do
    filtro e o compromisso suavidade x atraso de forma controlada.
    """
    from src.detector import Deteccao
    rng = np.random.default_rng(semente)
    saida = []
    for dets in deteccoes_por_quadro:
        nova = []
        for d in dets:
            ex, ey = rng.normal(0, sigma, 2)
            nova.append(Deteccao(d.x + ex, d.y + ey, d.area, d.bbox))
        saida.append(nova)
    return saida


# ----------------------------- métricas -----------------------------------
def erro_medio(traj, ref):
    """Erro euclidiano médio (px) nos quadros em que os dois existem."""
    d = np.linalg.norm(traj - ref, axis=1)
    return float(np.nanmean(d))


def rugosidade(traj):
    """RMS da segunda diferença (px/quadro²): mede o 'tremor' da trajetória."""
    a = np.diff(traj, 2, axis=0)
    a = a[~np.isnan(a).any(axis=1)]
    return float(np.sqrt(np.mean(np.sum(a**2, axis=1)))) if len(a) else np.nan


def atraso(traj, ref, vel_min=2.0):
    """
    Atraso médio em QUADROS em relação à referência.
    Projeta o erro (ref - traj) na direção do movimento e divide pela
    velocidade: atraso = ((ref - traj) . v) / |v|^2. Positivo = a estimativa
    está "atrás" do objeto. Só usa quadros com velocidade > vel_min px/quadro.
    """
    v = np.gradient(ref, axis=0)
    rapido = np.linalg.norm(v, axis=1) > vel_min
    e = ref - traj
    num = np.sum(e * v, axis=1)
    den = np.sum(v * v, axis=1)
    ok = rapido & ~np.isnan(num) & ~np.isnan(den)
    return float(np.mean(num[ok] / den[ok])) if ok.any() else np.nan


def rejeicoes_indevidas(resultados, deteccoes_por_quadro):
    """Quadros em que a bola foi detectada mas o filtro ficou 'no escuro'
    (a medição caiu fora da região de busca)."""
    return sum(r.estado == "no_escuro" and len(d) > 0
               for r, d in zip(resultados, deteccoes_por_quadro))


def tabela_md(cabecalho, linhas, caminho, titulo=None):
    """Salva uma tabela em Markdown (fácil de copiar para o relatório)."""
    def fmt(v):
        if isinstance(v, (float, np.floating)):
            return f"{v:.2e}" if 0 < abs(v) < 0.01 else f"{v:.2f}"
        return str(v)
    txt = ""
    if titulo:
        txt += f"### {titulo}\n\n"
    txt += "| " + " | ".join(cabecalho) + " |\n"
    txt += "|" + "---|" * len(cabecalho) + "\n"
    for l in linhas:
        txt += "| " + " | ".join(fmt(v) for v in l) + " |\n"
    with open(caminho, "a", encoding="utf-8") as f:
        f.write(txt + "\n")
    print(txt)
