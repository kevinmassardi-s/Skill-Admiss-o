"""
Script de entrada. Encadeia leitura -> casamento -> conferência e imprime um resumo legível:
o que está pronto para lançar, o que está pendente (com o motivo) e o que ficou ambíguo
(aguardando escolha humana). Nunca mistura os três grupos.

Uso:
    python executar_conferencia.py --caminho "C:\\...\\FORMULÁRIO DE ADMISSÃO - EXTERNO.xlsx"

--incluir-todos-status : por padrão, só processa admissões cujo status (coluna "DOC PENDENTE" na aba
    EMPRESA) não é SIM/CANCELOU/DESISTIU/DUPLICADO/EM AUDITORIA (ver references/regras-conferencia.md).
    Passe essa flag para processar tudo, inclusive o que já foi marcado concluído.

--data-corte (padrão: 2026-08-11, decisão do Kevin nesta data) : só processa admissões da aba EMPRESA
    cujo "Carimbo de data/hora" é dessa data em diante. O backlog antigo (registros sem status de
    conclusão, mas de antes do corte) fica de fora — é tratado à parte, não por esta rotina.

--modo aberto|auditoria (padrão: aberto) : pedido do Kevin (2026-08-12) — mesma esteira (leitura,
    casamento, conferência, jornada), só troca qual fatia da planilha entra:
      aberto     -> o de sempre: status ativo (não concluído/cancelado/etc.) e dentro do corte de data.
      auditoria  -> só as linhas com status exatamente "EM AUDITORIA", em QUALQUER data (esse recorte
                    não tem corte de data — é uma fila separada, não "o que é novo"). Ignora
                    --incluir-todos-status e --data-corte quando ativo.

Reescrita em Python (2026-08-11) no lugar da versão PowerShell original — mesma lógica de negócio,
~14x mais rápido no mesmo arquivo real (~60s -> ~4-8s).
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, date
from itertools import groupby

from ler_planilha import ler_planilha_admissao
from casar_admissoes import casar_admissoes
from conferir_admissao import confirmar_admissao

COL_STATUS_EMPRESA = "DOC PENDENTE"
COL_CARIMBO_EMPRESA = "Carimbo de data/hora"
STATUS_QUE_NAO_GERAM_TRABALHO = {"SIM", "CANCELOU", "DESISTIU", "DUPLICADO", "EM AUDITORIA"}


def status_ativo(status) -> bool:
    if status is None or str(status).strip() == "":
        return True
    return str(status).strip().upper() not in STATUS_QUE_NAO_GERAM_TRABALHO


def carimbo_como_data(valor) -> date | None:
    """openpyxl já devolve Carimbo de data/hora como datetime (não como serial do Excel cru)."""
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--caminho", required=True)
    parser.add_argument("--incluir-todos-status", action="store_true")
    parser.add_argument("--data-corte", default="2026-08-11")
    parser.add_argument("--modo", choices=["aberto", "auditoria"], default="aberto")
    args = parser.parse_args()

    data_corte = datetime.strptime(args.data_corte, "%Y-%m-%d").date()

    print(f"Lendo {args.caminho} ... (modo: {args.modo})")
    # Modo auditoria não tem corte de data — um item em auditoria pode ser bem mais antigo que as
    # últimas 600 linhas (a otimização de performance normal). Lê a aba inteira nesse modo.
    somente_ultimas_n_linhas = 0 if args.modo == "auditoria" else 600
    dados = ler_planilha_admissao(args.caminho, somente_ultimas_n_linhas=somente_ultimas_n_linhas)
    print(f"  EMPRESA: {len(dados['empresa'])} linhas | FUNCIONARIO: {len(dados['funcionario'])} linhas")

    empresa_para_processar = dados["empresa"]
    funcionario_para_processar = dados["funcionario"]

    if args.modo == "auditoria":
        antes = len(empresa_para_processar)
        empresa_para_processar = [
            e for e in empresa_para_processar
            if str(e.get(COL_STATUS_EMPRESA) or "").strip().upper() == "EM AUDITORIA"
        ]
        print(f"  MODO AUDITORIA: {len(empresa_para_processar)} de {antes} linha(s) da EMPRESA "
              f"marcadas 'EM AUDITORIA' (sem corte de data — mostra qualquer competência).")
    elif not args.incluir_todos_status:
        # Só a EMPRESA é filtrada por status: é a aba que Kevin usa como referência de "feito ou não".
        # A FUNCIONARIO é casada por inteiro (sem filtro de status próprio) — ver
        # references/estrutura-planilha.md sobre por que não confiamos no FEITO? da aba FUNCIONARIO.
        antes = len(empresa_para_processar)
        empresa_para_processar = [e for e in empresa_para_processar if status_ativo(e.get(COL_STATUS_EMPRESA))]
        print(f"  EMPRESA: {antes - len(empresa_para_processar)} linha(s) já concluída/cancelada/"
              f"duplicada/desistida — não processadas.")

        # Corte por data (decisão do Kevin, 2026-08-11): backlog antigo sem status de conclusão fica
        # fora do dia a dia.
        antes_data = len(empresa_para_processar)
        empresa_ativa_recente = []
        empresa_backlog_antigo = []
        for e in empresa_para_processar:
            d = carimbo_como_data(e.get(COL_CARIMBO_EMPRESA))
            if d is not None and d < data_corte:
                empresa_backlog_antigo.append(e)
            else:
                empresa_ativa_recente.append(e)
        empresa_para_processar = empresa_ativa_recente
        print(f"  EMPRESA: {len(empresa_backlog_antigo)} linha(s) anteriores a {args.data_corte}, "
              f"ainda sem status de conclusão — backlog antigo, fora do escopo desta rotina.")
        print("  (use --incluir-todos-status e/ou --data-corte pra revisar o backlog antigo se precisar algum dia)")

    casamento = casar_admissoes(empresa_para_processar, funcionario_para_processar)

    resultados = [confirmar_admissao(par) for par in casamento["casados"]]

    # CPF duplicado entre pessoas diferentes do lote — achado real de 2026-08-11 (Auany Vieira Pereira
    # e Wandrey Juneo Oliveira Cardoso tinham o mesmo CPF reconstruído; um dos dois estava errado).
    com_cpf = sorted([r for r in resultados if r["cpf_valido"]], key=lambda r: r["cpf_valido"])
    for cpf, grupo_iter in groupby(com_cpf, key=lambda r: r["cpf_valido"]):
        grupo = list(grupo_iter)
        if len(grupo) > 1:
            for r in grupo:
                outros = ", ".join(g["nome_colaborador"] for g in grupo if g is not r)
                r["pendencias"].append(
                    f"CPF ({cpf}) repetido em outra admissão deste lote ({outros}) — CPF não pode "
                    f"ser o mesmo pra pessoas diferentes; confirmar com o documento antes de lançar "
                    f"qualquer uma das duas"
                )

    prontas = [r for r in resultados if not r["pendencias"]]
    com_pendencia = [r for r in resultados if r["pendencias"]]

    print()
    print("========================================")
    print(f"PRONTAS PARA LANÇAR NO DOMÍNIO: {len(prontas)}")
    print("========================================")
    for r in prontas:
        print()
        print(r["resumo"])

    print()
    print("========================================")
    print(f"COM PENDÊNCIA: {len(com_pendencia)}")
    print("========================================")
    for r in com_pendencia:
        print()
        print(f"PENDÊNCIAS DE {r['nome_colaborador']} — {r['nome_empresa']}:")
        for p in r["pendencias"]:
            print(f"  - {p}")
        print()
        print(r["resumo"])

    print()
    print("========================================")
    print(f"AMBÍGUAS (mais de um candidato — escolha manual): {len(casamento['ambiguos'])}")
    print("========================================")
    for amb in casamento["ambiguos"]:
        print()
        e = amb["empresa"]
        print(f"Empresa: {e.get('EMPRESA: (RAZÃO SOCIAL)')} / Funcionário: {e.get('NOME COMPLETO DO FUNCIONÁRIO:')}")
        linhas_candidatos = ", ".join(str(c["_linha"]) for c in amb["candidatos"])
        print(f"  Candidatos na aba FUNCIONARIO (linha): {linhas_candidatos}")

    print()
    print("========================================")
    print(f"PROVÁVEIS (achado só com nome mais solto — confirmar antes de aceitar): {len(casamento['provaveis'])}")
    print("========================================")
    for prov in casamento["provaveis"]:
        print()
        e = prov["empresa"]
        print(f"Empresa (linha {e['_linha']}): {e.get('EMPRESA: (RAZÃO SOCIAL)')!r} / Funcionário: {e.get('NOME COMPLETO DO FUNCIONÁRIO:')!r}")
        for c in prov["candidatos"]:
            print(f"  Candidato (linha {c['_linha']}): empresa={c.get('NOME DA EMPRESA: (RAZAO SOCIAL)')!r} / nome={c.get('NOME COMPLETO:')!r}")
        if len(prov["candidatos"]) == 1:
            r = confirmar_admissao({"empresa": e, "funcionario": prov["candidatos"][0]})
            print()
            print("  ATENÇÃO: casamento ainda NÃO confirmado — confira se é a mesma empresa/pessoa antes de usar isto.")
            print()
            print(r["resumo"])
            if r["pendencias"]:
                print()
                print("  Pendências (se o casamento for confirmado):")
                for p in r["pendencias"]:
                    print(f"    - {p}")

    print()
    print("========================================")
    print(f"SEM PAR NA ABA FUNCIONARIO: {len(casamento['sem_par_funcionario'])}")
    print("========================================")
    for e in casamento["sem_par_funcionario"]:
        print(f"  Linha {e['_linha']}: {e.get('NOME COMPLETO DO FUNCIONÁRIO:')} / {e.get('EMPRESA: (RAZÃO SOCIAL)')}")

    print()
    print("========================================")
    print(f"SEM PAR NA ABA EMPRESA: {len(casamento['sem_par_empresa'])}")
    print("(inclui respostas antigas de FUNCIONARIO cuja EMPRESA já foi concluída — número alto aqui")
    print(" é esperado e não é necessariamente uma pendência de hoje)")
    print("========================================")
    for f in casamento["sem_par_empresa"]:
        print(f"  Linha {f['_linha']}: {f.get('NOME COMPLETO:')} / {f.get('NOME DA EMPRESA: (RAZAO SOCIAL)')}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
