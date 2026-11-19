# Robô Cuidador OuviAí · RPA + IA

> Global Solution 2026.2 · CitizenTech · FIAP Tecnólogo em IA · disciplina **AI for Robotic Process Automation**

**Integrantes**

| Nome completo | RM |
|---|---|
| Alexandre Ferreira | RM 565626 |
| Carlos Eduardo | RM 555812 |
| Filipe Melo | RM 564571 |

---

## O problema, em uma frase

A Dona Lúcia tem 72 anos, mora sozinha, não escuta a campainha e tem um celular simples, o OuviAí já ajuda ela a perceber os sons da casa e a tirar dúvidas por voz, mas **ninguém está olhando o conjunto**: quem insistiu na porta ontem, se o celular ficou dois dias desligado, se aquela ligação "do INSS" era golpe, se a página do gov.br sobre aparelho auditivo mudou.

Esse trabalho é repetitivo, periódico e cheio de regras, ou seja, é trabalho de robô. Então construímos um robô que roda toda semana, junta tudo, separa o que é urgente do que é rotina, manda para revisão humana o que ele não sabe decidir e entrega um resumo legível para a filha que cuida dela à distância.

Público: pessoas idosas com perda auditiva que moram sozinhas e seus cuidadores, gente com celular básico e pouco orçamento, onde a tecnologia precisa **economizar tempo e dinheiro**, não criar mais um gasto.

**ODS 10** (acessibilidade para pessoa com deficiência auditiva) · **ODS 3** (acesso a saúde auditiva pelo SUS) · **ODS 11** (comunidades inclusivas)

---

## Como o robô se encaixa no OuviAí

```
[Celular · Edge Impulse]     [Assistente de voz · RAG]          [ROBÔ CUIDADOR · este repositório]
 som → MFE → CNN → evento ─┐   pergunta → STT → LLM → TTS ─┐
                           ├──────────────────────────────┴──► 1. coleta fontes oficiais → base do RAG
                           │                                   2. eventos → regras de alerta
                           └─────────────────────────────────► 3. pedidos → triagem NLP
                                                               4. relatório Excel + HTML
                                                               5. e-mail para o cuidador
```

O robô **alimenta** o assistente (mantém a base de conhecimento atualizada em `saida/base_conhecimento/`) e **consome** o que o OuviAí produz (eventos sonoros e transcrições dos pedidos).

---

## Quadro de temas da disciplina

| # | Tema | Onde é usado no fluxo | O que resolve |
|---|---|---|---|
| 1 | **Web scraping e extração de documentos** (requests, BeautifulSoup, pypdf) | Etapa 1, `robo/etapas/coleta_fontes.py` | Busca páginas do gov.br, Planalto e INSS (HTML e PDF), limpa menu e rodapé, quebra em trechos com metadados e só reindexa o que mudou (hash SHA-256) |
| 2 | **Automação de planilhas e arquivos** (CSV, Pydantic, openpyxl) | Etapas 2 e 4, `eventos.py` e `relatorio.py` | Lê os eventos exportados do OuviAí, valida linha a linha, separa em quarentena o que está inválido e gera a planilha de 7 abas com filtros, cores e aba de revisão humana para preencher |
| 3 | **IA aplicada ao processo: NLP e regras inteligentes** (TF-IDF + Regressão Logística, regras de negócio) | Etapas 2 e 3, `triagem.py` e `eventos.py` | Classifica os pedidos em 6 temas e sugere o encaminhamento oficial; regras transformam eventos soltos em alertas (insistência na porta, porta de madrugada, celular parado); emergência por regra tem prioridade sobre o modelo |
| 4 | **Automação de e-mail e notificações** (smtplib, EmailMessage) | Etapa 5, `notificacao.py` | Envia ao cuidador o resumo em HTML com a planilha anexa, no máximo uma vez por semana |
| 5 | **Tratamento de exceções, logs e orquestração** (padrão REFramework) | Todo o robô, `resiliencia.py` e `orquestrador.py` | Separa erro de negócio de erro de sistema, faz retry com espera crescente, registra tudo em log, isola cada etapa para uma falha não derrubar as outras e gera relatório de execução |

O LLM é **opcional** (resumo em linguagem simples para o cuidador) e tem caminho seguro: sem chave, fora do ar ou com resposta inválida, o robô usa um resumo por template.

---

## Como executar

Precisa de Python 3.10 ou mais novo, e só.

```bash
git clone <url-do-repositorio>
cd rpa-ouviai
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python main.py --offline --data 2026-11-08T23:30      # demonstração reproduzível
```

Pronto, as saídas aparecem em `saida/` e o log em `logs/robo.log`. Vamos ver o que cada comando faz:

