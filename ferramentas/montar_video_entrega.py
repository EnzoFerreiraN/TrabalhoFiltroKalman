"""
Monta o vídeo de entrega (item c do enunciado: 1 a 3 minutos, com as
sobreposições e com um trecho de oclusão).

Ordem:
    1. tela de título com os nomes da dupla (3 s)
    2. o sistema rastreando a bola em velocidade normal, com a máscara do
       detector ao lado (~20 s)
    3. experimento 4 – oclusões (trecho obrigatório)
    4. experimento 5 – lançamento, velocidade × aceleração constante
    5. experimento 3 – filtro teimoso × nervoso (Σd)
    6. experimento 2 – trajetória bruta × filtrada

Precisa dos vídeos dos experimentos já gerados (python rodar_tudo.py) e do ffmpeg.
Uso: python ferramentas/montar_video_entrega.py
Saída: resultados/video_entrega.mp4
"""
import os
import shutil
import sys

import cv2
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "experimentos"))

from src.detector import DetectorHSV  # noqa: E402
from src.pipeline import fabrica  # noqa: E402
from src.rastreador import Rastreador, INATIVO  # noqa: E402
from video_util import (Gravador, tela, lado_a_lado, ler_quadros, escrever,  # noqa: E402
                        desenhar_resultado, emendar_videos, LARG, ALT, BRANCO)

INTEGRANTES = ["Antônio Enzo Ferreira do Nascimento", "João Felipe Garcia Morais"]
RES = os.path.join(RAIZ, "resultados")
TRECHOS = ["4_oclusao/video_oclusao.mp4",
           "5_lancamento_cv_vs_ca/video_lancamento_cv_vs_ca.mp4",
           "3_teimoso_vs_nervoso/video_teimoso_vs_nervoso.mp4",
           "2_bruto_vs_filtrado/video_bruto_vs_filtrado.mp4"]


def tela_titulo():
    q = np.full((ALT, LARG, 3), (60, 38, 18), np.uint8)
    itens = [("Rastreamento de objeto colorido", (80, 120), 44, BRANCO, True),
             ("com filtro de Kalman", (80, 176), 44, BRANCO, True),
             ("Visão Computacional – UFPI 2026.2 – Trabalho final, Opção 01", (80, 262), 24,
              (200, 220, 255), False),
             ("Prof. Kelson Aires", (80, 300), 22, (200, 220, 255), False)]
    for i, nome in enumerate(INTEGRANTES):
        itens.append((nome, (80, 400 + 48 * i), 30, BRANCO, True))
    return escrever(q, itens)


def demonstracao(caminho_saida, ini=95, fim=700):
    """O sistema rodando em velocidade normal: sobreposições + máscara HSV."""
    g = Gravador(caminho_saida)
    g.pausa(tela_titulo(), 3)
    qs = ler_quadros(os.path.join(RAIZ, "videos", "movimento_mao.mp4"))
    det = DetectorHSV()
    h, w = qs[0].shape[:2]
    r = Rastreador(fabrica("cv"), max_sem_medicao=30, raio_min=20, frac_area_min=0.5,
                   limites=(w, h))
    traj = []
    for i, f in enumerate(qs[:fim + 1]):
        res = r.passo(det.detectar(f))
        if res.iniciou or res.estado == INATIVO:
            traj = []
        if res.estado != INATIVO and res.estimativa is not None:
            traj.append(res.estimativa)
        if i < ini:
            continue
        im = desenhar_resultado(f, res, traj[-45:], escala=1.6)
        mascara = cv2.cvtColor(det.mascara(f), cv2.COLOR_GRAY2BGR)
        mascara = cv2.resize(mascara, (im.shape[1], im.shape[0]), interpolation=cv2.INTER_NEAREST)
        conteudo = lado_a_lado([im, mascara], ["rastreamento", "máscara HSV (o que o detector vê)"])
        g.add(tela(conteudo, "O sistema em funcionamento", "medição (azul) · predição (vermelho) · "
                   "estimativa e trajetória (laranja) · região de busca (elipse)", "velocidade normal"))
    g.fechar()


def main():
    if not shutil.which("ffmpeg"):
        sys.exit("precisa do ffmpeg instalado para emendar os trechos")
    faltando = [t for t in TRECHOS if not os.path.exists(os.path.join(RES, t))]
    if faltando:
        sys.exit("rode antes: python rodar_tudo.py  (faltam: " + ", ".join(faltando) + ")")
    abertura = os.path.join(RES, "_abertura_entrega.mp4")
    demonstracao(abertura)
    saida = os.path.join(RES, "video_entrega.mp4")
    emendar_videos([abertura] + [os.path.join(RES, t) for t in TRECHOS], saida, recodificar=True)
    os.remove(abertura)
    cap = cv2.VideoCapture(saida)   # duração sem depender do ffprobe
    dur = cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 30)
    cap.release()
    print(f"video de entrega: {saida} ({int(dur // 60)} min {dur % 60:.0f} s)")


if __name__ == "__main__":
    main()
