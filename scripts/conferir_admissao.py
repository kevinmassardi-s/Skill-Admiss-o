"""
Aplica o checklist de references/regras-conferencia.md a uma admissão já casada (par
empresa/funcionario) e devolve pendências + um resumo pronto para digitar no Domínio.

Não calcula horas semanais a partir do horário de trabalho (é texto livre — ver o princípio em
SKILL.md) e não trata cargo sem CBO ou ASO como pendência (confirmado fora de escopo).

Reescrita em Python (2026-08-11) — mesma lógica da versão PowerShell original, incluindo os dois
achados reais de 2026-08-11: reconstrução segura de CPF/PIS a partir de notação científica, e detecção
de CPF duplicado entre pessoas diferentes do mesmo lote (feita no orquestrador, não aqui, porque exige
comparar entre admissões).
"""

from __future__ import annotations

from calcular_jornada import calcular_jornada

# Nomes exatos das colunas, conforme references/estrutura-planilha.md.
COL_EMPRESA_CARGO = "CARGO:"
COL_EMPRESA_DATA_ADMISSAO = "DATA DE ADMISSÃO:"
COL_EMPRESA_SALARIO = "SALÁRIO DO FUNCIONÁRIO:"
COL_EMPRESA_HORARIO = "HORÁRIO DE TRABALHO:"
COL_EMPRESA_PAUSA = "PAUSA REFEIÇÃO"
COL_EMPRESA_ESCALA = "ESCALA:"
COL_EMPRESA_CONTRATO = "CONTRATO:"
COL_EMPRESA_VT = "DESCONTO DE 6% DE VALE TRANSPORTE?"
COL_EMPRESA_ADIANTAMENTO = (
    "O colaborador terá adiantamento salarial (vale) a partir do mês da admissão "
    "independente de ter 15 dias trabalhados?"
)
COL_EMPRESA_COMPENSACAO = "Acordo de compensação de horas"
COL_EMPRESA_PRORROGACAO = "Acordo de prorrogação de horas"

COL_FUNC_CPF = "CPF:"
COL_FUNC_PIS = "PIS:"
COL_FUNC_RG = "RG:"
COL_FUNC_NOME = "NOME COMPLETO:"
COL_EMPRESA_NOME = "EMPRESA: (RAZÃO SOCIAL)"

# Confirmado por Kevin (2026-08-11): só dois documentos são realmente obrigatórios. "Documento oficial
# com foto" é satisfeito por QUALQUER UM destes dois (não precisam ser os dois):
COL_DOC_RG = "RG - FRENTE E VERSO:"
COL_DOC_CNH = "CNH (CASO POSSUA):"
COL_DOC_COMPROVANTE_ENDERECO = "COMPROVANTE DE ENDEREÇO COM CEP E BAIRRO:"

# Aparecem no resumo, mas NUNCA viram pendência se faltarem.
DOCUMENTOS_INFORMATIVOS = [
    "TÍTULO DE ELEITOR:",
    "FOTO 3X4",
    "DISPENSA MILITAR:",
    "CERTIDÃO DE CASAMENTO (SE TIVER):",
]

COL_CERTIDAO_DEPENDENTE = "CERTIDÃO DE NASCIMENTO (FILHOS MENORES DE 14 ANOS):"
COL_CPF_DEPENDENTE = "CPF (FILHOS MENORES DE 14 ANOS):"


def _vazio(valor) -> bool:
    return valor is None or str(valor).strip() == ""


def resolver_documento_pessoal(valor) -> dict:
    """
    CPF/PIS às vezes chegam do Excel como número (float) em vez de texto, porque a célula foi
    digitada/lida como número. openpyxl entrega esse valor já como float Python — não como string em
    notação científica como no XML bruto (isso era uma particularidade da leitura via PowerShell/XML;
    aqui o problema é o mesmo, só que já resolvido pelo tipo nativo do Python).

    Testado com um caso real (RG físico do colaborador, 2026-08-11): os dígitos por baixo bateram
    exatamente com o CPF real. Isso é seguro de reconstruir automaticamente PORQUE CPF/PIS têm 11
    dígitos — um float (double) representa qualquer inteiro de até 15-16 dígitos sem perda, então
    reconstruir um número de 11 dígitos nunca arredonda errado. Não é "inventar dado": é desfazer uma
    conversão de tipo que o Excel aplicou, não adivinhar um dígito que não existe.

    Se a reconstrução não der exatamente 11 dígitos, não é mais um problema de formatação — é um dado
    genuinamente errado, e isso continua sendo pendência de verdade.
    """
    if _vazio(valor):
        return {"valor": "", "reconstruido": False, "valido": False}

    if isinstance(valor, float):
        digitos = str(int(round(valor)))
        if len(digitos) == 11:
            return {"valor": digitos, "reconstruido": True, "valido": True}
        return {"valor": str(valor), "reconstruido": True, "valido": False}

    texto = str(valor)
    digitos = "".join(c for c in texto if c.isdigit())
    return {"valor": texto, "reconstruido": False, "valido": len(digitos) == 11}


