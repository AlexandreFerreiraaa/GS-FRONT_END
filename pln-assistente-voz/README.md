# PLN · Assistente de voz para serviços públicos

Assistente por voz em PT-BR para orientar sobre SUS e CadÚnico/CRAS. Persona: Maria Helena, 68 anos, que se comunica só por áudio.

- Relatório: [`RELATÓRIO TÉCNICO PLN1.pdf`](RELAT%C3%93RIO%20T%C3%89CNICO%20PLN1.pdf)
- Entrega (código e material de teste): ver [`link_entrega_pln.txt`](link_entrega_pln.txt)
- Vídeo: https://youtu.be/u5V6h_HPIoY

## Arquitetura

Termo LGPD → microfone → STT (faster-whisper small) → RAG (FAISS) e memória → LLM (Qwen2.5-7B-Instruct quantizado, local) → adaptação para fala → TTS (Piper pt_BR), com latência registrada por etapa.

## Controles de privacidade descritos no relatório

- Aceite explícito antes de liberar o microfone
- Áudio mantido só em memória e descartado depois da transcrição
- Modelos executados localmente, sem enviar voz para APIs de terceiros
- Recusa fora do escopo e encaminhamento para 192 ou 136 em urgência

Integração: o assistente tem base de conhecimento própria e não troca dados com o Robô Cuidador.
