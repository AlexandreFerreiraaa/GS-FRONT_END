# Requisitos — Robô Cuidador OuviAí (RPA + IA)

**FIAP · Tecnólogo em Inteligência Artificial · Global Solution 2026.2 CitizenTech**
**Disciplina:** AI for Robotic Process Automation (RPA + IA)

| Integrante | RM |
|---|---|
| Alexandre Ferreira | 565626 |
| Carlos Eduardo | 555812 |
| Filipe Melo | 564571 |

Documento de requisitos do protótipo da disciplina **AI for Robotic Process Automation**, parte da Global Solution 2026.2 CitizenTech. A solução do grupo é única, e este robô é a peça que trabalha nos bastidores enquanto ninguém está olhando.

---

## 1. Problema e público

A persona é a **Dona Lúcia**, 72 anos, mora sozinha e tem perda auditiva leve a moderada, ela não escuta a campainha nem batidas na porta, tem um celular simples e uma filha que mora em outro bairro e acompanha à distância. O OuviAí já resolve o "ouvir" (classificador de sons no celular) e o "conversar" (assistente de voz com RAG), mas sobra um trabalho repetitivo que ninguém faz de forma consistente:

- juntar o que aconteceu na semana (sons, alertas, pedidos de ajuda) e avisar quem cuida;
- perceber padrões que um evento isolado não mostra, como alguém insistindo na porta, batida de madrugada ou o celular parado sem monitorar;
- separar o que é emergência, o que é golpe e o que é dúvida comum, e dizer para onde encaminhar;
- manter a base de conhecimento do assistente atualizada com as páginas oficiais (gov.br, Planalto, INSS).

É exatamente o tipo de tarefa que um robô faz melhor que uma pessoa, porque é periódica, baseada em regras e cansativa.

**ODS:** 10 (redução das desigualdades, acessibilidade para pessoa com deficiência auditiva), 3 (saúde e bem-estar, acesso ao aparelho auditivo pelo SUS) e 11 (cidades e comunidades inclusivas).

## 2. Escopo

**Dentro:** robô em Python executado por linha de comando (ou agendado), com 5 etapas, dados sintéticos, fontes públicas, LLM opcional.

**Fora:** interface gráfica (é do trabalho de Front-end), treinamento do modelo de áudio (é do trabalho de IoT), resposta ao cidadão em tempo real (é do assistente de voz), envio de alerta de emergência em tempo real (o robô é periódico e o protótipo não substitui 192/193/190).

## 3. Fluxo

```
Init (config, logs, estado)
  │
  ├─ 1. Coleta de fontes oficiais ── baixa HTML/PDF → extrai texto → hash → só reindexa o que mudou
  │                                    falhou? retry com espera → snapshot local → revisão humana
  ├─ 2. Eventos sonoros ───────────── CSV/API → valida (Pydantic) → quarentena → regras de alerta
  ├─ 3. Triagem de pedidos ────────── mascara dados pessoais → regra de emergência → modelo NLP
  │                                    confiança baixa? revisão humana
  ├─ 4. Relatórios ────────────────── Excel (7 abas) + HTML acessível + resumo (LLM ou template)
  └─ 5. Notificação ───────────────── e-mail ao cuidador, uma vez por semana (idempotente)
End (relatório de execução JSON + log)
```

## 4. Requisitos funcionais

| ID | Requisito | Onde está |
|---|---|---|
| RF01 | Coletar as fontes listadas em `config/fontes.json` (HTML e PDF) e extrair o texto útil, sem menu, rodapé e scripts | `coleta_fontes.py` |
| RF02 | Detectar mudança de conteúdo por hash SHA-256 e gravar trechos com metadados (fonte, URL, data) só das fontes alteradas, sinalizando em `reindexar.json` para o RAG do grupo | `coleta_fontes.py` |
| RF03 | Ler eventos sonoros do OuviAí por API (opcional) ou CSV exportado | `eventos.py` |
| RF04 | Validar cada evento (data, classe, confiança 0–1, dispositivo) e enviar linhas inválidas para quarentena sem parar o lote | `eventos.py` |
| RF05 | Gerar alertas por regra: insistência na porta, porta em horário noturno, dispositivo silencioso; ignorar detecções de baixa confiança | `eventos.py` |
| RF06 | Mascarar CPF, telefone, e-mail, CEP e NIS de todo texto livre antes de salvar, enviar ou classificar | `privacidade.py` |
| RF07 | Classificar pedidos do cidadão em 6 temas com modelo de NLP e sugerir o encaminhamento oficial de cada tema | `triagem.py` |
| RF08 | Marcar como emergência, por regra, pedidos com expressões de risco, com prioridade sobre o modelo | `triagem.py` |
| RF09 | Enviar para revisão humana pedidos com confiança abaixo do limiar, pedidos vazios, fontes sem conteúdo e eventos inválidos | todas as etapas |
| RF10 | Gerar planilha Excel (Resumo, Alertas, Pedidos, Eventos, Revisão humana, Fontes, Execução) e página HTML legível no celular | `relatorio.py` |
| RF11 | Gerar resumo em linguagem simples com LLM opcional, com validação da resposta e template como alternativa | `llm.py` |
| RF12 | Enviar o relatório ao cuidador por e-mail (SMTP) ou salvar `.eml` quando não houver SMTP | `notificacao.py` |

