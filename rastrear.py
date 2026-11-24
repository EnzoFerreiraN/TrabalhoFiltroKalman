"""
Programa principal: rastreia a bola verde num vídeo gravado ou na webcam.

Exemplos:
    python rastrear.py --video videos/oclusao_grande.mp4
    python rastrear.py --video videos/lancamento_horizontal.mp4 --modelo ca
    python rastrear.py --video 0                      # webcam
    python rastrear.py --video videos/movimento_mao.mp4 \
        --sigma-d 5 --salvar resultados/videos/nervoso.mp4 --sem-janela

    # câmera lenta 4x, guardando só os trechos em que a bola está sendo rastreada
    python rastrear.py --video videos/oclusao_medio_1.mp4 --sem-janela \
        --camera-lenta 4 --so-trechos-com-bola --salvar resultados/videos/lento.mp4

Teclas na janela: q = sair, espaço = pausar/continuar.
"""
import argparse
import os
import time
from collections import deque

import cv2

from src.detector import DetectorHSV
from src.kalman import LIMIAR_GATE_99
from src.pipeline import abrir_fonte, fabrica, salvar_csv
from src.rastreador import Rastreador, INATIVO
from src.visualizacao import desenhar


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", required=True,
                    help="caminho do vídeo ou índice da webcam (0, 1...)")
    ap.add_argument("--modelo", choices=["cv", "ca"], default="cv",
                    help="cv = velocidade constante, ca = aceleração constante")
    ap.add_argument("--sigma-d", type=float, default=None,
                    help="desvio do ruído do processo (padrão: 2.0 p/ cv, 0.2 p/ ca)")
    ap.add_argument("--sigma-m", type=float, default=2.0,
                    help="desvio do ruído de medição em pixels (padrão 2.0)")
    ap.add_argument("--max-sem-medicao", type=int, default=30,
                    help="quadros só com predição antes de perder a trilha")
    ap.add_argument("--raio-min", type=float, default=20.0,
                    help="raio mínimo da região de busca em pixels (padrão 20)")
    ap.add_argument("--frac-area-min", type=float, default=0.5,
                    help="descarta deteccoes com area < frac x area tipica "
                         "(bola parcialmente escondida). 0 = desliga")
    ap.add_argument("--hsv-min", type=int, nargs=3, default=[35, 80, 60])
    ap.add_argument("--hsv-max", type=int, nargs=3, default=[85, 255, 255])
    ap.add_argument("--redimensionar", type=int, nargs=2, metavar=("L", "A"),
                    help="redimensiona cada quadro (ex.: 640 480)")
    ap.add_argument("--salvar", help="salva o vídeo com as sobreposições (.mp4)")
    ap.add_argument("--camera-lenta", type=int, default=1, metavar="N",
                    help="vídeo salvo (e janela) N vezes mais lento (ex.: 4). "
                         "Cada quadro é repetido N vezes, mantendo 30 fps")
    ap.add_argument("--so-trechos-com-bola", action="store_true",
                    help="no vídeo salvo, mantém só os trechos com a trilha "
                         "ativa (+15 quadros antes e depois)")
    ap.add_argument("--seguir-fora-do-quadro", action="store_true",
                    help="não encerra a trilha quando a estimativa sai da imagem "
                         "(continua prevendo até --max-sem-medicao)")
    ap.add_argument("--csv", help="salva o log quadro a quadro (.csv)")
    ap.add_argument("--mascara", action="store_true",
                    help="mostra também a máscara HSV")
    ap.add_argument("--sem-janela", action="store_true",
                    help="não abre janela (útil para só gerar vídeo/CSV)")
    args = ap.parse_args()

    detector = DetectorHSV(args.hsv_min, args.hsv_max)
    rastreador = Rastreador(fabrica(args.modelo, args.sigma_d, args.sigma_m),
                            max_sem_medicao=args.max_sem_medicao,
                            raio_min=args.raio_min,
                            frac_area_min=args.frac_area_min)
    cap = abrir_fonte(args.video)
    fps_video = cap.get(cv2.CAP_PROP_FPS) or 30.0
    if not args.seguir_fora_do_quadro:
        if args.redimensionar:
            rastreador.limites = tuple(args.redimensionar)
        else:
            rastreador.limites = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                                  int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    escritor = None
    resultados, trajetoria = [], []
    tempos = []
    pausado = False
    rotulo = "CV" if args.modelo == "cv" else "CA"
    lento = max(1, args.camera_lenta)
    if lento > 1:
        rotulo += f" | camera lenta {lento}x"
    MARGEM = 15                     # quadros antes/depois de cada trecho
    antes = deque(maxlen=MARGEM)    # quadros guardados antes da trilha começar
    depois = 0                      # quadros ainda a gravar após a trilha acabar

    def gravar(im):
        nonlocal escritor
        if escritor is None:
            os.makedirs(os.path.dirname(args.salvar) or ".", exist_ok=True)
            h, w = im.shape[:2]
            escritor = cv2.VideoWriter(args.salvar, cv2.VideoWriter_fourcc(*"mp4v"),
                                       fps_video, (w, h))
        for _ in range(lento):      # repetir o quadro = câmera lenta
            escritor.write(im)

    while True:
        if not pausado:
            ok, frame = cap.read()
            if not ok:
                break
            t0 = time.perf_counter()
            if args.redimensionar:
                frame = cv2.resize(frame, tuple(args.redimensionar))

            # ---------- captura -> detecção -> filtro ----------
            dets = detector.detectar(frame)
            res = rastreador.passo(dets)
            resultados.append(res)

            if res.iniciou or res.estado == INATIVO:
                trajetoria = []
            if res.estado != INATIVO and res.estimativa is not None:
                trajetoria.append(res.estimativa)

            fps_inst = 1.0 / max(time.perf_counter() - t0, 1e-6)
            img = desenhar(frame, res, trajetoria, LIMIAR_GATE_99,
                           args.max_sem_medicao, fps=fps_inst, rotulo=rotulo,
                           raio_min=args.raio_min)
            tempos.append(time.perf_counter() - t0)

            if args.salvar and not args.so_trechos_com_bola:
                gravar(img)
            elif args.salvar:
                if res.estado != INATIVO:
                    while antes:                # começo do trecho: grava o "antes"
                        gravar(antes.popleft())
                    gravar(img)
                    depois = MARGEM
                elif depois > 0:
                    gravar(img)
                    depois -= 1
                else:
                    antes.append(img)

        if not args.sem_janela:
            cv2.imshow("rastreamento (q = sair, espaco = pausa)", img)
            if args.mascara:
                cv2.imshow("mascara HSV", detector.mascara(frame))
            espera = 0 if pausado else max(1, int(1000 * lento / fps_video))
            tecla = cv2.waitKey(espera) & 0xFF
            if tecla == ord("q"):
                break
            if tecla == ord(" "):
                pausado = not pausado

    cap.release()
    if escritor is not None:
        escritor.release()
    cv2.destroyAllWindows()

    if args.csv:
        salvar_csv(resultados, args.csv)
    if tempos:
        ms = 1000 * sum(tempos) / len(tempos)
        h, w = img.shape[:2]
        print(f"{len(tempos)} quadros {w}x{h} | processamento medio "
              f"{ms:.2f} ms/quadro = {1000 / ms:.0f} fps")
        n_escuro = sum(r.estado == "no_escuro" for r in resultados)
        print(f"quadros no escuro: {n_escuro} | trilhas iniciadas: "
              f"{sum(r.iniciou for r in resultados)}")


if __name__ == "__main__":
    main()
