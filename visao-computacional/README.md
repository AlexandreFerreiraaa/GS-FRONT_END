# Visão Computacional · Fissuras em concreto

Classificação binária (com e sem fissura) para a triagem de manutenção urbana do Front-end.

- Notebook: [`Visao computacional.ipynb`](Visao%20computacional.ipynb) (Google Colab)
- Relatório: [`RELATÓRIO VISAO.pdf`](RELAT%C3%93RIO%20VISAO.pdf)
- Vídeo: https://youtu.be/RdhAdSJ7MaY

Base Concrete Crack Images for Classification, MobileNetV2 pré-treinada no ImageNet com camada densa sigmoide, imagens 224 x 224, limiar 0,50. O modelo salvo (`modelo.keras`) é o que o Front-end carrega em `citizentech/models/`.

As células da Etapa 8, no fim do notebook, calculam precisão, recall, F1, matriz de confusão e latência no conjunto de teste (900 imagens na divisão 70/15/15 de 6.000).
