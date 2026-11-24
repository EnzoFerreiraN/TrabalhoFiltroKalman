### Validacao contra cv2.KalmanFilter

| video | modelo | quadros comparados | dif. relativa max em x | dif. relativa max em P | resultado (tol. 1e-9) |
|---|---|---|---|---|---|
| movimento_mao | CV | 845 | 2.21e-16 | 3.21e-15 | OK |
| movimento_mao | CA | 844 | 2.95e-11 | 2.59e-10 | OK |
| oclusao_grande | CV | 103 | 5.08e-15 | 1.00e-13 | OK |
| oclusao_grande | CA | 103 | 1.29e-12 | 2.98e-12 | OK |
| lancamento_horizontal | CV | 43 | 8.98e-16 | 3.21e-15 | OK |
| lancamento_horizontal | CA | 43 | 1.06e-14 | 1.95e-13 | OK |

