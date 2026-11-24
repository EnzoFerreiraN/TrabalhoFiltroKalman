### Ruido de medicao do detector

| situacao | desvio x (px) | desvio y (px) | n quadros |
|---|---|---|---|
| bola parada | 0.07 | 0.05 | 392 |
| bola em movimento (residuo) | 0.53 | 0.46 | 816 |

Valor adotado: sigma_m = 2.0 px (Sm = sigma_m^2 * I).

A bola parada da o limite inferior. Em movimento o residuo e maior, e ainda subestima o ruido real, porque a suavizacao absorve parte dele e porque os quadros com oclusao parcial (centroide deslocado) sao poucos. Adotamos uma margem de ~4x o residuo. O comportamento do filtro depende da razao Sd/Sm, que e variada no experimento 3.
