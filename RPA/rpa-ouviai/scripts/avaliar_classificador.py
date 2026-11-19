"""Avaliação honesta do classificador de triagem.

Treina com o conjunto gerado por templates e mede no conjunto de teste escrito à
mão (vocabulário diferente). Também mede a regra de emergência e o efeito do
limiar de confiança que manda itens para revisão humana.

Uso: python scripts/avaliar_classificador.py
Saída: saida/avaliacao/metricas.md e metricas.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score  # noqa: E402

from robo.config import Config  # noqa: E402
from robo.etapas.triagem import criar_pipeline, detectar_emergencia, ler_rotulados  # noqa: E402

FRASES_EMERGENCIA = [
    ("caí da escada e não consigo levantar", True), ("socorro tem alguém forçando minha porta", True),
    ("estou com dor no peito forte", True), ("tá saindo cheiro de gás da cozinha", True),
    ("minha vizinha desmaiou aqui em casa", True), ("estou com falta de ar desde cedo", True),
    ("como faço pra pedir o bpc", False), ("o caixa do banco caiu e não consegui sacar", False),
    ("meu aparelho auditivo caiu no chão e quebrou", False), ("quero saber do passe livre", False),
]


def main() -> None:
    cfg = Config.carregar(offline=True)
    x_tr, y_tr = ler_rotulados(cfg.arquivo_treino)
    x_te, y_te = ler_rotulados(RAIZ / "dados" / "teste" / "pedidos_teste_rotulados.csv")

    modelo = criar_pipeline().fit(x_tr, y_tr)
    pred = modelo.predict(x_te)
    probs = modelo.predict_proba(x_te).max(axis=1)
    classes = list(modelo.classes_)

    limiar = cfg.regras["triagem"]["confianca_minima_modelo"]
    automaticos = [(p, y) for p, y, c in zip(pred, y_te, probs) if c >= limiar]
    acc_auto = sum(p == y for p, y in automaticos) / len(automaticos) if automaticos else 0.0

    emerg_ok = sum(bool(detectar_emergencia(t, cfg.regras["triagem"]["palavras_emergencia"])) == esperado
                   for t, esperado in FRASES_EMERGENCIA)
    falsos_emerg = [t for t, esp in FRASES_EMERGENCIA
                    if bool(detectar_emergencia(t, cfg.regras["triagem"]["palavras_emergencia"])) != esp]

    curva = []
    for lim in (0.0, 0.3, 0.45, 0.6, 0.75):
        dec = [(p, y) for p, y, c in zip(pred, y_te, probs) if c >= lim]
        curva.append({"limiar": lim, "cobertura": round(len(dec) / len(y_te), 3),
                      "acuracia": round(sum(p == y for p, y in dec) / len(dec), 3) if dec else None})

    erros = [{"texto": t, "esperado": y, "previsto": p, "confianca": round(float(c), 3)}
             for t, y, p, c in zip(x_te, y_te, pred, probs) if y != p]
    matriz = confusion_matrix(y_te, pred, labels=classes).tolist()

    metricas = {
        "treino": len(x_tr), "teste": len(x_te),
        "acuracia": round(accuracy_score(y_te, pred), 3),
        "f1_macro": round(f1_score(y_te, pred, average="macro"), 3),
        "limiar_revisao_humana": limiar,
        "enviados_para_revisao": int(sum(probs < limiar)),
        "acuracia_nos_decididos_automaticamente": round(acc_auto, 3),
        "regra_emergencia_acertos": f"{emerg_ok}/{len(FRASES_EMERGENCIA)}",
        "regra_emergencia_erros": falsos_emerg,
        "curva_limiar": curva, "classes": classes, "matriz_confusao": matriz, "erros": erros,
    }
    destino = RAIZ / "saida" / "avaliacao"
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "metricas.json").write_text(json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8")

    rel = classification_report(y_te, pred, zero_division=0)
    cab = "| real \\ previsto | " + " | ".join(c[:10] for c in classes) + " |"
    linhas_m = "\n".join(f"| {classes[i]} | " + " | ".join(str(v) for v in linha) + " |" for i, linha in enumerate(matriz))
    grupo = " · ".join(f"{m['nome']} (RM {m['rm']})" for m in cfg.grupo.get("integrantes", []))
    md = f"""# Avaliação do classificador de triagem

{cfg.grupo.get("projeto", "")} · {cfg.grupo.get("disciplina", "")}  
Grupo: {grupo}

- Treino: {len(x_tr)} frases sintéticas (templates) · Teste: {len(x_te)} frases escritas à mão, vocabulário diferente
- **Acurácia: {metricas['acuracia']:.1%}** · F1 macro: {metricas['f1_macro']:.3f}
- Limiar de revisão humana: {limiar:.0%} → {metricas['enviados_para_revisao']} de {len(x_te)} frases iriam para revisão
- Acurácia nas frases decididas automaticamente: {acc_auto:.1%}
- Regra de emergência: {metricas['regra_emergencia_acertos']} corretas {('(erros: ' + '; '.join(falsos_emerg) + ')') if falsos_emerg else ''}

## Limiar de confiança: cobertura automática × acurácia
| Limiar | Decidido pelo robô | Acurácia nesses casos |
|---|---|---|
""" + "\n".join(f"| {c['limiar']:.0%} | {c['cobertura']:.0%} | {c['acuracia']:.1%} |" for c in curva) + f"""

## Relatório por classe
```
{rel}
```

## Matriz de confusão
{cab}
|{'---|' * (len(classes) + 1)}
{linhas_m}

## Erros
""" + "\n".join(f"- \"{e['texto']}\" → previsto **{e['previsto']}** ({e['confianca']:.0%}), esperado {e['esperado']}" for e in erros)
    (destino / "metricas.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
