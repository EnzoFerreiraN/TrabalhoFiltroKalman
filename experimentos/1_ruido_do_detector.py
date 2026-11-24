"""
Experimento 1 - Ruído do detector (de onde vem o valor de Σm).

1) Bola parada (bola_parada): a variação do centroide é puro ruído
   do detector -> limite INFERIOR de Σm (câmera parada, sem borrão).
2) Bola em movimento (movimento_mao): resíduo entre a trajetória
   bruta e uma versão suavizada -> ruído "real" durante o movimento
   (borrão, oclusão parcial pela mão, compressão do vídeo).
"""
import os

import numpy as np

from comum import (deteccoes, bruto, referencia, pasta_saida, tabela_md, plt,
                   SIGMA_M)

saida = pasta_saida("1_ruido_do_detector")
md = os.path.join(saida, "tabela.md")
if os.path.exists(md):
    os.remove(md)

# 1) parada
d, _, _ = deteccoes("bola_parada")
b = bruto(d)
b = b[~np.isnan(b).any(axis=1)]
std_parada = b.std(axis=0)

# 2) movimento
d2, _, _ = deteccoes("movimento_mao")
b2 = bruto(d2)
ref, _ = referencia("movimento_mao", b2)  # usa só a suavização
res = b2 - ref
res = res[~np.isnan(res).any(axis=1)]
std_mov = res.std(axis=0)

tabela_md(["situacao", "desvio x (px)", "desvio y (px)", "n quadros"],
          [["bola parada", std_parada[0], std_parada[1], len(b)],
           ["bola em movimento (residuo)", std_mov[0], std_mov[1], len(res)]],
          md, "Ruido de medicao do detector")

with open(md, "a") as f:
    f.write(f"Valor adotado: sigma_m = {SIGMA_M} px (Sm = sigma_m^2 * I).\n\n"
            "A bola parada da o limite inferior. Em movimento o residuo e "
            "maior, e ainda subestima o ruido real, porque a suavizacao "
            "absorve parte dele e porque os quadros com oclusao parcial "
            "(centroide deslocado) sao poucos. Adotamos uma margem de ~4x o "
            "residuo. O comportamento do filtro depende da razao Sd/Sm, que "
            "e variada no experimento 3.\n")

fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ax[0].scatter(b[:, 0] - b[:, 0].mean(), b[:, 1] - b[:, 1].mean(), s=4)
ax[0].set_title("Bola parada: centroide - media (px)")
ax[0].set_aspect("equal")
ax[1].hist(res[:, 0], 60, alpha=.6, label="x")
ax[1].hist(res[:, 1], 60, alpha=.6, label="y")
ax[1].set_title("Bola em movimento: residuo bruto - suavizado (px)")
ax[1].legend()
fig.tight_layout()
fig.savefig(os.path.join(saida, "sigma_m.png"), dpi=130)
print("figuras e tabela em", saida)