| Comando | Para quê |
|---|---|
| `python main.py` | Execução real: tenta as fontes online e cai no snapshot se o site falhar |
| `python main.py --offline` | Sem internet, usa só os snapshots locais |
| `python main.py --offline --data 2026-11-08T23:30` | Fixa a data de referência na semana dos dados sintéticos (é o que usamos no vídeo) |
| `python main.py --demo-falhas --offline --forcar-envio` | Injeta falhas previsíveis para demonstrar o caminho seguro |
| `python scripts/avaliar_classificador.py` | Mede o classificador de triagem e gera `saida/avaliacao/metricas.md` |
| `python scripts/gerar_dados_sinteticos.py` | Regera eventos e frases de treino (semente fixa, sempre o mesmo resultado) |
| `python -m pytest -q` | 21 testes automáticos, sem internet e sem SMTP |

Para agendar toda segunda às 7h, no Linux/Mac: `0 7 * * 1 cd /caminho/rpa-ouviai && .venv/bin/python main.py`, no Windows use o Agendador de Tarefas apontando para o mesmo comando.

### Configurando as chaves

Nenhuma chave é obrigatória. Copiamos o modelo e preenchemos só o que formos usar:

```bash
cp .env.example .env
```

| Variável | Sem ela, o robô... |
|---|---|
| `EVENTOS_API_URL` | lê `dados/entrada/eventos_*.csv` |
| `LLM_API_URL`, `LLM_API_KEY`, `LLM_MODELO` | escreve o resumo por template |
| `SMTP_HOST`, `SMTP_USUARIO`, `SMTP_SENHA` | salva o e-mail em `saida/caixa_de_saida/*.eml` (abre em qualquer cliente de e-mail) |

O `.env` está no `.gitignore` e nunca vai para o repositório. O LLM funciona com qualquer API compatível com OpenAI, por exemplo a camada gratuita do Groq ou um Ollama rodando local.

---

## Evidências de validação

### 1. Classificador de triagem (amostra rotulada)

Treinamos com 360 frases geradas por templates e medimos em **48 frases escritas à mão**, com vocabulário diferente, justamente para não medir o modelo com o próprio treino. Resultado completo em `saida/avaliacao/metricas.md`.

| Métrica | Valor |
|---|---|
| Acurácia geral (48 frases, 6 temas) | **89,6%** |
| F1 macro | 0,895 |
| Regra de emergência (10 frases, 6 de risco e 4 armadilhas como "o caixa do banco caiu") | 10/10 |

O limiar de confiança decide quanto o robô resolve sozinho e quanto vai para uma pessoa, e escolhemos 45% olhando essa troca:

| Limiar | Robô decide sozinho | Acurácia nesses casos |
|---|---|---|
| 0% | 100% | 89,6% |
| 30% | 94% | 91,1% |
| **45% (escolhido)** | **67%** | **96,9%** |
| 60% | 50% | 95,8% |

Com 45%, o robô acerta quase 97% do que decide e manda um terço para revisão humana, que é um preço aceitável quando o assunto é golpe ou benefício de uma pessoa idosa.

**Onde ele erra, e por quê:** os 5 erros são frases que até uma pessoa hesitaria. "O CRAS falou que eu preciso atualizar o cadastro senão perco o dinheiro do LOAS" virou golpe (o template de golpe tem muito "atualizar cadastro"), "uma mulher disse que é do posto e vai vir buscar meu aparelho auditivo" virou saúde auditiva quando era golpe, e "minha nora fica com meu cartão" virou transporte com só 24% de confiança, ou seja, foi para revisão humana como deveria. A lição para a próxima versão é treinar com frases reais anonimizadas e não só templates.

### 2. Execução ponta a ponta (semana sintética de 2 a 8/nov/2026)

| Entrada | Resultado |
|---|---|
| 109 eventos no CSV | 108 válidos (1 duplicado descartado), 2 de baixa confiança ignorados, **3 alertas**: insistência na porta (4 sons em 2 min), batida às 02h47, celular 32 h sem enviar dados |
| 16 pedidos da semana | 1 emergência por regra ("caí no banheiro... socorro"), 2 dados pessoais mascarados (CPF e telefone), 1 para revisão humana ("aquilo"), 4 golpes sinalizados |
| 3 fontes oficiais | 3 atualizadas na primeira execução, 0 na segunda (sem mudança, nada a reindexar) |
| Notificação | 1 e-mail na primeira execução, 0 na segunda (idempotência) |

Conferindo à mão os 15 pedidos que o modelo classificou, ele errou 1 ("minha filha pegou meu cartão do benefício e não devolve" foi para BPC, deveria ser violência patrimonial em direitos da pessoa idosa) e 1 é ambíguo ("tenho direito a algum desconto").

### 3. Casos de falha demonstrados

