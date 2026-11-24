#!/usr/bin/env bash
# Roda todos os experimentos e gera os vídeos de saída com as sobreposições.
# Uso: bash rodar_tudo.sh
set -e
cd "$(dirname "$0")"
PY=${PYTHON:-python3}

echo "== experimentos =="
$PY experimentos/1_ruido_do_detector.py
$PY experimentos/2_bruto_vs_filtrado.py
$PY experimentos/3_teimoso_vs_nervoso.py
$PY experimentos/4_oclusao.py
$PY experimentos/5_lancamento_cv_vs_ca.py
$PY experimentos/6_validacao_opencv.py
$PY experimentos/7_desempenho_fps.py

echo "== videos de saida =="
mkdir -p resultados/videos resultados/logs
for v in videos/*.mp4; do
  n=$(basename "$v" .mp4)
  $PY rastrear.py --video "$v" --sem-janela \
      --salvar "resultados/videos/${n}_cv.mp4" --csv "resultados/logs/${n}_cv.csv"
  case "$n" in
    *lancamento*)
      $PY rastrear.py --video "$v" --modelo ca --sem-janela \
          --salvar "resultados/videos/${n}_ca.mp4" --csv "resultados/logs/${n}_ca.csv" ;;
  esac
done
echo "== videos em camera lenta (so os trechos com a bola) =="
mkdir -p resultados/videos/camera_lenta
for v in videos/oclusao_*.mp4; do
  n=$(basename "$v" .mp4)
  $PY rastrear.py --video "$v" --sem-janela --camera-lenta 4 --so-trechos-com-bola \
      --salvar "resultados/videos/camera_lenta/${n}_cv_lento4x.mp4"
done
for v in videos/lancamento_1.mp4 videos/lancamento_2.mp4 videos/lancamento_horizontal.mp4; do
  n=$(basename "$v" .mp4)
  for m in cv ca; do
    $PY rastrear.py --video "$v" --modelo $m --sem-janela --camera-lenta 8 \
        --so-trechos-com-bola --salvar "resultados/videos/camera_lenta/${n}_${m}_lento8x.mp4"
  done
done
echo "pronto: veja a pasta resultados/"
