"""
Experimento 5 - Lançamento: velocidade constante (CV) x aceleração
constante (CA), e predição k quadros à frente.

Para cada vídeo de lançamento:
  - referência física: parábola ajustada por mínimos quadrados às detecções
    (x linear no tempo, y quadrático) -> gravidade de referência g = 2·c2;
  - erro da predição de 1 quadro (inovação) para CV e CA;
  - aceleração vertical ay estimada pelo CA ao longo do voo;
  - erro da predição k quadros à frente (k = 1..6);
  - extensão: prever o ponto em que a bola cruza uma linha vertical
    (x = 80% do caminho), a partir de cada quadro antes do cruzamento.

Opcional: --diametro-bola-cm 6.5 converte a gravidade para m/s² usando o
diâmetro da bola em pixels como escala (meça a sua bola!).
"""
import argparse
import os

import numpy as np

from comum import (deteccoes, bruto, pasta_saida, tabela_md, plt,
                   SIGMA_D_CV, SIGMA_D_CA, SIGMA_M)
from src.pipeline import rodar_rastreador, fabrica

ap = argparse.ArgumentParser()
ap.add_argument("--diametro-bola-cm", type=float, default=None)
args = ap.parse_args()

saida = pasta_saida("5_lancamento_cv_vs_ca")
md = os.path.join(saida, "tabela.md")
if os.path.exists(md):
    os.remove(md)

VIDEOS = ["lancamento_horizontal", "lancamento_1", "lancamento_2"]
FABS = {"CV": fabrica("cv", SIGMA_D_CV["intermediario"], SIGMA_M),
        "CA": fabrica("ca", SIGMA_D_CA, SIGMA_M)}
KS = range(1, 7)
FRAC_LINHA = 0.8


def propagar(mod, x, k):
    for _ in range(k):
        x = mod.D @ x
    return x


def cruzamento(xs, ys, xl):
    """y no ponto em que a sequência (xs, ys) cruza x = xl (interpolação)."""
    s = np.sign(xs - xl)
    for i in range(1, len(xs)):
        if s[i - 1] != s[i] and s[i] != 0 or s[i] == 0:
            a = (xl - xs[i - 1]) / (xs[i] - xs[i - 1]) if xs[i] != xs[i - 1] else 0
            return i - 1 + a, ys[i - 1] + a * (ys[i] - ys[i - 1])
    return None, None


l_resumo, l_k, l_linha = [], [], []
fig_t, axs_t = plt.subplots(len(VIDEOS), 2, figsize=(12, 3.6 * len(VIDEOS)))
fig_k, axs_k = plt.subplots(1, len(VIDEOS), figsize=(14, 4))
fig_l, axs_l = plt.subplots(1, len(VIDEOS), figsize=(14, 4))

