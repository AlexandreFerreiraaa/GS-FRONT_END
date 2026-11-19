"""Gera os dados sintéticos do projeto (nenhum dado pessoal real).

- dados/entrada/eventos_semana.csv  → eventos sonoros de uma semana da "Dona Lúcia" (persona fictícia)
- dados/treino/pedidos_rotulados.csv → frases de treino do classificador, montadas por templates

O conjunto de TESTE (dados/teste/pedidos_teste_rotulados.csv) NÃO é gerado aqui:
foi escrito à mão, com outro vocabulário, para medir o modelo de forma honesta.

Uso: python scripts/gerar_dados_sinteticos.py
"""
from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
random.seed(42)


# ---------------------------------------------------------------- eventos
def gerar_eventos() -> list[dict]:
    disp = "celular-dona-lucia"
    eventos = []
    inicio = datetime(2026, 11, 2, 7, 0)
    for dia in range(7):
        base = inicio + timedelta(days=dia)
        if dia == 3:  # quinta: celular descarregou das 9h de quinta às 15h de sexta (30 h sem dados)
            for h in range(0, 2):
                eventos.append((base + timedelta(hours=h, minutes=random.randint(0, 50)), "ambiente", 0.9))
            continue
        horas = range(0, 16) if dia != 4 else range(8, 16)
        for h in horas:  # "batimento": classe ambiente ao longo do dia
            eventos.append((base + timedelta(hours=h, minutes=random.randint(0, 55)), "ambiente",
                            round(random.uniform(0.75, 0.99), 2)))
        for _ in range(random.randint(1, 3)):  # visitas normais
            t = base + timedelta(hours=random.randint(2, 11), minutes=random.randint(0, 59))
            eventos.append((t, random.choice(["campainha", "batida_porta"]), round(random.uniform(0.7, 0.97), 2)))

    # segunda: entregador insistiu (4 sons em 2 minutos)
    t = datetime(2026, 11, 2, 14, 10)
    for k, cls in enumerate(["campainha", "campainha", "batida_porta", "batida_porta"]):
        eventos.append((t + timedelta(seconds=35 * k), cls, round(random.uniform(0.8, 0.95), 2)))
    # quarta: batida de madrugada
    eventos.append((datetime(2026, 11, 4, 2, 47), "batida_porta", 0.86))
    # detecções de baixa confiança (TV alta, panela) que não devem virar alerta
    eventos.append((datetime(2026, 11, 7, 20, 15), "campainha", 0.41))
    eventos.append((datetime(2026, 11, 6, 18, 3), "batida_porta", 0.38))
    # duplicata exportada duas vezes (testa idempotência)
    eventos.append((datetime(2026, 11, 2, 14, 10), "campainha", 0.9))

    eventos.sort()
    return [{"momento": t.isoformat(timespec="seconds"), "classe": c, "confianca": p, "dispositivo": disp}
            for t, c, p in eventos]


