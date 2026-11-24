"""
Experimento 4 - Oclusões (a bola passa atrás de um obstáculo).

A) Oclusões REAIS (bola passando atrás do obstáculo) nos vídeos oclusao_*:
   duração, se a trilha foi recuperada, erro da predição no quadro em que a
   bola reaparece e tamanho da região de busca nesse momento.
   Compara com e sem o descarte de medições parciais (área < 50% da
   típica: a bola entrando atrás do obstáculo) e roda com
   max_sem_medicao = 10 para mostrar a trilha sendo perdida.
B) Oclusões SINTÉTICAS: em trechos onde a bola é visível, as medições são
   apagadas de propósito por N quadros. Como a bola continuava sendo vista,
   temos a posição verdadeira durante a "oclusão" e podemos medir o erro da
   predição quadro a quadro. Compara velocidade constante (CV) e aceleração
   constante (CA).
"""
import os

import numpy as np

from comum import (deteccoes, bruto, pasta_saida, tabela_md, plt,
                   SIGMA_D_CV, SIGMA_D_CA, SIGMA_M)
from src.kalman import LIMIAR_GATE_99
from src.pipeline import rodar_rastreador, fabrica, serie

saida = pasta_saida("4_oclusao")
md = os.path.join(saida, "tabela.md")
if os.path.exists(md):
    os.remove(md)

MODELOS = {"CV": fabrica("cv", SIGMA_D_CV["intermediario"], SIGMA_M),
           "CA": fabrica("ca", SIGMA_D_CA, SIGMA_M)}
VIDEOS_OCL = ["oclusao_pequeno_2", "oclusao_pequeno_1", "oclusao_medio_2",
              "oclusao_medio_1", "oclusao_grande"]


def raio_busca(S):
    """Semi-eixo maior da elipse de 99% (px)."""
    return float(np.sqrt(np.linalg.eigvalsh(S).max() * LIMIAR_GATE_99))


def oclusoes_reais(res, dets):
    """Trechos 'no escuro' entre duas medições (descarta a saída do quadro)."""
    tem_det_depois = np.cumsum([len(d) > 0 for d in dets][::-1])[::-1]
    lista, ini = [], None
    for i, r in enumerate(res):
        if r.estado == "no_escuro" and ini is None:
            ini = i
        if ini is not None and r.estado != "no_escuro":
            if i < len(dets) and tem_det_depois[i] > 0:
                recuperou = r.estado == "rastreando" and not r.iniciou
                erro = (np.linalg.norm(r.predicao - r.medicao)
                        if recuperou else np.nan)
                raio = raio_busca(r.S) if r.S is not None else np.nan
                lista.append((ini, i - ini, recuperou, erro, raio))
            ini = None
    return lista


# ---------------- A) oclusões reais ----------------
linhas = []
for v in VIDEOS_OCL:
    d, _, _ = deteccoes(v)
    for nome, fab in MODELOS.items():
        for maxq, frac in ((30, 0.0), (30, 0.5), (10, 0.5)):
            res = rodar_rastreador(d, fab, max_sem_medicao=maxq,
                                   frac_area_min=frac)
            for ini, dur, rec, err, raio in oclusoes_reais(res, d):
                if dur < 1:
                    continue
                linhas.append([v, nome, "sim" if frac else "nao", maxq, ini, dur,
                               "sim" if rec else "NAO (reiniciou)",
                               min(dur, maxq), err, raio])
tabela_md(["video", "modelo", "descarta bola parcial", "max sem medicao",
           "inicio (quadro)",
           "duracao (quadros)", "trilha recuperada", "quadros cobertos pela predicao",
           "erro da predicao ao reaparecer (px)", "raio da regiao de busca (px)"],
          linhas, md, "A - Oclusoes reais")

