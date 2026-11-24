### Bruta x filtrada (sensor real: referencia = Savitzky-Golay centrado (nao causal); sensor degradado: referencia = deteccao limpa)

| video | sensor | trajetoria | erro medio (px) | rugosidade (px/q^2) | atraso (quadros) | bola rejeitada (quadros) |
|---|---|---|---|---|---|---|
| movimento_mao | real | bruta | 0.43 | 1.63 | -1.13e-03 | - |
| movimento_mao | real | filtrada | 0.76 | 1.61 | 8.69e-03 | 1 |
| movimento_mao | +3px | bruta | 3.73 | 10.48 | -0.02 | - |
| movimento_mao | +3px | filtrada | 3.09 | 5.44 | 0.01 | 38 |
| oclusao_pequeno_1 | real | bruta | 0.53 | 1.45 | -6.66e-03 | - |
| oclusao_pequeno_1 | real | filtrada | 0.56 | 1.22 | -0.02 | 8 |
| oclusao_pequeno_1 | +3px | bruta | 3.65 | 9.30 | 0.01 | - |
| oclusao_pequeno_1 | +3px | filtrada | 3.03 | 4.88 | -3.96e-03 | 8 |

### Bola parada (bola_parada) - variancia da posicao

| sensor | trajetoria | var x (px^2) | var y (px^2) |
|---|---|---|---|
| real | bruta | 4.46e-03 | 2.69e-03 |
| real | filtrada | 4.45e-03 | 2.69e-03 |
| +3px | bruta | 9.33 | 9.25 |
| +3px | filtrada | 5.69 | 5.15 |