# ---------------------------------------------------------------- treino da triagem
TEMPLATES = {
    "beneficio_bpc": {
        "frases": ["como faço pra pedir o {b}", "tenho {idade} anos e não tenho renda, tenho direito ao {b}",
                   "quanto paga o {b} esse ano", "meu {b} foi negado o que eu faço", "preciso estar no cadastro único pro {b}?",
                   "onde eu peço o {b}", "o {b} é aposentadoria?", "minha renda conta para o {b}",
                   "o {b} do meu marido foi cortado", "quero saber se posso receber o {b} morando com meu filho",
                   "como atualizo o cadúnico pra não perder o {b}", "liguei no 135 e não consegui pedir o {b}"],
        "b": ["bpc", "benefício de prestação continuada", "loas", "benefício do idoso", "bpc loas", "salário do idoso"],
    },
    "saude_auditiva": {
        "frases": ["como consigo um {a} pelo sus", "meu {a} quebrou onde eu conserto", "não estou escutando direito, o que faço",
                   "a pilha do {a} acabou, o posto dá?", "quanto tempo demora pra receber o {a} do sus",
                   "preciso de encaminhamento pro {a}?", "o médico disse que eu preciso de {a}, e agora",
                   "onde tem exame de audição de graça", "o {a} está apitando muito", "meu ouvido zumbe e escuto pouco",
                   "posto de saúde faz exame de audiometria?", "quero trocar meu {a} antigo"],
        "a": ["aparelho auditivo", "aparelho de surdez", "aparelho do ouvido", "aasi", "aparelho pra escutar"],
    },
    "direitos_idoso": {
        "frases": ["o banco não quis me dar {p}", "tenho direito a {p} no {l}?", "meu filho pega meu dinheiro sem deixar, o que eu faço",
                   "estou sendo maltratada pela minha família", "o {l} me deixou esperando horas mesmo eu tendo {p}",
                   "quais são os direitos do idoso", "onde denuncio abandono de idoso", "o estatuto do idoso garante {p}?",
                   "meu vizinho idoso está sozinho e sem comida", "plano de saúde aumentou porque fiz 60 anos, pode?",
                   "o que diz o estatuto da pessoa idosa", "a farmácia não respeitou a fila de idoso"],
        "p": ["atendimento prioritário", "fila preferencial", "prioridade", "preferência no atendimento"],
        "l": ["banco", "posto", "mercado", "cartório", "hospital", "correio"],
    },
    "transporte_gratuidade": {
        "frases": ["idoso paga {t}?", "com quantos anos eu tenho {g} no {t}", "o motorista do {t} não quis me deixar passar de graça",
                   "como tiro a carteirinha de idoso pro {t}", "como faço pra viajar de {t} interestadual de graça",
                   "preciso de cartão pra andar de {t} sem pagar", "tenho 66 anos, posso andar de {t} de graça",
                   "a passagem de {t} é grátis pra quem tem 65?", "onde faço o bilhete do idoso", "o {t} não parou pra mim no ponto",
                   "assento reservado no {t} é obrigatório?", "desconto na passagem de {t} pra idoso"],
        "t": ["ônibus", "metrô", "trem", "ônibus intermunicipal", "busão", "lotação"],
        "g": ["gratuidade", "passe livre", "passagem grátis"],
    },
    "golpe_suspeito": {
        "frases": ["me ligaram do {o} pedindo {d}", "recebi mensagem dizendo que meu benefício vai ser bloqueado se eu não mandar {d}",
                   "um moço falou que é do {o} e quer vir aqui em casa", "pediram pix pra liberar meu {o}",
                   "chegou um link no whatsapp pra atualizar meu cadastro do {o}", "disseram que eu ganhei um prêmio e pediram {d}",
                   "ligaram falando que sou eu que tenho dívida no {o}", "é verdade que o {o} manda sms pedindo {d}?",
                   "meu neto mandou mensagem de número novo pedindo dinheiro", "falaram que meu aparelho auditivo é de graça mas tenho que pagar o frete",
                   "um senhor bateu aqui dizendo que é do {o} e quer meus documentos", "querem que eu passe o código que chegou no celular"],
        "o": ["inss", "banco", "governo", "sus", "gov.br"],
        "d": ["minha senha", "o código do celular", "meus dados", "o número do cartão", "um pix"],
    },
    "fora_escopo": {
        "frases": ["qual o resultado do jogo de ontem", "me conta uma piada", "que horas são", "vai chover amanhã?",
                   "receita de bolo de fubá", "quem ganhou a novela", "qual o melhor celular pra comprar",
                   "toca uma música", "me ajuda a fazer palavras cruzadas", "qual a capital da frança",
                   "quanto está o dólar", "como planto tomate no vaso", "me recomenda um filme", "o que é inteligência artificial"],
    },
}


def expandir(categoria: str, cfg: dict, alvo: int) -> list[str]:
    frases = set()
    slots = {k: v for k, v in cfg.items() if k != "frases"}
    tentativas = 0
    while len(frases) < alvo and tentativas < alvo * 30:
        tentativas += 1
        f = random.choice(cfg["frases"])
        valores = {k: random.choice(v) for k, v in slots.items()}
        valores["idade"] = random.randint(62, 90)
        texto = f.format(**valores)
        if random.random() < 0.3:
            texto = random.choice(["oi ", "bom dia, ", "por favor ", "olá, ", "minha filha, "]) + texto
        if random.random() < 0.15:  # ruído típico de transcrição
            texto = texto.replace("ç", "c").replace("ã", "a")
        frases.add(texto)
    return sorted(frases)


def main() -> None:
    entrada = RAIZ / "dados" / "entrada"
    with (entrada / "eventos_semana.csv").open("w", encoding="utf-8", newline="") as arq:
        w = csv.DictWriter(arq, fieldnames=["momento", "classe", "confianca", "dispositivo"])
        w.writeheader()
        w.writerows(gerar_eventos())

    linhas = []
    for cat, cfg in TEMPLATES.items():
        for texto in expandir(cat, cfg, 60):
            linhas.append({"texto": texto, "categoria": cat})
    random.shuffle(linhas)
    destino = RAIZ / "dados" / "treino" / "pedidos_rotulados.csv"
    with destino.open("w", encoding="utf-8", newline="") as arq:
        w = csv.DictWriter(arq, fieldnames=["texto", "categoria"])
        w.writeheader()
        w.writerows(linhas)
    print(f"eventos_semana.csv e {len(linhas)} frases de treino geradas")


if __name__ == "__main__":
    main()