## 5. Requisitos não funcionais

| ID | Requisito | Como foi atendido |
|---|---|---|
| RNF01 | Resiliência: falha previsível não interrompe a execução | cada etapa roda isolada (`Etapa`), erro vira registro e as próximas continuam |
| RNF02 | Retry com espera | backoff exponencial (1s, 2s, 4s) só para erro de sistema; erro de negócio não é repetido |
| RNF03 | Idempotência | hash de fontes, eventos duplicados contados uma vez, e-mail no máximo uma vez por semana |
| RNF04 | Rastreabilidade | log rotativo em `logs/robo.log` e relatório JSON por execução em `saida/execucoes/` |
| RNF05 | Segredos fora do código | `.env` (ignorado pelo Git) + `.env.example` |
| RNF06 | Só ferramentas gratuitas e dados sintéticos/públicos | Python + bibliotecas open source; persona e eventos fictícios |
| RNF07 | Reprodutível | `python main.py --offline --data 2026-11-08T23:30` gera sempre o mesmo resultado |
| RNF08 | Acessibilidade do relatório | HTML com fonte 20px, alto contraste, severidade com texto e ícone, não só cor |
| RNF09 | Testável sem internet | 21 testes automáticos com `pytest` |

## 6. Falhas previsíveis e caminho seguro

| Falha | Tipo | Caminho seguro |
|---|---|---|
| Site fora do ar, timeout, proxy | sistema | 3 tentativas com espera, depois snapshot local, aviso no relatório |
| URL errada (HTTP 4xx) | negócio | sem retry, snapshot local; sem snapshot → revisão humana |
| Página mudou de layout (texto curto) | negócio | revisão humana, a base antiga não é sobrescrita |
| Arquivo de eventos ausente | negócio | segue sem eventos, aviso no relatório |
| Linha de evento inválida | negócio | quarentena + revisão humana, resto do lote segue |
| Pedido vazio (falha de transcrição) | negócio | revisão humana |
| Modelo indeciso | negócio | revisão humana |
| Modelo salvo corrompido | sistema | retreina a partir do CSV de treino |
| Estado corrompido | sistema | backup do arquivo e estado limpo |
| LLM sem chave, fora do ar, vazio ou com resposta inválida | sistema | resumo por template |
| SMTP fora do ar | sistema | retry, depois `.eml` salvo para reenvio, notificação não marcada como enviada |

## 7. Critérios de aceite (ligados ao barema)

| Critério do barema | Peso | Evidência que vamos mostrar |
|---|---|---|
| Uso dos temas da disciplina | 30% | Quadro de temas no README, com 5 temas e a função de cada um no fluxo |
| Funcionamento ponta a ponta | 25% | `python main.py --offline` roda do início ao fim sem intervenção |
| Resiliência e segurança | 20% | `--demo-falhas` + log + aba Revisão humana + testes de retry/idempotência |
| Evidências de validação | 15% | `scripts/avaliar_classificador.py`: acurácia em 48 frases escritas à mão, matriz de confusão, erros e curva de limiar |
| Dados, ética, ODS | 10% | Seção de ética no README, mascaramento de dados, LLM só com dados agregados |

## 8. Pontos a confirmar com o grupo

O formato dos dados trocados com o grupo está em `contrato_integracao_ouviai.json` (JSON Schema).

- [ ] Os 5 temas do quadro batem com os nomes usados em aula? Ajustar o vocabulário no README se necessário.
- [ ] O Front-end vai expor `GET /events` em JSON? Se sim, configurar `EVENTOS_API_URL`.
- [ ] O RAG do GenAI vai ler `saida/base_conhecimento/*.jsonl`? Combinar o formato do trecho.