for iv, v in enumerate(VIDEOS):
    d, fps, _ = deteccoes(v)
    b = bruto(d)
    idx = np.where(~np.isnan(b).any(axis=1))[0]
    t = idx.astype(float)

    # referência física: parábola
    cx = np.polyfit(t, b[idx, 0], 1)
    cy = np.polyfit(t, b[idx, 1], 2)
    g_ref = 2 * cy[0]                              # px/quadro²
    resid = np.sqrt(np.mean((np.polyval(cy, t) - b[idx, 1])**2
                            + (np.polyval(cx, t) - b[idx, 0])**2))

    escala = None
    if args.diametro_bola_cm:
        diam_px = np.median([min(dd[0].bbox[2:]) for dd in d if dd])
        escala = (args.diametro_bola_cm / 100) / diam_px      # m por pixel

    ax_xy, ax_a = axs_t[iv]
    ax_xy.plot(b[idx, 0], b[idx, 1], "o", color="tab:blue", label="medicao")
    tt = np.linspace(t[0], t[-1], 100)
    ax_xy.plot(np.polyval(cx, tt), np.polyval(cy, tt), "k--", lw=1, label="parabola ajustada")
    ax_a.axhline(g_ref, color="k", ls="--", lw=1, label=f"g da parabola = {g_ref:.2f}")

    for nome, fab in FABS.items():
        mod = fab()
        res = rodar_rastreador(d, fab)
        est = np.array([r.estimativa if r.estimativa is not None else [np.nan] * 2
                        for r in res])
        # inovação (erro da predição de 1 quadro) nos quadros com medição
        inov = [np.linalg.norm(r.medicao - r.predicao) for r in res
                if r.medicao is not None and r.predicao is not None]
        linha = [v, nome, len(idx), float(np.mean(inov)), float(np.max(inov))]
        if nome == "CA":
            ay = [r.estado_vetor[5] for r in res
                  if r.estado_vetor is not None and r.medicao is not None]
            linha += [ay[-1], g_ref]
            if escala:
                linha += [ay[-1] * fps**2 * escala, g_ref * fps**2 * escala]
            ax_a.plot(idx[:len(ay)], ay, "o-", color="tab:purple", label="ay estimado (CA)")
        else:
            linha += ["-", g_ref] + (["-", g_ref * fps**2 * escala] if escala else [])
        l_resumo.append(linha)
        ax_xy.plot(est[idx[0]:idx[-1] + 1, 0], est[idx[0]:idx[-1] + 1, 1], "-",
                   label=f"estimativa {nome}")

        # predição k quadros à frente
        erros_k = []
        for k in KS:
            e = []
            for i in idx[3:]:
                if i + k < len(b) and not np.isnan(b[i + k]).any() and res[i].medicao is not None:
                    xk = propagar(mod, res[i].estado_vetor, k)
                    e.append(np.linalg.norm(xk[:2] - b[i + k]))
            erros_k.append(np.mean(e) if e else np.nan)
            l_k.append([v, nome, k, len(e), erros_k[-1]])
        axs_k[iv].plot(list(KS), erros_k, "o-", label=nome)

        # cruzamento da linha
        xl = b[idx[0], 0] + FRAC_LINHA * (b[idx[-1], 0] - b[idx[0], 0])
        tc, yc = cruzamento(b[idx, 0], b[idx, 1], xl)
        if yc is None:
            continue
        tc = idx[0] + tc   # aproximado (quadros consecutivos)
        antecs, errs = [], []
        for i in idx[2:]:
            if i >= tc or res[i].medicao is None:
                continue
            traj = [res[i].estado_vetor]
            for _ in range(60):
                traj.append(mod.D @ traj[-1])
            traj = np.array(traj)
            _, yp = cruzamento(traj[:, 0], traj[:, 1], xl)
            if yp is not None:
                antecs.append(tc - i)
                errs.append(abs(yp - yc))
        axs_l[iv].plot(antecs, errs, "o-", label=nome)
        for a_, e_ in zip(antecs, errs):
            l_linha.append([v, nome, round(a_, 1), e_])

    ax_xy.invert_yaxis()
    ax_xy.set_title(v)
    ax_xy.legend(fontsize=7)
    ax_a.set_title("aceleracao vertical (px/quadro^2)")
    ax_a.set_xlabel("quadro")
    ax_a.legend(fontsize=7)
    axs_k[iv].set_title(v)
    axs_k[iv].set_xlabel("k (quadros a frente)")
    axs_k[iv].legend()
    axs_l[iv].set_title(f"{v}: linha em x = {FRAC_LINHA:.0%} do caminho", fontsize=9)
    axs_l[iv].set_xlabel("quadros antes do cruzamento")
    axs_l[iv].invert_xaxis()
    axs_l[iv].legend()

axs_k[0].set_ylabel("erro medio (px)")
axs_l[0].set_ylabel("erro em y no cruzamento (px)")
for f, nome in [(fig_t, "trajetoria_e_aceleracao.png"), (fig_k, "erro_k_passos.png"),
                (fig_l, "cruzamento_linha.png")]:
    f.tight_layout()
    f.savefig(os.path.join(saida, nome), dpi=130)

cab = ["video", "modelo", "quadros com bola", "erro medio pred. 1 quadro (px)",
       "erro max pred. 1 quadro (px)", "ay final estimado (px/q^2)",
       "g da parabola (px/q^2)"]
if args.diametro_bola_cm:
    cab += ["ay final (m/s^2)", "g parabola (m/s^2)"]
tabela_md(cab, l_resumo, md, "Resumo CV x CA")
tabela_md(["video", "modelo", "k", "n", "erro medio (px)"], l_k, md,
          "Predicao k quadros a frente")
