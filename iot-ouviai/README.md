# Physical Computing (IoT) · OuviAí

Classificador de sons domésticos para avisar uma pessoa com deficiência auditiva, treinado no Edge Impulse e executado no navegador do celular (Deployment → Run this model).

- Relatório: [`Physical Computing.pdf`](Physical%20Computing.pdf)
- Vídeo do teste ao vivo: https://youtube.com/shorts/_qvth7-RmWA
- Áudio 16 kHz mono, bloco MFE, rede convolucional
- 60 gravações feitas no celular: 45 de treino e 15 de teste (15 e 5 por classe)

## Resultados

| Etapa | Resultado |
| --- | --- |
| Validação no treino | 77,8% |
| Model testing (áudios inéditos) | 33,33% |
| 15 tentativas ao vivo no celular | 14 acertos (93,33%) |

A classe batida de porta foi confundida com campainha no Model testing. Nas 5 tentativas de ambiente ao vivo, o modelo devolveu "No event detected" e isso foi contado como acerto.

Os áudios não ficam no repositório nem são enviados para a nuvem durante a execução.

Integração: cada detecção vira um `evento_som` no formato do [contrato de integração](../RPA/rpa-ouviai/contrato_integracao_ouviai.json), que o Robô Cuidador consome.
