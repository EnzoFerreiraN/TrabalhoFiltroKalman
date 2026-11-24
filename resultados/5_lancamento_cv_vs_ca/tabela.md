### Resumo CV x CA

| video | modelo | quadros com bola | erro medio pred. 1 quadro (px) | erro max pred. 1 quadro (px) | ay final estimado (px/q^2) | g da parabola (px/q^2) |
|---|---|---|---|---|---|---|
| lancamento_horizontal | CV | 13 | 14.71 | 57.19 | - | 5.22 |
| lancamento_horizontal | CA | 13 | 9.36 | 57.19 | 5.41 | 5.22 |
| lancamento_1 | CV | 9 | 14.99 | 42.93 | - | 6.00 |
| lancamento_1 | CA | 9 | 7.86 | 42.93 | 6.04 | 6.00 |
| lancamento_2 | CV | 11 | 10.77 | 35.45 | - | 3.75 |
| lancamento_2 | CA | 11 | 9.23 | 35.45 | 4.16 | 3.75 |

### Predicao k quadros a frente

| video | modelo | k | n | erro medio (px) |
|---|---|---|---|---|
| lancamento_horizontal | CV | 1 | 9 | 11.04 |
| lancamento_horizontal | CV | 2 | 8 | 24.32 |
| lancamento_horizontal | CV | 3 | 7 | 42.57 |
| lancamento_horizontal | CV | 4 | 6 | 65.62 |
| lancamento_horizontal | CV | 5 | 5 | 93.14 |
| lancamento_horizontal | CV | 6 | 4 | 125.94 |
| lancamento_horizontal | CA | 1 | 9 | 4.52 |
| lancamento_horizontal | CA | 2 | 8 | 9.06 |
| lancamento_horizontal | CA | 3 | 7 | 14.97 |
| lancamento_horizontal | CA | 4 | 6 | 22.66 |
| lancamento_horizontal | CA | 5 | 5 | 32.47 |
| lancamento_horizontal | CA | 6 | 4 | 45.75 |
| lancamento_1 | CV | 1 | 5 | 12.70 |
| lancamento_1 | CV | 2 | 4 | 28.04 |
| lancamento_1 | CV | 3 | 3 | 49.58 |
| lancamento_1 | CV | 4 | 2 | 77.97 |
| lancamento_1 | CV | 5 | 1 | 112.28 |
| lancamento_1 | CV | 6 | 0 | nan |
| lancamento_1 | CA | 1 | 5 | 2.03 |
| lancamento_1 | CA | 2 | 4 | 3.86 |
| lancamento_1 | CA | 3 | 3 | 7.59 |
| lancamento_1 | CA | 4 | 2 | 15.28 |
| lancamento_1 | CA | 5 | 1 | 31.48 |
| lancamento_1 | CA | 6 | 0 | nan |
| lancamento_2 | CV | 1 | 7 | 9.02 |
| lancamento_2 | CV | 2 | 6 | 19.58 |
| lancamento_2 | CV | 3 | 5 | 33.79 |
| lancamento_2 | CV | 4 | 4 | 50.68 |
| lancamento_2 | CV | 5 | 3 | 68.60 |
| lancamento_2 | CV | 6 | 2 | 87.43 |
| lancamento_2 | CA | 1 | 7 | 7.11 |
| lancamento_2 | CA | 2 | 6 | 14.33 |
| lancamento_2 | CA | 3 | 5 | 24.04 |
| lancamento_2 | CA | 4 | 4 | 33.81 |
| lancamento_2 | CA | 5 | 3 | 39.79 |
| lancamento_2 | CA | 6 | 2 | 36.42 |

### Extensao: previsao do ponto de cruzamento da linha

| video | modelo | quadros antes do cruzamento | erro em y (px) |
|---|---|---|---|
| lancamento_horizontal | CV | 7.70 | 188.45 |
| lancamento_horizontal | CV | 6.70 | 152.74 |
| lancamento_horizontal | CV | 5.70 | 113.95 |
| lancamento_horizontal | CV | 4.70 | 79.59 |
| lancamento_horizontal | CV | 3.70 | 56.13 |
| lancamento_horizontal | CV | 2.70 | 36.90 |
| lancamento_horizontal | CV | 1.70 | 21.16 |
| lancamento_horizontal | CV | 0.70 | 8.66 |
| lancamento_horizontal | CA | 7.70 | 52.67 |
| lancamento_horizontal | CA | 6.70 | 137.98 |
| lancamento_horizontal | CA | 5.70 | 65.23 |
| lancamento_horizontal | CA | 4.70 | 34.62 |
| lancamento_horizontal | CA | 3.70 | 18.05 |
| lancamento_horizontal | CA | 2.70 | 8.13 |
| lancamento_horizontal | CA | 1.70 | 2.97 |
| lancamento_horizontal | CA | 0.70 | 1.14 |
| lancamento_1 | CV | 4.40 | 82.50 |
| lancamento_1 | CV | 3.40 | 60.84 |
| lancamento_1 | CV | 2.40 | 37.92 |
| lancamento_1 | CV | 1.40 | 18.36 |
| lancamento_1 | CV | 0.40 | 6.89 |
| lancamento_1 | CA | 4.40 | 46.14 |
| lancamento_1 | CA | 3.40 | 10.30 |
| lancamento_1 | CA | 2.40 | 3.63 |
| lancamento_1 | CA | 1.40 | 0.09 |
| lancamento_1 | CA | 0.40 | 0.06 |
| lancamento_2 | CV | 6.10 | 74.27 |
| lancamento_2 | CV | 5.10 | 56.01 |
| lancamento_2 | CV | 4.10 | 47.28 |
| lancamento_2 | CV | 3.10 | 35.56 |
| lancamento_2 | CV | 2.10 | 20.38 |
| lancamento_2 | CV | 1.10 | 7.65 |
| lancamento_2 | CV | 0.10 | 2.19 |
| lancamento_2 | CA | 6.10 | 44.94 |
| lancamento_2 | CA | 5.10 | 3.15 |
| lancamento_2 | CA | 4.10 | 0.80 |
| lancamento_2 | CA | 3.10 | 2.11 |
| lancamento_2 | CA | 2.10 | 3.10 |
| lancamento_2 | CA | 1.10 | 3.43 |
| lancamento_2 | CA | 0.10 | 0.99 |

