# Governança em IA e Business Analytics

Esta pasta junta o que a disciplina de Governança pede sobre a GS: quais materiais foram integrados, quais não foram, e os controles que cada módulo aplica.

| Arquivo | O que é |
| --- | --- |
| [`quadro-integracao.md`](quadro-integracao.md) | Os 5 pilares de Model Governance por módulo e o que ficou de fora |
| [`model-card-triagem-rpa.md`](model-card-triagem-rpa.md) | Model Card do classificador de triagem do Robô Cuidador |
| [`model-card-ouviai.md`](model-card-ouviai.md) | Model Card do classificador de sons do OuviAí |
| [`termo-consentimento-gravacoes.md`](termo-consentimento-gravacoes.md) | Termo LGPD para quem gravou áudios ou testou os protótipos |
| [`../RPA/rpa-ouviai/contrato_integracao_ouviai.json`](../RPA/rpa-ouviai/contrato_integracao_ouviai.json) | Contrato de dados entre os módulos (JSON Schema) |

## Controles que já existem no código

| Controle | Onde está | Conceito da disciplina |
| --- | --- | --- |
| Mascaramento de CPF, e-mail, CEP, telefone e NIS antes de salvar ou enviar ao LLM | `RPA/rpa-ouviai/robo/privacidade.py` | LGPD, pseudonimização |
| Log de cada etapa do robô, com execução normal e com falhas | `RPA/rpa-ouviai/exemplos_saida/*.log` | Rastreabilidade, metadados operacionais |
| Pedido com confiança abaixo de 45% vai para revisão humana | `RPA/rpa-ouviai/exemplos_saida/metricas.md` | Human-in-the-loop |
| Evento sonoro com confiança abaixo de 0.60 não gera alerta | `RPA/rpa-ouviai/contrato_integracao_ouviai.json` | Limiar de decisão |
| Dados de treino e teste do robô são sintéticos | `RPA/rpa-ouviai/scripts/gerar_dados_sinteticos.py` | Privacidade por camada |
| Cidadão confirma ou corrige categoria e urgência antes de registrar | `citizentech/` | Human-in-the-loop |
| Chave de API em `.env`, com `.env.example` versionado | `citizentech/`, `RPA/rpa-ouviai/` | Segurança |
| Urgência com cor, ícone e texto | `citizentech/` | Acessibilidade (WCAG) |
| Áudio processado no celular, sem envio para a nuvem | `iot-ouviai/Physical Computing.pdf` | Privacy by Design |
| Aceite LGPD antes de liberar o microfone e áudio descartado após a transcrição | `pln-assistente-voz/` (relatório) | Consentimento destacado, minimização |
| Modelos de voz e LLM executados localmente | `pln-assistente-voz/` (relatório) | Dados sensíveis fora de terceiros |
| Lista de termos bloqueados antes de chamar o LLM e resposta padrão de abstenção | `genai-rag/GsGenIA.ipynb` | Riscos de GenAI, prompt injection |
| Chave da OpenAI pelo painel de Secrets do Colab | `genai-rag/GsGenIA.ipynb` | Segurança |