`python main.py --demo-falhas --offline --forcar-envio` cria entradas problemáticas e o robô termina com status `concluido_com_pendencias`, sem travar:

| Falha injetada | O que o robô fez |
|---|---|
| Fonte com URL inexistente e sem snapshot | Registrou erro, mandou para revisão humana, seguiu com as outras fontes |
| Evento com confiança 1,7 | Quarentena |
| Evento com data "ontem de tarde" | Quarentena |
| Evento com classe "alarme_incendio" (que o modelo de áudio não conhece) | Quarentena |
| Evento sem dispositivo | Quarentena |
| Pedido com transcrição vazia | Revisão humana |
| Pedido com CPF e telefone | Mascarados antes de qualquer gravação |

E sem `--offline`, com o site do governo fora do ar, o log mostra as 3 tentativas com espera de 1s e 2s e depois a troca para o snapshot, que é o caminho seguro. Os testes automáticos cobrem também SMTP e LLM fora do ar, estado corrompido e modelo corrompido.

---

## Proteção de dados, ética e ODS

Voz e mensagens de uma pessoa idosa são dados pessoais, e alguns pedidos falam de saúde e dinheiro, então tratamos tudo com cuidado de documento sigiloso. **Todo texto livre passa pelo mascaramento antes de ir para planilha, e-mail ou API**, CPF, telefone, e-mail, CEP e NIS viram marcadores. O LLM opcional **só recebe números agregados** (quantos eventos, quantos pedidos por tema), nunca a frase do cidadão, e a resposta dele é validada antes de ser usada. Todos os dados do repositório são sintéticos, a Dona Lúcia não existe, e as fontes são páginas públicas do governo.

Nos limites, o robô **não decide sozinho o que é sensível**: emergência por regra sempre aparece no topo do relatório com os números 192, 193 e 190, mas o robô roda uma vez por semana e **não substitui serviço de emergência**, isso está escrito no próprio relatório. O que o modelo não tem confiança para decidir vai para revisão humana, e cada sugestão de encaminhamento aponta para um canal oficial e gratuito (CRAS, Meu INSS, 135, UBS, Disque 100), para não empurrar ninguém para intermediário pago. Um viés que conhecemos: o classificador foi treinado com o jeito de falar que o grupo imaginou, e pode errar mais com regionalismos e com transcrições ruins de sotaques que o STT entende pior.

A conexão com os ODS é direta, o robô aumenta a autonomia de uma pessoa com deficiência auditiva (ODS 10), facilita o acesso ao aparelho auditivo e a benefícios (ODS 3 e 10) e reduz o custo de cuidar à distância usando só o celular que a pessoa já tem (ODS 11).

---

## Estrutura do projeto

```
rpa-ouviai/
├── main.py                       ponto de entrada
├── config/
│   ├── grupo.json                integrantes e RMs, impressos na planilha, no HTML e no relatório de execução
│   ├── fontes.json               fontes oficiais monitoradas (URL, seletor, snapshot)
│   └── regras.json               limiares e palavras de emergência, ajustáveis sem código
├── robo/
│   ├── orquestrador.py           Init → etapas → End (estilo REFramework)
│   ├── resiliencia.py            ErroDeNegocio, ErroDeSistema, retry, Etapa
│   ├── privacidade.py            mascaramento de dados pessoais
│   ├── estado.py                 idempotência entre execuções
│   ├── llm.py                    resumo opcional com LLM + template
│   └── etapas/                   coleta_fontes, eventos, triagem, relatorio, notificacao
├── dados/
│   ├── snapshots/                cópias locais das fontes (caminho seguro)
│   ├── entrada/                  eventos e pedidos da semana (sintéticos)
│   ├── treino/                   frases de treino (geradas)
│   └── teste/                    frases de teste (escritas à mão)
├── scripts/                      gerar_dados_sinteticos.py, avaliar_classificador.py
├── tests/                        21 testes com pytest
├── exemplos_saida/               saídas de uma execução, para quem não quiser rodar
├── REQUISITOS.md                 requisitos funcionais, não funcionais e critérios de aceite
├── contrato_integracao_ouviai.json  formato dos dados trocados com IoT, Front-end, PLN e RAG
└── .env.example
```

## Limitações e próximos passos

- O robô é **periódico**: emergência aparece no relatório, não vira alerta em tempo real. A evolução natural é um gatilho imediato (push ou SMS) quando a etapa 3 encontrar emergência.
- As frases de treino são de template, o próximo passo é coletar pedidos reais anonimizados do assistente de voz e retreinar.
- Os snapshots são resumos feitos pelo grupo, na execução online o robô usa a página oficial de verdade.
- Seletores HTML quebram quando o gov.br muda de layout, por isso a regra de "texto curto demais vai para revisão humana".
