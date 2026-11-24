"""
Marcação manual da referência (ground truth).

Abre o vídeo e mostra um quadro a cada --passo quadros, ampliado. Clique no
CENTRO da bola. Os experimentos 1 e 2 passam a usar essa referência no lugar
da suavização automática.

Teclas:
    clique esquerdo  marca o centro e avança
    n                bola não visível neste quadro (avança sem marcar)
    b                volta um quadro marcado
    q                salva e sai

Uso:
    python ferramentas/marcar_referencia.py --video videos/movimento_mao.mp4
Saída: referencias/<nome_do_video>.csv  (quadro, x, y)
"""
import argparse
import csv
import os

import cv2

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--passo", type=int, default=5, help="marca 1 a cada N quadros")
    ap.add_argument("--zoom", type=float, default=2.0)
    args = ap.parse_args()

    cap = cv2.VideoCapture(args.video)
    quadros = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        quadros.append(f)
    indices = list(range(0, len(quadros), args.passo))

    nome = os.path.splitext(os.path.basename(args.video))[0]
    saida = os.path.join(RAIZ, "referencias", nome + ".csv")
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    marcas = {}
    if os.path.exists(saida):
        with open(saida) as f:
            for l in csv.DictReader(f):
                marcas[int(l["quadro"])] = (None if l["x"] == "" else
                                            (float(l["x"]), float(l["y"])))

    pos = 0
    clique = {"pt": None}

    def ao_clicar(ev, x, y, *_):
        if ev == cv2.EVENT_LBUTTONDOWN:
            clique["pt"] = (x / args.zoom, y / args.zoom)

    janela = "marcar referencia (clique = centro, n = sem bola, b = voltar, q = sair)"
    cv2.namedWindow(janela)
    cv2.setMouseCallback(janela, ao_clicar)
    while 0 <= pos < len(indices):
        q = indices[pos]
        img = cv2.resize(quadros[q], None, fx=args.zoom, fy=args.zoom,
                         interpolation=cv2.INTER_NEAREST)
        if marcas.get(q):
            x, y = marcas[q]
            cv2.circle(img, (int(x * args.zoom), int(y * args.zoom)), 6, (255, 0, 255), 2)
        cv2.putText(img, f"quadro {q} ({pos + 1}/{len(indices)})", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imshow(janela, img)
        k = cv2.waitKey(30) & 0xFF
        if clique["pt"] is not None:
            marcas[q] = clique["pt"]
            clique["pt"] = None
            pos += 1
        elif k == ord("n"):
            marcas[q] = None
            pos += 1
        elif k == ord("b"):
            pos = max(0, pos - 1)
        elif k == ord("q"):
            break
    cv2.destroyAllWindows()

    with open(saida, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["quadro", "x", "y"])
        for q in sorted(marcas):
            v = marcas[q]
            wr.writerow([q, "", ""] if v is None else [q, f"{v[0]:.2f}", f"{v[1]:.2f}"])
    print(f"{sum(v is not None for v in marcas.values())} marcas salvas em {saida}")


if __name__ == "__main__":
    main()
