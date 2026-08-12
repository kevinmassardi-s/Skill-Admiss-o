"""
Casa cada linha da aba EMPRESA com a linha correspondente da aba FUNCIONARIO, pela única chave
disponível hoje: nome da empresa + nome do colaborador, normalizados. Ver
references/casamento-empresa-funcionario.md para a lógica completa e o porquê de cada decisão.

Nunca decide sozinho um caso ambíguo (mais de um candidato) — devolve os candidatos para uma pessoa
escolher. O mesmo vale para os "prováveis" (achados só na segunda tentativa, mais solta): são uma
sugestão, não uma decisão.

Reescrita em Python (2026-08-11) — mesma lógica da versão PowerShell original.

Achado real (2026-08-12): a mesma empresa apareceu grafada de pelo menos 6 jeitos diferentes no
histórico ("R G TAVARES DROGARIA LTDA", "RG TAVARES DROGARIA EIRELI", "DROGARIA J G TAVARES LTDA",
"DROGARIA JG TAVARES LTDA"...). Uma admissão real (Alexsandro Neves Mota do Monte) ficou "sem par" só
porque a EMPRESA usou "JG" (sem espaço) e o FUNCIONARIO usou "J G" (com espaço) — a normalização
antiga (só maiúscula + espaço duplicado) não pegava isso. Adicionada uma segunda tentativa, mais solta
(remove todo espaço do nome da empresa), mas só como sugestão — nunca casamento automático.
"""

from __future__ import annotations

import re

CAMPO_NOME_FUNCIONARIO_NA_EMPRESA = "NOME COMPLETO DO FUNCIONÁRIO:"
CAMPO_NOME_EMPRESA_NA_EMPRESA = "EMPRESA: (RAZÃO SOCIAL)"
CAMPO_NOME_FUNCIONARIO_NO_FUNCIONARIO = "NOME COMPLETO:"
CAMPO_NOME_EMPRESA_NO_FUNCIONARIO = "NOME DA EMPRESA: (RAZAO SOCIAL)"


def normalizar_nome(texto) -> str:
    if not texto:
        return ""
    t = str(texto).strip()
    t = re.sub(r"\s+", " ", t)
    return t.upper()


def normalizar_nome_frouxo(texto) -> str:
    """Segunda tentativa: remove TODO espaço, não só duplicado — pega "JG" vs "J G"."""
    return re.sub(r"\s+", "", normalizar_nome(texto))


def casar_admissoes(empresa: list[dict], funcionario: list[dict]) -> dict:
    for f in funcionario:
        f["_chave_funcionario"] = normalizar_nome(f.get(CAMPO_NOME_FUNCIONARIO_NO_FUNCIONARIO))
        f["_chave_empresa"] = normalizar_nome(f.get(CAMPO_NOME_EMPRESA_NO_FUNCIONARIO))
        f["_chave_funcionario_frouxa"] = normalizar_nome_frouxo(f.get(CAMPO_NOME_FUNCIONARIO_NO_FUNCIONARIO))
        f["_chave_empresa_frouxa"] = normalizar_nome_frouxo(f.get(CAMPO_NOME_EMPRESA_NO_FUNCIONARIO))
        f["_usado"] = False

    casados = []
    sem_par_funcionario = []
    ambiguos = []
    provaveis = []

    for e in empresa:
        chave_funcionario = normalizar_nome(e.get(CAMPO_NOME_FUNCIONARIO_NA_EMPRESA))
        chave_empresa = normalizar_nome(e.get(CAMPO_NOME_EMPRESA_NA_EMPRESA))

        candidatos = [
            f for f in funcionario
            if f["_chave_funcionario"] == chave_funcionario and f["_chave_empresa"] == chave_empresa
        ]

        if len(candidatos) == 1:
            candidatos[0]["_usado"] = True
            casados.append({"empresa": e, "funcionario": candidatos[0]})
        elif len(candidatos) > 1:
            ambiguos.append({"empresa": e, "candidatos": candidatos})
        else:
            # Nada na tentativa exata — tenta a versão frouxa (sem espaço nenhum no nome da empresa)
            # antes de desistir. Isso é sugestão, nunca casamento automático.
            chave_funcionario_frouxa = normalizar_nome_frouxo(e.get(CAMPO_NOME_FUNCIONARIO_NA_EMPRESA))
            chave_empresa_frouxa = normalizar_nome_frouxo(e.get(CAMPO_NOME_EMPRESA_NA_EMPRESA))
            candidatos_frouxos = [
                f for f in funcionario
                if not f["_usado"]
                and f["_chave_funcionario_frouxa"] == chave_funcionario_frouxa
                and f["_chave_empresa_frouxa"] == chave_empresa_frouxa
            ]
            if candidatos_frouxos:
                provaveis.append({"empresa": e, "candidatos": candidatos_frouxos})
            else:
                sem_par_funcionario.append(e)

    sem_par_empresa = [f for f in funcionario if not f["_usado"]]

    return {
        "casados": casados,
        "sem_par_funcionario": sem_par_funcionario,
        "sem_par_empresa": sem_par_empresa,
        "ambiguos": ambiguos,
        "provaveis": provaveis,
    }
