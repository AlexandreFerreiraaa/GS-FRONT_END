# Model Card · Classificador de triagem do Robô Cuidador

Seções no formato de Mitchell et al. (2019), como vimos na disciplina.

## 1. Detalhes do modelo

| Campo | Valor |
| --- | --- |
| Nome | Triagem de pedidos OuviAí |
| Versão | 1.0.0 |
| Tipo | TF-IDF + Regressão Logística (scikit-learn), com regra de emergência por palavras-chave antes do modelo |
| Código | `RPA/rpa-ouviai/robo/etapas/triagem.py` |
| Autores | Alexandre Ferreira, Carlos Eduardo, Filipe Melo |
| Objetivo | Classificar o tema de um pedido do cidadão e sugerir o canal certo (CRAS, INSS, UBS, Disque 100) |

## 2. Uso pretendido

- Adequado: separar pedidos de uma pessoa idosa com perda auditiva em seis temas e avisar o cuidador.
- Inadequado: decidir sozinho sobre benefício, saúde ou denúncia. O modelo sugere, uma pessoa confirma.
- Emergência não passa pelo modelo: a regra de palavras-chave tem prioridade e manda acionar 192, 193 ou 190.

## 3. Dados de treino

- Treino: 360 frases sintéticas geradas por templates (`scripts/gerar_dados_sinteticos.py`).
- Teste: 48 frases escritas à mão, com vocabulário diferente do treino, 8 por classe.
- Nenhum dado real de pessoa foi usado.
- Limitação: frases sintéticas não cobrem gírias, erros de transcrição do STT nem variações regionais.

## 4. Métricas de desempenho

| Métrica | Valor |
| --- | --- |
| Acurácia no teste | 89,6% |
| F1 macro | 0,895 |
| Limiar de revisão humana | 45% de confiança |
| Pedidos que iriam para revisão | 16 de 48 |
| Acurácia nos pedidos decididos pelo robô | 96,9% |
| Regra de emergência | 10 de 10 corretas |

Relatório por classe e matriz de confusão: `RPA/rpa-ouviai/exemplos_saida/metricas.md`.

Não há métricas por subgrupo (idade, região, escolaridade), porque o conjunto de teste não tem esses atributos.

## 5. Considerações éticas

- O erro mais grave observado foi um golpe classificado como saúde auditiva com 80% de confiança, ou seja, acima do limiar e sem revisão humana. Um golpe que passa como pedido legítimo pode causar dano financeiro à pessoa idosa.
- Texto livre do cidadão passa pelo mascaramento de dados pessoais antes de ser salvo, enviado por e-mail ou mandado a um LLM (`robo/privacidade.py`).
- O público é vulnerável (idoso, com deficiência auditiva), então erros caem sobre quem tem menos condição de contestar.

## 6. Limitações e recomendações

- Não usar com pedidos reais antes de testar com frases reais transcritas pelo assistente de voz.
- Revisar o limiar de 45% para a classe `golpe_suspeito`, que precisa de recall alto.
- Medir o desempenho por grupo quando houver dados reais.
- Monitorar a taxa de pedidos enviados para revisão: se subir, o vocabulário mudou e o modelo precisa ser retreinado.
