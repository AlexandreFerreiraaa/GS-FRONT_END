# Model Card · Classificador de sons do OuviAí

Seções no formato de Mitchell et al. (2019). Os campos marcados com **PREENCHER** dependem do projeto no Edge Impulse.

## 1. Detalhes do modelo

| Campo | Valor |
| --- | --- |
| Nome | OuviAí · sons domésticos |
| Versão | **PREENCHER** (versão do impulse no Edge Impulse) |
| Tipo | Áudio 16 kHz mono, bloco MFE, rede convolucional (CNN) |
| Classes | campainha, batida_porta, ambiente |
| Projeto | **PREENCHER: link público do Edge Impulse** |
| Autores | Alexandre Ferreira, Carlos Eduardo, Filipe Melo |
| Objetivo | Avisar uma pessoa com deficiência auditiva quando alguém toca a campainha ou bate na porta |

## 2. Uso pretendido

- Adequado: apoio no dia a dia, com o aviso aparecendo no celular.
- Inadequado: substituir alarme de incêndio, alerta de emergência ou qualquer sistema de segurança.
- O áudio é processado no próprio celular, pelo navegador (Deployment → Run this model). **PREENCHER: confirmar que nenhum áudio é salvo ou enviado.**

## 3. Dados de treino

- 20 gravações de 5 segundos por classe: 15 para treino e 5 para teste.
- Origem das gravações: **PREENCHER** (onde foram gravadas e por quem).
- Limitação: poucas casas e poucos modelos de campainha, então o modelo pode errar em outro ambiente.

## 4. Métricas de desempenho

| Métrica | Valor |
| --- | --- |
| Acurácia no teste (Model testing) | **PREENCHER** |
| Acertos ao vivo no celular | **PREENCHER** de 15 |
| Falsos positivos na classe ambiente | **PREENCHER** |

A probabilidade mostrada na tela é a confiança de uma previsão, não a acurácia do modelo.

## 5. Considerações éticas

- Voz é dado sensível pela LGPD. Gravações de treino com pessoas falando ao fundo precisam do consentimento de quem aparece nelas (ver [`termo-consentimento-gravacoes.md`](termo-consentimento-gravacoes.md)).
- Um falso negativo (campainha não detectada) deixa a pessoa sem o aviso, e é o erro que mais pesa para esse público.

## 6. Limitações e recomendações

- Testar em outras casas antes de qualquer uso real.
- Um som novo, como uma campainha diferente, é data drift: o modelo precisa de novas gravações e novo treino.
- Medir o acerto separado por ambiente (casa silenciosa, casa com TV ligada, rua barulhenta).