def confirmar_admissao(par: dict) -> dict:
    e = par["empresa"]
    f = par["funcionario"]
    pendencias: list[str] = []

    # --- Documentos: só dois são obrigatórios ---
    tem_rg = not _vazio(f.get(COL_DOC_RG))
    tem_cnh = not _vazio(f.get(COL_DOC_CNH))
    if not tem_rg and not tem_cnh:
        pendencias.append("Documento oficial com foto faltando (nem RG frente/verso, nem CNH)")
    if _vazio(f.get(COL_DOC_COMPROVANTE_ENDERECO)):
        pendencias.append(f"Documento faltando: {COL_DOC_COMPROVANTE_ENDERECO}")

    # --- Dependente: precisa de prova do CPF, não só a certidão ---
    tem_certidao_dependente = not _vazio(f.get(COL_CERTIDAO_DEPENDENTE))
    if tem_certidao_dependente:
        tem_cpf_dependente = not _vazio(f.get(COL_CPF_DEPENDENTE))
        if not tem_cpf_dependente:
            pendencias.append(
                "Confirmar CPF do dependente: certidão de nascimento anexada, mas a coluna de CPF "
                "do filho está vazia — checar se o CPF já aparece na própria certidão ou em outro "
                "documento com foto antes de pedir de novo"
            )

    # --- CPF / PIS do colaborador ---
    cpf_resolvido = resolver_documento_pessoal(f.get(COL_FUNC_CPF))
    if _vazio(f.get(COL_FUNC_CPF)):
        pendencias.append("CPF do colaborador faltando")
    elif not cpf_resolvido["valido"]:
        pendencias.append(
            f"CPF do colaborador com dígitos inválidos, não é só formatação "
            f"(conferir na planilha): '{f.get(COL_FUNC_CPF)}'"
        )

    # PIS não é mais obrigatório (Kevin, 2026-08-11): desde o Decreto 9.723/2019 o CPF substituiu o
    # PIS como identificador — ver references/base-legal.md. Se vier preenchido, ótimo, e ainda vale
    # checar o formato; se estiver vazio, não é pendência.
    pis_resolvido = resolver_documento_pessoal(f.get(COL_FUNC_PIS))
    if not _vazio(f.get(COL_FUNC_PIS)) and not pis_resolvido["valido"]:
        pendencias.append(
            f"PIS do colaborador com dígitos inválidos, não é só formatação "
            f"(conferir na planilha): '{f.get(COL_FUNC_PIS)}'"
        )

    # --- Jornada: limite varia por tipo de contrato (pesquisa de 2026-08-12, ver base-legal.md) ---
    jornada = calcular_jornada(
        e.get(COL_EMPRESA_HORARIO),
        e.get(COL_EMPRESA_PAUSA),
        e.get(COL_EMPRESA_ESCALA),
        contrato_texto=e.get(COL_EMPRESA_CONTRATO),
        cargo_texto=e.get(COL_EMPRESA_CARGO),
    )
    if not jornada["aplica_checagem"]:
        pass  # ex.: intermitente — sem teto legal de jornada, não é pendência nem "dentro do limite"
    elif not jornada["calculado"]:
        limite_txt = (
            f"{jornada.get('limite_semanal')}h/{jornada.get('limite_mensal')}h"
            if jornada.get("limite_semanal") is not None
            else "44h/220h"
        )
        pendencias.append(
            f"Jornada: não deu pra calcular automaticamente ({jornada['motivo']}) — confira "
            f"manualmente se está dentro do limite ({limite_txt}). {jornada['detalhe']}"
        )
    elif not jornada["dentro_do_limite"]:
        pendencias.append(
            f"Jornada ACIMA DO LIMITE: {jornada['horas_semanais']}h/semana, "
            f"{jornada['horas_mensais']}h/mês (limite {jornada['limite_semanal']}h/"
            f"{jornada['limite_mensal']}h). {jornada['detalhe']}"
        )

    # Aprendiz: hora extra/compensação é proibida em qualquer hipótese (Lei 10.097/2000) — checagem
    # direta nos campos que já existem, independente de ter dado pra calcular a jornada ou não.
    if "APRENDIZ" in str(e.get(COL_EMPRESA_CARGO) or "").upper():
        tem_compensacao = str(e.get(COL_EMPRESA_COMPENSACAO) or "").strip().upper() == "SIM"
        tem_prorrogacao = str(e.get(COL_EMPRESA_PRORROGACAO) or "").strip().upper() == "SIM"
        if tem_compensacao or tem_prorrogacao:
            pendencias.append(
                "Aprendiz com acordo de compensação/prorrogação de horas marcado — isso é proibido "
                "por lei pra aprendiz (Lei 10.097/2000), não pode ser lançado assim"
            )

    nome_colaborador = f.get(COL_FUNC_NOME)
    nome_empresa = e.get(COL_EMPRESA_NOME)

    cpf_txt = cpf_resolvido["valor"]
    if cpf_resolvido["reconstruido"] and cpf_resolvido["valido"]:
        cpf_txt += " (reconstruído da notação científica — confira)"
    pis_txt = pis_resolvido["valor"]
    if pis_resolvido["reconstruido"] and pis_resolvido["valido"]:
        pis_txt += " (reconstruído da notação científica — confira)"

    linhas_resumo = [
        f"=== {nome_colaborador} — {nome_empresa} ===",
        f"Cargo: {e.get(COL_EMPRESA_CARGO)}",
        f"Data de admissão: {e.get(COL_EMPRESA_DATA_ADMISSAO)}",
        f"Salário: {e.get(COL_EMPRESA_SALARIO)}",
        f"Contrato: {e.get(COL_EMPRESA_CONTRATO)}",
        f"Horário de trabalho: {e.get(COL_EMPRESA_HORARIO)}"
        + (
            f" -> contrato {e.get(COL_EMPRESA_CONTRATO)}: sem teto legal de jornada agregada, "
            f"não conferido ({jornada['motivo']})"
            if not jornada["aplica_checagem"]
            else (
                # 12x36: não é "some e compare com teto" — o próprio explicacao_turnos já diz se o
                # plantão confere com o padrão. Achado real (2026-08-20): mostrar "192.5h/mês (DENTRO
                # do limite 180h)" parece contraditório (192,5 > 180), porque 180h é o divisor de
                # folha, não um teto — ver calcular_jornada.py.
                f" -> {jornada['explicacao_turnos']}"
                if jornada["calculado"] and "plantão 12h" in jornada.get("explicacao_turnos", "")
                else (
                    f" -> {jornada['explicacao_turnos']} = {jornada['horas_semanais']}h/semana, "
                    f"{jornada['horas_mensais']}h/mês "
                    f"({'DENTRO' if jornada['dentro_do_limite'] else 'ACIMA'} do limite "
                    f"{jornada['limite_semanal']}h/{jornada['limite_mensal']}h)"
                    if jornada["calculado"]
                    else f" -> não calculado automaticamente ({jornada['motivo']}), CONFERIR À MÃO"
                )
            )
        ),
        f"Pausa refeição: {e.get(COL_EMPRESA_PAUSA)}",
        f"Escala: {e.get(COL_EMPRESA_ESCALA)}",
        f"VT (desconto 6%): {e.get(COL_EMPRESA_VT)}",
        f"Adiantamento salarial: {e.get(COL_EMPRESA_ADIANTAMENTO)}",
        f"Acordo de compensação de horas: {e.get(COL_EMPRESA_COMPENSACAO)}",
        f"Acordo de prorrogação de horas: {e.get(COL_EMPRESA_PRORROGACAO)}",
        "",
        f"RG: {f.get(COL_FUNC_RG)}   CPF: {cpf_txt}   PIS: {pis_txt}",
        f"Tem dependente: {'SIM' if tem_certidao_dependente else 'NÃO'}",
        "",
        "Documentos:",
    ]
    for nome_doc in [COL_DOC_RG, COL_DOC_CNH, COL_DOC_COMPROVANTE_ENDERECO] + DOCUMENTOS_INFORMATIVOS:
        link = f.get(nome_doc)
        marca = "(faltando)" if _vazio(link) else link
        linhas_resumo.append(f"  - {nome_doc} {marca}")
    if tem_certidao_dependente:
        linhas_resumo.append(f"  - {COL_CERTIDAO_DEPENDENTE} {f.get(COL_CERTIDAO_DEPENDENTE)}")
        linhas_resumo.append(f"  - {COL_CPF_DEPENDENTE} {f.get(COL_CPF_DEPENDENTE)}")

    return {
        "nome_colaborador": nome_colaborador,
        "nome_empresa": nome_empresa,
        "pendencias": pendencias,
        "resumo": "\n".join(linhas_resumo),
        "cpf_valido": cpf_resolvido["valor"] if cpf_resolvido["valido"] else None,
    }