# figura da oclusão grande
d, _, _ = deteccoes("oclusao_grande")
b = bruto(d)
fig, ax = plt.subplots(figsize=(10, 5))
t = np.arange(len(b))
ax.plot(t, b[:, 1], "o", ms=4, color="tab:blue", label="medicao")
for nome, cor in [("CV", "tab:orange"), ("CA", "tab:purple")]:
    res = rodar_rastreador(d, MODELOS[nome])
    e = serie(res, "estimativa")
    ax.plot(t, e[:, 1], "-", color=cor, lw=1.5, label=f"estimativa {nome}")
    if nome == "CV":
        raio = np.array([raio_busca(r.S) if r.S is not None else np.nan for r in res])
        ax.fill_between(t, e[:, 1] - raio, e[:, 1] + raio, color=cor, alpha=.12,
                        label="regiao de busca CV (semi-eixo)")
        escuro = np.array([r.estado == "no_escuro" for r in res])
        ax.fill_between(t, 0, 640, where=escuro, color="gray", alpha=.15,
                        label="no escuro")
ax.set_xlim(90, 200)
ax.set_ylim(660, -20)
ax.set_xlabel("quadro")
ax.set_ylabel("y (px)")
ax.legend(fontsize=8, loc="lower left")
ax.set_title("oclusao_grande: predicao durante a oclusao e crescimento da regiao de busca")
fig.tight_layout()
fig.savefig(os.path.join(saida, "oclusao_grande.png"), dpi=130)
plt.close(fig)

# ---------------- B) oclusões sintéticas ----------------
DURACOES = [5, 10, 15, 20, 30]
VIDEOS_SINT = ["oclusao_pequeno_1", "oclusao_medio_1", "movimento_mao"]
HIST = 10      # quadros rastreados antes da oclusão
PASSO = 3

linhas, curvas = [], {}
for v in VIDEOS_SINT:
    d, _, _ = deteccoes(v)
    b = bruto(d)
    vis = ~np.isnan(b).any(axis=1)
    for nome, fab in MODELOS.items():
        for N in DURACOES:
            erros_medios, erros_finais, recuperou = [], [], []
            for t0 in range(HIST, len(d) - N - 3, PASSO):
                if not vis[t0 - HIST:t0 + N + 3].all():
                    continue
                apagar = set(range(t0, t0 + N))
                res = rodar_rastreador(d[:t0 + N + 3], fab, quadros_sem_medicao=apagar)
                if any(r.iniciou for r in res[t0 - HIST + 1:]):
                    continue  # trilha não estava estável antes
                est = serie(res, "estimativa")[t0:t0 + N]
                err = np.linalg.norm(est - b[t0:t0 + N], axis=1)
                erros_medios.append(err.mean())
                erros_finais.append(err[-1])
                depois = res[t0 + N:t0 + N + 3]
                recuperou.append(any(r.estado == "rastreando" for r in depois)
                                 and not any(r.iniciou for r in depois))
                curvas.setdefault((v, nome, N), []).append(err)
            if erros_medios:
                linhas.append([v, nome, N, len(erros_medios),
                               float(np.mean(erros_medios)), float(np.mean(erros_finais)),
                               f"{100 * np.mean(recuperou):.0f}%"])
tabela_md(["video", "modelo", "N (quadros apagados)", "n testes",
           "erro medio durante a oclusao (px)", "erro no ultimo quadro (px)",
           "trilha recuperada (ate 3 quadros)"], linhas, md,
          "B - Oclusoes sinteticas (referencia = deteccao real escondida do filtro)")

fig, axs = plt.subplots(1, len(VIDEOS_SINT), figsize=(14, 4))
for ax, v in zip(axs, VIDEOS_SINT):
    for nome, ls in [("CV", "-"), ("CA", "--")]:
        key = (v, nome, 30)
        if key not in curvas:
            key = max((k for k in curvas if k[0] == v and k[1] == nome),
                      key=lambda k: k[2], default=None)
        if key is None:
            continue
        m = np.mean(np.vstack(curvas[key]), axis=0)
        ax.plot(np.arange(1, len(m) + 1), m, ls, lw=2, label=f"{nome} (N={key[2]})")
    ax.set_title(v, fontsize=9)
    ax.set_xlabel("quadros desde o inicio da oclusao")
    ax.legend()
axs[0].set_ylabel("erro medio da predicao (px)")
fig.suptitle("Oclusao sintetica: erro da predicao ao longo da oclusao")
fig.tight_layout()
fig.savefig(os.path.join(saida, "erro_vs_tempo_oclusao.png"), dpi=130)
print("figuras e tabela em", saida)
