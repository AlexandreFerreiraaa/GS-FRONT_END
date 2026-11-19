# Avaliação do classificador de triagem

Global Solution 2026.2 · CitizenTech · OuviAí · AI for Robotic Process Automation (RPA + IA)  
Grupo: Alexandre Ferreira (RM 565626) · Carlos Eduardo (RM 555812) · Filipe Melo (RM 564571)

- Treino: 360 frases sintéticas (templates) · Teste: 48 frases escritas à mão, vocabulário diferente
- **Acurácia: 89.6%** · F1 macro: 0.895
- Limiar de revisão humana: 45% → 16 de 48 frases iriam para revisão
- Acurácia nas frases decididas automaticamente: 96.9%
- Regra de emergência: 10/10 corretas 

## Limiar de confiança: cobertura automática × acurácia
| Limiar | Decidido pelo robô | Acurácia nesses casos |
|---|---|---|
| 0% | 100% | 89.6% |
| 30% | 94% | 91.1% |
| 45% | 67% | 96.9% |
| 60% | 50% | 95.8% |
| 75% | 25% | 91.7% |

## Relatório por classe
```
                       precision    recall  f1-score   support

        beneficio_bpc       1.00      0.75      0.86         8
       direitos_idoso       0.88      0.88      0.88         8
          fora_escopo       1.00      0.88      0.93         8
       golpe_suspeito       0.78      0.88      0.82         8
       saude_auditiva       0.89      1.00      0.94         8
transporte_gratuidade       0.89      1.00      0.94         8

             accuracy                           0.90        48
            macro avg       0.91      0.90      0.90        48
         weighted avg       0.91      0.90      0.90        48

```

## Matriz de confusão
| real \ previsto | beneficio_ | direitos_i | fora_escop | golpe_susp | saude_audi | transporte |
|---|---|---|---|---|---|---|
| beneficio_bpc | 6 | 1 | 0 | 1 | 0 | 0 |
| direitos_idoso | 0 | 7 | 0 | 0 | 0 | 1 |
| fora_escopo | 0 | 0 | 7 | 1 | 0 | 0 |
| golpe_suspeito | 0 | 0 | 0 | 7 | 1 | 0 |
| saude_auditiva | 0 | 0 | 0 | 0 | 8 | 0 |
| transporte_gratuidade | 0 | 0 | 0 | 0 | 0 | 8 |

## Erros
- "o cras falou que eu preciso atualizar o cadastro senão perco o dinheiro do loas" → previsto **golpe_suspeito** (43%), esperado beneficio_bpc
- "quem tem direito ao amparo assistencial ao idoso" → previsto **direitos_idoso** (39%), esperado beneficio_bpc
- "minha nora fica com meu cartão e não me deixa sair de casa" → previsto **transporte_gratuidade** (24%), esperado direitos_idoso
- "uma mulher disse que é do posto e vai vir buscar meu aparelho auditivo pra conserto" → previsto **saude_auditiva** (80%), esperado golpe_suspeito
- "como desbloqueia o celular que esqueci a senha" → previsto **golpe_suspeito** (39%), esperado fora_escopo