# Cluster Computing · Simulação no iSPD

- Relatório: [`GSCLUSTER1.pdf`](GSCLUSTER1.pdf)

500 tarefas independentes (500 MFLOP e 5 Mbits cada), escalonador RoundRobin, workers de 1000 MFLOPS, rede de 100 Mbps e latência de 0,001 s. Só o número de workers muda.

| Indicador | 2 workers | 4 workers |
| --- | --- | --- |
| Total Simulated Time | 63,38 s | 34,27 s |
| Tarefas por worker | 250 | 125 |
| Ociosidade | 1,19% | 8,22% |
| Redução de tempo | | 45,93% |
| Speedup (T2/T4) | | 1,85x |
