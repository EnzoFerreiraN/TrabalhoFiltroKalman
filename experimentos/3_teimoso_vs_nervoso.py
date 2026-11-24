"""
Experimento 3 - Filtro teimoso x nervoso (efeito de Σd: elefante x peixinho-dourado).

Três filtros de velocidade constante, mudando só o desvio da aceleração
aleatória (sigma_d) que gera Σd:
    teimoso       (elefante: lembra do passado, confia no modelo)
    intermediario
    nervoso       (peixinho-dourado: esquece, segue a última medição)

Tabela A - sem gating (todas as medições aceitas): isola o compromisso
           suavidade (rugosidade) x atraso x erro.
Tabela B - com gating: quantas vezes a bola visível caiu fora da região de
           busca e o filtro ficou no escuro / perdeu a trilha.
Cada caso é avaliado com o sensor real e com o sensor degradado (+3 px).
"""
import os

import numpy as np

from comum import (deteccoes, bruto, referencia, pasta_saida, tabela_md, plt,
                   com_ruido, erro_medio, rugosidade, atraso, rejeicoes_indevidas,
                   SIGMA_D_CV, SIGMA_M)
from src.pipeline import rodar_rastreador, fabrica, serie

saida = pasta_saida("3_teimoso_vs_nervoso")
md = os.path.join(saida, "tabela.md")
if os.path.exists(md):
    os.remove(md)

VIDEOS = ["movimento_mao", "oclusao_pequeno_1"]
RUIDO = 3.0
CORES = {"teimoso": "tab:green", "intermediario": "tab:orange", "nervoso": "tab:red"}

la, lb, figs = [], [], {}
for v in VIDEOS:
    d, _, _ = deteccoes(v)
    b = bruto(d)
    ref_real, _ = referencia(v, b)
    for sensor, dets, sm, ref in [("real", d, SIGMA_M, ref_real),
                                  (f"+{RUIDO:.0f}px", com_ruido(d, RUIDO), RUIDO, b)]:
        traj_b = bruto(dets)
        la.append([v, sensor, "bruta (detector)", "-", erro_medio(traj_b, ref),
                   rugosidade(traj_b), atraso(traj_b, ref)])
        for nome, sd in SIGMA_D_CV.items():
            fab = fabrica("cv", sd, sm)
            # A: sem gating
            res = rodar_rastreador(dets, fab, limiar_gate=np.inf)
            f = serie(res, "estimativa")
            f[np.isnan(traj_b).any(axis=1)] = np.nan
            la.append([v, sensor, nome, sd, erro_medio(f, ref), rugosidade(f),
                       atraso(f, ref)])
            figs[(v, sensor, nome)] = f
            # B: com gating
            resg = rodar_rastreador(dets, fab)
            lb.append([v, sensor, nome, sd, rejeicoes_indevidas(resg, dets),
                       sum(r.perdeu for r in resg)])
        figs[(v, sensor, "bruta")] = traj_b
        figs[(v, sensor, "ref")] = ref

tabela_md(["video", "sensor", "filtro", "sigma_d", "erro medio (px)",
           "rugosidade (px/q^2)", "atraso (quadros)"], la, md,
          "A - compromisso suavidade x atraso (sem gating)")
tabela_md(["video", "sensor", "filtro", "sigma_d", "bola rejeitada (quadros)",
           "trilhas perdidas"], lb, md,
          "B - robustez do gating (regiao de busca 99% + raio minimo 20 px)")

# ---------------- figuras: desvio em relação à referência ----------------
# Plotar y direto esconde as diferenças (a bola anda centenas de pixels);
# o desvio (estimativa - referência) mostra o tremor e o atraso de cada filtro.
trechos = {"movimento_mao": (150, 260), "oclusao_pequeno_1": (61, 140)}
for v, (a, z) in trechos.items():
    fig, ax = plt.subplots(2, 1, figsize=(12, 6.5), sharex=True)
    t = np.arange(a, z)
    for k, sensor in enumerate(["real", f"+{RUIDO:.0f}px"]):
        ref = figs[(v, sensor, "ref")][a:z, 1]
        ax[k].plot(t, figs[(v, sensor, "bruta")][a:z, 1] - ref, "o", ms=3,
                   color="tab:blue", alpha=.6, label="bruta")
        for nome in SIGMA_D_CV:
            ax[k].plot(t, figs[(v, sensor, nome)][a:z, 1] - ref, "-", lw=1.6,
                       color=CORES[nome], label=f"{nome} ({SIGMA_D_CV[nome]})")
        ax[k].axhline(0, color="k", lw=.8)
        ax[k].set_ylabel("y - referencia (px)")
        ax[k].set_title(f"sensor {sensor}")
    ax[0].legend(fontsize=8, ncol=4)
    ax[1].set_xlabel("quadro")
    fig.suptitle(f"Efeito de sigma_d - {v} (desvio vertical em relacao a referencia)")
    fig.tight_layout()
    fig.savefig(os.path.join(saida, f"{v}_sigma_d.png"), dpi=130)
    plt.close(fig)
print("figuras e tabela em", saida)
