# Quadro de integração

Cada módulo que coloca um modelo em uso foi avaliado pelos 5 pilares de Model Governance vistos na disciplina. Cluster e Computação Quântica ficam fora do quadro porque são análises e não colocam modelo em uso.

Legenda: **Sim** = existe evidência no repositório · **Parcial** = existe, mas incompleto · **Não** = não foi feito ou não há evidência

| Módulo | Integra com o OuviAí? | Rastreabilidade | Reprodutibilidade | Equidade | Explicabilidade | Monitoramento |
| --- | --- | --- | --- | --- | --- | --- |
| IoT · OuviAí | É o OuviAí | Parcial | Parcial | Não | Não | Parcial |
| RPA · Robô Cuidador | Sim, consome os eventos | Sim | Sim | Não | Parcial | Parcial |
| PLN · assistente de voz | Não | Parcial | Não | Não | Parcial | Parcial |
| GenAI · RAG | Não | Parcial | Sim | Não | Parcial | Não |
| Visão Computacional | Não, alimenta o Front-end | Parcial | Parcial | Não | Não | Não |
| Front-end · Manutenção Urbana | Não | Não | Sim | Não | Não | Parcial |

## Evidência de cada "Sim" e "Parcial"

| Módulo | Pilar | Evidência |
| --- | --- | --- |
| IoT | Rastreabilidade | Projeto no Edge Impulse com dados e versões do impulse |
| IoT | Reprodutibilidade | Divisão fixa de 45 áudios de treino e 15 de teste, descrita no relatório |
| IoT | Monitoramento | 15 tentativas ao vivo registradas no relatório e em vídeo; não há monitoramento contínuo |
| RPA | Rastreabilidade | Log por etapa em `RPA/rpa-ouviai/exemplos_saida/` |
| RPA | Reprodutibilidade | Dados sintéticos gerados por script e testes em `RPA/rpa-ouviai/tests/` |
| RPA | Explicabilidade | Model Card e lista de erros comentados; não há explicação por decisão |
| RPA | Monitoramento | Métricas por execução no JSON de saída; não há alerta automático |
| PLN | Rastreabilidade | Latência registrada por etapa, segundo o relatório |
| PLN | Explicabilidade | Resposta ancorada nos trechos recuperados pelo RAG |
| PLN | Monitoramento | Painel de latência na interface |
| GenAI | Rastreabilidade | Metadado de fonte mantido em cada trecho |
| GenAI | Reprodutibilidade | Notebook com as saídas das 10 perguntas de teste e temperatura 0 |
| GenAI | Explicabilidade | Abstenção padrão quando o contexto não tem a resposta |
| Visão Computacional | Rastreabilidade | Notebook de treino no repositório |
| Visão Computacional | Reprodutibilidade | O notebook treina e salva o modelo, mas a avaliação no conjunto de teste não está nele |
| Front-end | Reprodutibilidade | `docker compose up` e testes com pytest em `citizentech/tests/` |
| Front-end | Monitoramento | Painel com o percentual de relatos corrigidos pelo cidadão |

## O que não foi integrado

- A solução ficou com três temas: OuviAí (IoT e RPA), serviços públicos por voz e texto (PLN e GenAI) e manutenção urbana (Front-end e Visão Computacional).
- O contrato de integração prevê que PLN e GenAI troquem dados com o Robô Cuidador e que o Front-end mostre os eventos do OuviAí. Nada disso foi implementado.
- PLN e GenAI têm bases de conhecimento separadas sobre o mesmo assunto (SUS e serviços do gov.br), sem fonte comum.
- Não existe uma política única de dados sensíveis: o PLN roda modelos locais para não enviar voz a terceiros, e o GenAI envia as perguntas para a API da OpenAI.
- Nenhum modelo tem medição de equidade, por exemplo acerto do OuviAí em casas diferentes ou WER do assistente por faixa etária e sotaque.
