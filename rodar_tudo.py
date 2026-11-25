"""
Roda todos os experimentos e gera todos os vídeos. Funciona no Windows,
no Linux e no macOS.

Uso:
    python rodar_tudo.py              # tudo (~3 min)
    python rodar_tudo.py --sem-video  # só tabelas e figuras (mais rápido)

Gera, em resultados/:
    <experimento>/tabela.md, figuras e video_*.mp4
    videos/                vídeos de rastreamento (velocidade normal)
    videos/camera_lenta/   os mesmos, em câmera lenta e só com a bola
    logs/                  CSV quadro a quadro
    video_todos_os_experimentos.mp4 e video_entrega.mp4 (precisam do ffmpeg)
"""
import argparse
import glob
import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable          # o mesmo Python que está rodando este script


def rodar(*args):
    subprocess.run([PY, *args], cwd=RAIZ, check=True)


def nome(caminho):
    return os.path.splitext(os.path.basename(caminho))[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sem-video", action="store_true",
                    help="não gera os vídeos explicativos dos experimentos")
    args = ap.parse_args()
    if args.sem_video:
        os.environ["SEM_VIDEO"] = "1"   # lido por experimentos/video_util.py
    t0 = time.time()

    print("== experimentos ==")
    for script in sorted(glob.glob(os.path.join(RAIZ, "experimentos", "[1-7]_*.py"))):
        print("->", os.path.basename(script))
        rodar(script)

    print("== videos de rastreamento ==")
    res = os.path.join(RAIZ, "resultados")
    os.makedirs(os.path.join(res, "videos", "camera_lenta"), exist_ok=True)
    os.makedirs(os.path.join(res, "logs"), exist_ok=True)
    videos = sorted(glob.glob(os.path.join(RAIZ, "videos", "*.mp4")))
    for v in videos:
        n = nome(v)
        modelos = ["cv", "ca"] if n.startswith("lancamento") else ["cv"]
        for m in modelos:
            rodar("rastrear.py", "--video", v, "--modelo", m, "--sem-janela",
                  "--salvar", os.path.join(res, "videos", f"{n}_{m}.mp4"),
                  "--csv", os.path.join(res, "logs", f"{n}_{m}.csv"))

    print("== videos em camera lenta (so os trechos com a bola) ==")
    for v in videos:
        n = nome(v)
        if n.startswith("oclusao"):
            rodar("rastrear.py", "--video", v, "--sem-janela", "--camera-lenta", "4",
                  "--so-trechos-com-bola",
                  "--salvar", os.path.join(res, "videos", "camera_lenta", f"{n}_cv_lento4x.mp4"))
        elif n in ("lancamento_1", "lancamento_2", "lancamento_horizontal"):
            for m in ("cv", "ca"):
                rodar("rastrear.py", "--video", v, "--modelo", m, "--sem-janela",
                      "--camera-lenta", "8", "--so-trechos-com-bola",
                      "--salvar", os.path.join(res, "videos", "camera_lenta", f"{n}_{m}_lento8x.mp4"))

    if not args.sem_video:
        sys.path.insert(0, os.path.join(RAIZ, "experimentos"))
        sys.path.insert(0, RAIZ)
        from video_util import emendar_videos
        print("== video unico com todos os experimentos ==")
        exps = sorted(glob.glob(os.path.join(res, "[1-7]_*", "video_*.mp4")))
        if exps and emendar_videos(exps, os.path.join(res, "video_todos_os_experimentos.mp4")):
            print("video: resultados/video_todos_os_experimentos.mp4")
            print("== video de entrega ==")
            rodar(os.path.join("ferramentas", "montar_video_entrega.py"))

    print(f"pronto em {time.time() - t0:.0f} s: veja a pasta resultados/")


if __name__ == "__main__":
    main()
