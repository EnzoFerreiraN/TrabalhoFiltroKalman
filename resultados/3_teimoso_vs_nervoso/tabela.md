### A - compromisso suavidade x atraso (sem gating)

| video | sensor | filtro | sigma_d | erro medio (px) | rugosidade (px/q^2) | atraso (quadros) |
|---|---|---|---|---|---|---|
| movimento_mao | real | bruta (detector) | - | 0.43 | 1.63 | -1.13e-03 |
| movimento_mao | real | teimoso | 0.30 | 4.63 | 1.62 | 0.25 |
| movimento_mao | real | intermediario | 2.00 | 0.77 | 1.61 | 8.69e-03 |
| movimento_mao | real | nervoso | 10.00 | 0.46 | 1.62 | -7.04e-04 |
| movimento_mao | +3px | bruta (detector) | - | 3.73 | 10.48 | -0.02 |
| movimento_mao | +3px | teimoso | 0.30 | 7.60 | 2.93 | 0.46 |
| movimento_mao | +3px | intermediario | 2.00 | 3.10 | 5.49 | 7.92e-03 |
| movimento_mao | +3px | nervoso | 10.00 | 3.47 | 8.50 | -0.02 |
| oclusao_pequeno_1 | real | bruta (detector) | - | 0.53 | 1.45 | -6.66e-03 |
| oclusao_pequeno_1 | real | teimoso | 0.30 | 1.69 | 1.33 | -0.08 |
| oclusao_pequeno_1 | real | intermediario | 2.00 | 1.25 | 3.86 | 0.10 |
| oclusao_pequeno_1 | real | nervoso | 10.00 | 1.61 | 6.53 | 0.19 |
| oclusao_pequeno_1 | +3px | bruta (detector) | - | 3.65 | 9.30 | 0.01 |
| oclusao_pequeno_1 | +3px | teimoso | 0.30 | 3.19 | 2.69 | -0.12 |
| oclusao_pequeno_1 | +3px | intermediario | 2.00 | 3.79 | 6.57 | 0.10 |
| oclusao_pequeno_1 | +3px | nervoso | 10.00 | 4.36 | 8.84 | 0.14 |

### B - robustez do gating (regiao de busca 99% + raio minimo 20 px)

| video | sensor | filtro | sigma_d | bola rejeitada (quadros) | trilhas perdidas |
|---|---|---|---|---|---|
| movimento_mao | real | teimoso | 0.30 | 195 | 6 |
| movimento_mao | real | intermediario | 2.00 | 1 | 1 |
| movimento_mao | real | nervoso | 10.00 | 1 | 1 |
| movimento_mao | +3px | teimoso | 0.30 | 258 | 4 |
| movimento_mao | +3px | intermediario | 2.00 | 38 | 2 |
| movimento_mao | +3px | nervoso | 10.00 | 1 | 1 |
| oclusao_pequeno_1 | real | teimoso | 0.30 | 8 | 1 |
| oclusao_pequeno_1 | real | intermediario | 2.00 | 8 | 1 |
| oclusao_pequeno_1 | real | nervoso | 10.00 | 8 | 1 |
| oclusao_pequeno_1 | +3px | teimoso | 0.30 | 8 | 1 |
| oclusao_pequeno_1 | +3px | intermediario | 2.00 | 8 | 1 |
| oclusao_pequeno_1 | +3px | nervoso | 10.00 | 8 | 1 |

