"""Ponto de entrada do Robô Cuidador OuviAí.

Uso:
    python main.py                 # tenta as fontes online, cai no snapshot se falhar
    python main.py --offline       # usa só os snapshots locais (sem internet)
    python main.py --demo-falhas   # injeta falhas previsíveis para demonstração
    python main.py --forcar-envio  # reenvia o relatório mesmo se já enviado no período
    python main.py --offline --data 2026-11-09T08:00   # reproduz a demonstração do relatório
"""
import argparse
import sys
from datetime import datetime

from robo.orquestrador import executar


def main() -> int:
    parser = argparse.ArgumentParser(description="Robô Cuidador OuviAí (RPA + IA)")
    parser.add_argument("--offline", action="store_true", default=None, help="não acessa a internet")
    parser.add_argument("--demo-falhas", action="store_true", default=None, help="injeta entradas inválidas")
    parser.add_argument("--forcar-envio", action="store_true", help="ignora a idempotência da notificação")
    parser.add_argument("--data", help="data de referência ISO (ex.: 2026-11-09T08:00) para reproduzir a demonstração")
    args = parser.parse_args()

    agora = datetime.fromisoformat(args.data) if args.data else None
    resultado = executar(offline=args.offline, demo_falhas=args.demo_falhas, forcar_envio=args.forcar_envio, agora=agora)
    print("\nResumo da execução")
    for etapa in resultado["etapas"]:
        print(f"  {etapa['status']:<15} {etapa['etapa']} ({etapa['duracao_s']}s)")
    print(f"  Itens para revisão humana: {len(resultado['revisao_humana'])}")
    print("  Saídas em: saida/  |  Log em: logs/robo.log")
    # código 0 mesmo com pendências: o robô cumpriu o caminho seguro; 1 só se tudo falhou
    return 1 if all(e["status"] == "falhou" for e in resultado["etapas"]) else 0


if __name__ == "__main__":
    sys.exit(main())
