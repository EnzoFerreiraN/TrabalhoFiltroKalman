"""
Converte os vídeos do celular para o formato usado no trabalho
(funciona no Windows, no Linux e no macOS; precisa do ffmpeg):
    - H.264 (o HEVC do celular não abre em todo lugar)
    - 30 fps constantes (o celular grava com taxa variável; o filtro usa dt = 1 quadro)
    - 360x640 (vertical) ou 640x360 (horizontal), sem distorcer nem cortar;
      são menos pixels que 640x480, então o requisito de desempenho vale
    - sem áudio

Uso:
    python ferramentas/converter_videos.py                       # videos_originais -> videos
    python ferramentas/converter_videos.py PASTA_ORIGEM PASTA_DESTINO
"""
import glob
import os
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    origem = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "videos_originais")
    destino = sys.argv[2] if len(sys.argv) > 2 else os.path.join(RAIZ, "videos")
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg não encontrado (veja a seção de instalação do README)")
    os.makedirs(destino, exist_ok=True)
    arquivos = sorted(glob.glob(os.path.join(origem, "*.mp4")) +
                      glob.glob(os.path.join(origem, "*.MP4")) +
                      glob.glob(os.path.join(origem, "*.mov")) +
                      glob.glob(os.path.join(origem, "*.MOV")))
    if not arquivos:
        sys.exit(f"nenhum vídeo em {origem}")
    for f in arquivos:
        saida = os.path.join(destino, os.path.splitext(os.path.basename(f))[0] + ".mp4")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f,
                        "-vf", "scale='if(gt(iw,ih),640,360)':'if(gt(iw,ih),360,640)'",
                        "-r", "30", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                        "-an", saida], check=True)
        print("convertido:", f, "->", saida)


if __name__ == "__main__":
    main()