tabela_md(["video", "modelo", "quadros antes do cruzamento", "erro em y (px)"],
          l_linha, md, "Extensao: previsao do ponto de cruzamento da linha")
print("figuras e tabela em", saida)

# =========================== vídeo ===========================
from video_util import (gerar_videos, Gravador, tela, lado_a_lado, ler_quadros,
                        desenhar_resultado, escrever, BRANCO, MAGENTA)
from comum import VIDEOS as PASTA_VIDEOS
import cv2

if gerar_videos():
    g = Gravador(os.path.join(saida, "video_lancamento_cv_vs_ca.mp4"))
    TIT = "Experimento 5 – Lançamento: velocidade × aceleração constante"
    E = 1.0   # ampliação para desenhar

    def ponto(p):
        return int(p[0] * E), int(p[1] * E)

    for k, v in enumerate(["lancamento_horizontal", "lancamento_2"]):
        d, _, _ = deteccoes(v)
        b = bruto(d)
        idx = np.where(~np.isnan(b).any(axis=1))[0]
        xl = b[idx[0], 0] + FRAC_LINHA * (b[idx[-1], 0] - b[idx[0], 0])
        tc, yc = cruzamento(b[idx, 0], b[idx, 1], xl)
        qs = ler_quadros(os.path.join(PASTA_VIDEOS, v + ".mp4"))
        res = {n: rodar_rastreador(d, fab) for n, fab in FABS.items()}
        mods = {n: fab() for n, fab in FABS.items()}
        ini, fim = idx[0] - 8, idx[-1]
        for i in range(ini, fim + 1):
            paineis, rotulos = [], []
            for n in FABS:
                r = res[n][i]
                traj = [x.estimativa for x in res[n][idx[0]:i + 1]
                        if x.estimativa is not None and x.estado != "inativo"]
                im = desenhar_resultado(qs[i], r, traj, escala=E)
                h = im.shape[0]
                cv2.line(im, (int(xl * E), 0), (int(xl * E), h), BRANCO, 2, cv2.LINE_AA)
                cv2.circle(im, ponto((xl, yc)), 10, BRANCO, 2, cv2.LINE_AA)
                linhas = []
                if r.estado_vetor is not None and r.estado != "inativo" and i >= idx[0] + 2:
                    caminho = [r.estado_vetor]
                    for _ in range(40):
                        caminho.append(mods[n].D @ caminho[-1])
                    caminho = np.array(caminho)
                    for a_, b_ in zip(caminho[:12:1], caminho[1:13:1]):
                        if np.linalg.norm(b_[:2] - a_[:2]) > 0:
                            cv2.line(im, ponto(a_[:2]), ponto(b_[:2]), (0, 0, 220) if n == "CV"
                                     else (200, 0, 160), 2, cv2.LINE_AA)
                    for p in caminho[1:13]:
                        cv2.circle(im, ponto(p[:2]), 3, BRANCO, -1, cv2.LINE_AA)
                    if (caminho[0][0] - xl) * (b[idx[-1], 0] - xl) < 0 or i <= tc + idx[0]:
                        _, yp = cruzamento(caminho[:, 0], caminho[:, 1], xl)
                        if yp is not None and i < idx[0] + tc:
                            cv2.drawMarker(im, ponto((xl, yp)), MAGENTA, cv2.MARKER_DIAMOND, 22, 3)
                            linhas.append(f"erro no cruzamento: {abs(yp - yc):.0f} px")
                    if n == "CA":
                        linhas.append(f"ay estimado: {r.estado_vetor[5]:.2f} px/q²".replace(".", ","))
                if linhas:
                    im = escrever(im, [(t, (12, h - 52 - 24 * (len(linhas) - j)), 17, (30, 30, 30), True)
                                       for j, t in enumerate(linhas)])
                paineis.append(im)
                rotulos.append("velocidade constante (CV)" if n == "CV" else
                               "aceleração constante (CA)")
            conteudo = lado_a_lado(paineis, rotulos, cores=[(110, 110, 255), (230, 120, 230)])
            q = tela(conteudo, TIT, f"{v}, câmera lenta 8x. O CV prevê a bola sempre acima; o CA dobra a "
                     "previsão para baixo, como a gravidade.", f"lançamento {k + 1}/2")
            g.add(q, 8)
        g.pausa(q, 2)
    g.fechar()
