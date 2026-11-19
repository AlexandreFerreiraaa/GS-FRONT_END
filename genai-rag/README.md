# Generative AI & Advanced Nets · Assistente RAG

Assistente de serviços públicos com base simulada de Cartas de Serviços do gov.br.

- Notebook: [`GsGenIA.ipynb`](GsGenIA.ipynb) (Google Colab, chave da OpenAI pelo painel de Secrets)
- Documentação: [`Documentacao_Global_Solution_GenAI.pdf`](Documentacao_Global_Solution_GenAI.pdf)
- Vídeo: https://youtu.be/Vuh5_UaCfeo

## Configuração

| Componente | Escolha |
| --- | --- |
| Chunking | RecursiveCharacterTextSplitter, 500 com sobreposição de 50 |
| Retriever | FAISS, embeddings paraphrase-multilingual-MiniLM-L12-v2, top-k 2 |
| Generator | gpt-4o-mini, temperatura 0, resposta padrão de abstenção |
| Guardrail | Lista de termos bloqueados antes de chamar o LLM |

10 perguntas de teste: 3 respondíveis, 1 ambígua, 3 fora da base, 3 adversariais (prompt injection, troca de papel e pedido de dados de acesso).

Integração: a base é própria (3 trechos no notebook) e não usa os trechos produzidos pelo Robô Cuidador.
