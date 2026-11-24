"""
Calibração dos limites HSV com barras deslizantes.

    python ferramentas/calibrar_hsv.py --video videos/movimento_mao.mp4
    python ferramentas/calibrar_hsv.py --video 0            # webcam

Ajuste as barras até a bola ficar branca e sólida na máscara e o resto preto.
Teclas: espaço = pausa/continua, q = sai e imprime os valores para usar em
rastrear.py (--hsv-min H S V --hsv-max H S V).
"""
import argparse
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.pipeline import abrir_fonte  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    args = ap.parse_args()

    cap = abrir_fonte(args.video)
    j = "calibrar HSV (q = sair)"
    cv2.namedWindow(j)
    padrao = {"H min": 35, "S min": 80, "V min": 60,
              "H max": 85, "S max": 255, "V max": 255}
    for nome, v in padrao.items():
        cv2.createTrackbar(nome, j, v, 179 if nome.startswith("H") else 255, lambda _: None)

    pausado, frame = False, None
    while True:
        if not pausado or frame is None:
            ok, f = cap.read()
            if not ok:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            frame = f
        lo = np.array([cv2.getTrackbarPos(n, j) for n in ("H min", "S min", "V min")])
        hi = np.array([cv2.getTrackbarPos(n, j) for n in ("H max", "S max", "V max")])
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        m = cv2.inRange(hsv, lo, hi)
        lado = np.hstack([frame, cv2.cvtColor(m, cv2.COLOR_GRAY2BGR)])
        esc = min(1.0, 1200 / lado.shape[1])
        cv2.imshow(j, cv2.resize(lado, None, fx=esc, fy=esc))
        k = cv2.waitKey(33) & 0xFF
        if k == ord(" "):
            pausado = not pausado
        if k == ord("q"):
            break
    cv2.destroyAllWindows()
    print("--hsv-min", *lo, "--hsv-max", *hi)


if __name__ == "__main__":
    main()
