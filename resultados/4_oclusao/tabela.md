### A - Oclusoes reais

| video | modelo | descarta bola parcial | max sem medicao | inicio (quadro) | duracao (quadros) | trilha recuperada | quadros cobertos pela predicao | erro da predicao ao reaparecer (px) | raio da regiao de busca (px) |
|---|---|---|---|---|---|---|---|---|---|
| oclusao_pequeno_2 | CV | nao | 30 | 116 | 2 | sim | 2 | 18.86 | 28.79 |
| oclusao_pequeno_2 | CV | sim | 30 | 115 | 3 | sim | 3 | 7.96 | 39.69 |
| oclusao_pequeno_2 | CV | sim | 10 | 115 | 3 | sim | 3 | 7.96 | 39.69 |
| oclusao_pequeno_2 | CA | nao | 30 | 116 | 1 | sim | 1 | 18.84 | 13.09 |
| oclusao_pequeno_2 | CA | sim | 30 | 115 | 3 | sim | 3 | 3.12 | 24.53 |
| oclusao_pequeno_2 | CA | sim | 10 | 115 | 3 | sim | 3 | 3.12 | 24.53 |
| oclusao_pequeno_1 | CV | nao | 30 | 87 | 3 | sim | 3 | 38.92 | 39.69 |
| oclusao_pequeno_1 | CV | sim | 30 | 86 | 6 | sim | 6 | 24.55 | 79.49 |
| oclusao_pequeno_1 | CV | sim | 10 | 86 | 6 | sim | 6 | 24.55 | 79.49 |
| oclusao_pequeno_1 | CA | nao | 30 | 87 | 19 | sim | 19 | 376.14 | 377.82 |
| oclusao_pequeno_1 | CA | sim | 30 | 86 | 14 | sim | 14 | 207.96 | 209.97 |
| oclusao_pequeno_1 | CA | sim | 10 | 86 | 10 | NAO (reiniciou) | 10 | nan | 115.84 |
| oclusao_medio_2 | CV | nao | 30 | 102 | 9 | sim | 9 | 70.10 | 127.93 |
| oclusao_medio_2 | CV | sim | 30 | 101 | 11 | sim | 11 | 18.13 | 164.30 |
| oclusao_medio_2 | CV | sim | 10 | 101 | 10 | NAO (reiniciou) | 10 | nan | 145.73 |
| oclusao_medio_2 | CA | nao | 30 | 102 | 10 | sim | 10 | 108.39 | 115.87 |
| oclusao_medio_2 | CA | sim | 30 | 101 | 11 | sim | 11 | 44.16 | 136.36 |
| oclusao_medio_2 | CA | sim | 10 | 101 | 10 | NAO (reiniciou) | 10 | nan | 115.93 |
| oclusao_medio_1 | CV | nao | 30 | 89 | 15 | sim | 15 | 59.32 | 245.63 |
| oclusao_medio_1 | CV | sim | 30 | 88 | 17 | sim | 17 | 11.10 | 290.22 |
| oclusao_medio_1 | CV | sim | 10 | 88 | 10 | NAO (reiniciou) | 10 | nan | 145.73 |
| oclusao_medio_1 | CA | nao | 30 | 89 | 15 | sim | 15 | 115.98 | 238.89 |
| oclusao_medio_1 | CA | sim | 30 | 88 | 17 | sim | 17 | 37.20 | 303.61 |
| oclusao_medio_1 | CA | sim | 10 | 88 | 10 | NAO (reiniciou) | 10 | nan | 115.84 |
| oclusao_grande | CV | nao | 30 | 126 | 24 | sim | 24 | 127.70 | 464.55 |
| oclusao_grande | CV | sim | 30 | 124 | 27 | sim | 27 | 47.62 | 547.23 |
| oclusao_grande | CV | sim | 10 | 124 | 10 | NAO (reiniciou) | 10 | nan | 145.73 |
| oclusao_grande | CA | nao | 30 | 126 | 24 | sim | 24 | 473.40 | 607.82 |
| oclusao_grande | CA | sim | 30 | 124 | 27 | sim | 27 | 228.09 | 778.24 |
| oclusao_grande | CA | sim | 10 | 124 | 10 | NAO (reiniciou) | 10 | nan | 115.83 |

### B - Oclusoes sinteticas (referencia = deteccao real escondida do filtro)

| video | modelo | N (quadros apagados) | n testes | erro medio durante a oclusao (px) | erro no ultimo quadro (px) | trilha recuperada (ate 3 quadros) |
|---|---|---|---|---|---|---|
| oclusao_pequeno_1 | CV | 5 | 20 | 2.59 | 5.00 | 95% |
| oclusao_pequeno_1 | CV | 10 | 16 | 5.64 | 11.89 | 94% |
| oclusao_pequeno_1 | CV | 15 | 14 | 8.51 | 18.49 | 93% |
| oclusao_pequeno_1 | CV | 20 | 12 | 12.30 | 27.90 | 92% |
| oclusao_pequeno_1 | CV | 30 | 8 | 22.94 | 49.04 | 100% |
| oclusao_pequeno_1 | CA | 5 | 20 | 16.58 | 22.30 | 95% |
| oclusao_pequeno_1 | CA | 10 | 16 | 28.99 | 47.12 | 94% |
| oclusao_pequeno_1 | CA | 15 | 14 | 43.35 | 78.48 | 93% |
| oclusao_pequeno_1 | CA | 20 | 11 | 23.92 | 59.41 | 91% |
| oclusao_pequeno_1 | CA | 30 | 7 | 48.02 | 124.43 | 100% |
| oclusao_medio_1 | CV | 5 | 7 | 2.77 | 5.10 | 100% |
| oclusao_medio_1 | CV | 10 | 5 | 6.39 | 13.09 | 80% |
| oclusao_medio_1 | CV | 15 | 2 | 9.06 | 21.06 | 100% |
| oclusao_medio_1 | CA | 5 | 7 | 5.48 | 9.87 | 100% |
| oclusao_medio_1 | CA | 10 | 5 | 13.16 | 28.16 | 80% |
| oclusao_medio_1 | CA | 15 | 2 | 26.09 | 66.88 | 100% |
| movimento_mao | CV | 5 | 266 | 8.60 | 16.71 | 94% |
| movimento_mao | CV | 10 | 265 | 22.38 | 51.06 | 89% |
| movimento_mao | CV | 15 | 263 | 40.34 | 94.10 | 90% |
| movimento_mao | CV | 20 | 261 | 60.03 | 137.94 | 93% |
| movimento_mao | CV | 30 | 253 | 95.60 | 200.56 | 100% |
| movimento_mao | CA | 5 | 260 | 34.88 | 48.38 | 77% |
| movimento_mao | CA | 10 | 258 | 49.96 | 95.87 | 78% |
| movimento_mao | CA | 15 | 254 | 67.66 | 159.94 | 79% |
| movimento_mao | CA | 20 | 250 | 94.52 | 246.35 | 79% |
| movimento_mao | CA | 30 | 202 | 99.10 | 259.85 | 100% |

