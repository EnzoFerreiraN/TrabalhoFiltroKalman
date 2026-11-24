#!/usr/bin/env bash
# Converte os vídeos do celular para o formato usado no trabalho:
#   - H.264 (o HEVC do celular não abre em todo lugar)
#   - 30 fps constantes (o celular grava com taxa variável; o filtro usa dt = 1 quadro)
#   - 360x640 (vertical) ou 640x360 (horizontal), sem distorcer nem cortar;
#     são menos pixels que 640x480, então o requisito de desempenho vale
#   - sem áudio
# Uso: bash ferramentas/converter_videos.sh pasta_dos_originais pasta_de_saida
set -e
ORIG=${1:-videos_originais}
DEST=${2:-videos}
mkdir -p "$DEST"
for f in "$ORIG"/*.mp4; do
  ffmpeg -y -v error -i "$f" \
    -vf "scale='if(gt(iw,ih),640,360)':'if(gt(iw,ih),360,640)'" \
    -r 30 -c:v libx264 -crf 18 -pix_fmt yuv420p -an "$DEST/$(basename "$f")"
  echo "convertido: $f"
done
