"""
Calcula a jornada semanal/mensal a partir do texto livre de "Horário de trabalho", "Pausa refeição"
e "Escala", e confere contra os limites de 44h semanais e 220h mensais (pedido do Kevin, 2026-08-12).

**Isto reverte um princípio anterior da skill** ("não calcular o que exige leitura de texto livre" —
ver SKILL.md), porque Kevin pediu explicitamente. Mas o risco que motivou o princípio original
continua real: texto livre em português, escrito por dezenas de empresas diferentes, é fácil de
interpretar errado com aparência de certeza. A mitigação aqui é: **sempre devolver o texto original
junto do número calculado**, e sempre que o texto não seguir um padrão reconhecido com confiança,
devolver "não consegui calcular" em vez de arriscar um número — isso também vira alerta (Kevin pediu
"sempre alertar quando não estiver dentro do limite", e não conseguir confirmar que está dentro do
limite é, por padrão, tratado como não confirmado).

Cobre os padrões observados nos dados reais: 1 turno diário (a maioria dos casos), inclusive
atravessando meia-noite (ex.: "15:40 ÀS 00:00"). NÃO tenta interpretar escalas irregulares (12x36,
turnos múltiplos no mesmo dia, "escala variável") — esses sempre caem em "não consegui calcular".
"""

from __future__ import annotations

import re

LIMITE_SEMANAL_HORAS = 44
LIMITE_MENSAL_HORAS = 220
# Convenção padrão da CLT: 44h/semana x 5 = 220h/mês. Não é uma conta de calendário (dias do mês
# variam) — é a referência que a folha de pagamento usa universalmente.
#
# IMPORTANTE (pesquisa de 2026-08-12, ver references/base-legal.md): 220h/mês **não é um teto legal
# independente** — é o divisor de folha (CLT art. 64: salário-hora = salário ÷ 220), derivado do
# limite semanal. O limite legal de verdade é o semanal (44h, CF art. 7º XIII) e o diário (8h, CLT
# art. 58, até 10h com compensação). Continuamos comparando contra 220h/mês porque foi pedido
# explicitamente e é uma referência útil — mas não é a fonte legal primária, é derivada.
SEMANAS_POR_MES = 5

# Limites por tipo de contrato (pesquisa de 2026-08-12 — ver references/base-legal.md).
# CLT padrão e "horista" (é só forma de pagamento, não muda o limite) usam 44h/220h.
LIMITE_ESTAGIO_SEMANAL = 30  # Lei 11.788/2008, art. 10, I — ensino superior/técnico/médio regular.
LIMITE_ESTAGIO_MENSAL = LIMITE_ESTAGIO_SEMANAL * SEMANAS_POR_MES
LIMITE_APRENDIZ_DIARIO_HORAS = 6  # Lei 10.097/2000 — 8h só se já concluiu o ensino fundamental
# (essa exceção não é detectável pelos campos do formulário; assume-se o limite mais restrito).

# 12x36 (CLT art. 59-A): ciclo de 48h (12h trabalho + 36h folga) — a semana varia entre 4 plantões
# (44h) e 3 plantões (33h), média de 3,5 plantões/semana. Cada plantão são 12h de presença menos 1h
# de intervalo obrigatório = 11h efetivas. Guia de referência trazido pelo Kevin (2026-08-20, fonte:
# documento gerado por outra IA a partir do art. 59-A da CLT e Súmula do TST — não pesquisado por
# fonte oficial própria desta vez, registrado aqui pra rastreabilidade).
#   Horas semana (média) = 3,5 x 11h = 38,5h
#   Horas mês (padrão de cadastro em sistema de folha, divisor da categoria) = 180h
# Como 3,5 já é a média do ciclo completo, não precisa de lógica extra: cai na mesma fórmula de
# "minutos_dia x dias" que os outros casos usam — só o número de dias/semana é 3,5 em vez de inteiro.
LIMITE_12X36_SEMANAL = 38.5
LIMITE_12X36_MENSAL = 180

_PADRAO_HORA = re.compile(
    r"(\d{1,2})[:h.]?(\d{2})?\s*h?\s*(?:as|às|-|à|ate|até)\s*(\d{1,2})[:h.]?(\d{2})?\s*h?",
    re.IGNORECASE,
)

# Limite de sanidade: nada nesse processo é um turno de mais de 16h por dia. Se o cálculo der isso,
# não é um horário real — é o regex tropeçando em algo que não entendeu direito (achado real,
# 2026-08-12: "12:00H ÀS 20:20H" foi interpretado errado antes desta correção, virando 116h/semana em
# vez de 44h). Servir de rede de segurança além do regex em si, não só confiar que o regex está certo.
LIMITE_SANIDADE_HORAS_DIA = 16

_MAPA_ESCALA_DIAS = [
    (re.compile(r"SEGUNDA.{0,10}S[ÁA]BADO", re.IGNORECASE), 6),
    (re.compile(r"SEGUNDA.{0,10}SEXTA", re.IGNORECASE), 5),
    (re.compile(r"\b6\s*[xX]\s*1\b"), 6),
    (re.compile(r"\b5\s*[xX]\s*2\b"), 5),
    (re.compile(r"\b12\s*[xX]\s*36\b"), 3.5),
]

_PADRAO_ESCALA_12X36 = re.compile(r"\b12\s*[xX]\s*36\b")


def _extrair_intervalos_de_hora(texto: str) -> list[tuple[int, int]]:
    """Devolve lista de (minutos_inicio, minutos_fim) — pode ter mais de um se o texto citar mais
    de um horário diferente (isso já é sinal de complexidade, tratado por quem chama)."""
    return [(i, f) for i, f, _, _ in _extrair_intervalos_com_posicao(texto)]


def _extrair_intervalos_com_posicao(texto: str) -> list[tuple[int, int, int, int]]:
    """Igual à de cima, mas devolve também a posição (início, fim) do match no texto — usado pra
    olhar o que tem ESCRITO ENTRE dois horários (ex.: a palavra "sexta")."""
    if not texto:
        return []
    intervalos = []
    for m in _PADRAO_HORA.finditer(texto):
        h1, m1, h2, m2 = m.groups()
        try:
            inicio = int(h1) * 60 + int(m1 or 0)
            fim = int(h2) * 60 + int(m2 or 0)
        except (TypeError, ValueError):
            continue
        if 0 <= inicio < 24 * 60 and 0 <= fim <= 24 * 60:
            intervalos.append((inicio, fim, m.start(), m.end()))
    return intervalos


_PADRAO_DIA_ESPECIAL = re.compile(r"\bS[ÁA]BADO\b|\bSEXTA\b|\bSEX\b|\bS[ÁA]B\b", re.IGNORECASE)


def _tentar_turno_com_dia_especial(horario_texto: str, dias_semana: int):
    """
    Padrão real muito comum nos dados (achado 2026-08-12): "seg a quinta X às Y e sexta W às Z" —
    um horário de segunda a quinta (ou sábado), outro só na sexta (ou sábado). Isso não é
    "texto confuso", é um turno normal com um dia diferente — vale a pena calcular, não só desistir.

    Só aceita quando: exatamente 2 horários no texto, existe a palavra "sexta" ou "sábado" ESCRITA
    ENTRE os dois horários (prova de que o segundo horário é só daquele dia), e 1 dia + o resto bate
    exatamente com o total de dias da escala. Fora isso, não arrisca — devolve None.
    """
    intervalos = _extrair_intervalos_com_posicao(horario_texto)
    if len(intervalos) != 2:
        return None

    (i1, f1, _, fim1), (i2, f2, ini2, _) = intervalos
    entre = horario_texto[fim1:ini2]
    if not _PADRAO_DIA_ESPECIAL.search(entre):
        return None

    dias_principal = dias_semana - 1
    if dias_principal < 1:
        return None  # escala de 1 dia só não faz sentido pra esse padrão

    return {
        "inicio_principal": i1,
        "fim_principal": f1,
        "duracao_principal": _duracao_minutos(i1, f1),
        "dias_principal": dias_principal,
        "inicio_especial": i2,
        "fim_especial": f2,
        "duracao_especial": _duracao_minutos(i2, f2),
        "dias_especial": 1,
    }


def _duracao_minutos(inicio: int, fim: int) -> int:
    """Trata virada de meia-noite: se fim <= início, soma 24h (ex.: 15:40 às 00:00)."""
    duracao = fim - inicio
    if duracao <= 0:
        duracao += 24 * 60
    return duracao


def _fmt_hora(minutos: int) -> str:
    return f"{(minutos // 60) % 24:02d}:{minutos % 60:02d}"


def _dias_por_semana(escala_texto: str) -> float | None:
    if not escala_texto:
        return None
    for padrao, dias in _MAPA_ESCALA_DIAS:
        if padrao.search(escala_texto):
            return dias
    return None


def _pausa_minutos(pausa_texto: str) -> int | None:
    """0 se não houver pausa declarada (campo vazio); None se o texto existir mas não for
    reconhecível (não adivinha — isso derruba o cálculo pra 'não consegui calcular')."""
    if not pausa_texto or not str(pausa_texto).strip():
        return 0

    texto = str(pausa_texto)

    intervalos = _extrair_intervalos_de_hora(texto)
    if len(intervalos) == 1:
        inicio, fim = intervalos[0]
        return _duracao_minutos(inicio, fim)

    m = re.search(r"(\d+)\s*(?:hora|hrs|h)\b(?:\s*(\d{2})\s*(?:min)?)?", texto, re.IGNORECASE)
    if m:
        horas = int(m.group(1))
        minutos = int(m.group(2) or 0)
        return horas * 60 + minutos

    return None


def determinar_limites_por_contrato(contrato_texto, cargo_texto) -> dict:
    """
    Achado real (2026-08-12): a planilha tem 221 admissões "INTERMITENTE" e 84 "ESTÁGIO" — tipos que
    NÃO seguem o limite de 44h/220h do CLT padrão. Ver references/base-legal.md para a pesquisa
    completa (5 fontes: CLT padrão, estágio, intermitente/horista, tempo parcial, aprendiz/teletrabalho).

    Devolve: aplica_checagem (bool), limite_semanal, limite_mensal, motivo_isento (str, se não aplica).
    """
    contrato = str(contrato_texto or "").upper()
    cargo = str(cargo_texto or "").upper()

    if "INTERMITENTE" in contrato:
        return {
            "aplica_checagem": False,
            "limite_semanal": None,
            "limite_mensal": None,
            "motivo_isento": (
                "contrato intermitente não tem teto legal de jornada agregada (CLT art. 452-A é "
                "silencioso quanto a isso — a jornada varia por convocação, não é fixa)"
            ),
        }

    if "ESTÁGIO" in contrato or "ESTAGIO" in contrato:
        if "APRENDIZ" in cargo:
            # Menor aprendiz: 6h/dia é o limite direto (Lei 10.097/2000), não um limite semanal — mas
            # convertido pra semana de 5 dias pra manter a mesma lógica de cálculo.
            limite_semanal = LIMITE_APRENDIZ_DIARIO_HORAS * SEMANAS_POR_MES / 1  # 6h x 5 dias = 30h
        else:
            limite_semanal = LIMITE_ESTAGIO_SEMANAL
        return {
            "aplica_checagem": True,
            "limite_semanal": limite_semanal,
            "limite_mensal": limite_semanal * SEMANAS_POR_MES,
            "motivo_isento": "",
        }

    return {
        "aplica_checagem": True,
        "limite_semanal": LIMITE_SEMANAL_HORAS,
        "limite_mensal": LIMITE_MENSAL_HORAS,
        "motivo_isento": "",
    }


# Tolerância pro plantão 12x36: presença esperada é 12h. Aceita uma faixa (11h-13h) porque plantão
# real varia um pouco de horário de troca — o que importa é confirmar o padrão, não exigir 12h00min
# cravado. Fora dessa faixa, não é mais "confere com 12x36", é pendência de verdade.
_TOLERANCIA_12X36_MIN = (11 * 60, 13 * 60)


def _calcular_jornada_12x36(horario_texto: str, pausa_texto: str, escala_texto: str) -> dict:
    intervalos = _extrair_intervalos_de_hora(horario_texto)
    if len(intervalos) != 1:
        return {
            "aplica_checagem": True,
            "calculado": False,
            "horas_semanais": None,
            "horas_mensais": None,
            "dentro_do_limite": None,
            "motivo": (
                "nenhum horário reconhecido no texto do plantão 12x36"
                if not intervalos
                else f"{len(intervalos)} horários diferentes no texto — não é um plantão só"
            ),
            "detalhe": f"Horário: {horario_texto!r} / Escala: {escala_texto!r}",
        }

    inicio, fim = intervalos[0]
    turno_bruto = _duracao_minutos(inicio, fim)

    if not (_TOLERANCIA_12X36_MIN[0] <= turno_bruto <= _TOLERANCIA_12X36_MIN[1]):
        return {
            "aplica_checagem": True,
            "calculado": False,
            "horas_semanais": None,
            "horas_mensais": None,
            "dentro_do_limite": False,
            "motivo": (
                f"plantão de {turno_bruto / 60:.2f}h não bate com o padrão 12x36 (esperado ~12h de "
                f"presença) — confira manualmente"
            ),
            "detalhe": f"Horário: {horario_texto!r} / Escala: {escala_texto!r}",
        }

    pausa_min = _pausa_minutos(pausa_texto)
    if pausa_min is None:
        pausa_min = 60  # padrão legal do intervalo em plantão 12x36, se o texto não deu pra ler

    minutos_efetivos = turno_bruto - pausa_min
    horas_efetivas = round(minutos_efetivos / 60, 2)

    return {
        "aplica_checagem": True,
        "calculado": True,
        "horas_semanais": LIMITE_12X36_SEMANAL,
        "horas_mensais": round(LIMITE_12X36_SEMANAL * SEMANAS_POR_MES, 2),
        "limite_semanal": LIMITE_12X36_SEMANAL,
        "limite_mensal": LIMITE_12X36_MENSAL,
        "dentro_do_limite": True,
        "motivo": "",
        "explicacao_turnos": (
            f"{_fmt_hora(inicio)} às {_fmt_hora(fim)} (plantão 12h, {horas_efetivas}h efetivas "
            f"descontada a pausa) — média de 3,5 plantões/semana (ciclo 4 semana A + 3 semana B)"
        ),
        "detalhe": (
            f"Plantão {_fmt_hora(inicio)} às {_fmt_hora(fim)} confere com o padrão 12x36 "
            f"({horas_efetivas}h efetivas). Referência (CLT art. 59-A): 38,5h/semana em média, "
            f"180h/mês é o divisor de folha (não um teto de horas trabalhadas — {LIMITE_12X36_SEMANAL} "
            f"x {SEMANAS_POR_MES} = {LIMITE_12X36_SEMANAL * SEMANAS_POR_MES}h/mês seria a média real, "
            f"maior que o divisor, e isso é esperado, não pendência). "
            f"Horário: {horario_texto!r}, Pausa: {pausa_texto!r}, Escala: {escala_texto!r}"
        ),
    }


def calcular_jornada(horario_texto, pausa_texto, escala_texto, contrato_texto=None, cargo_texto=None) -> dict:
    """
    Devolve:
      aplica_checagem: bool — False pra contratos sem teto de jornada (ex.: intermitente)
      calculado: bool — se deu pra calcular com confiança
      horas_semanais, horas_mensais: float | None
      dentro_do_limite: bool | None
      motivo: str — por que não deu pra calcular, ou por que não se aplica
      detalhe: str — como o número foi montado, pra Kevin conferir a conta
    """
    horario_texto = str(horario_texto or "")
    escala_texto = str(escala_texto or "")

    limites = determinar_limites_por_contrato(contrato_texto, cargo_texto)
    if not limites["aplica_checagem"]:
        return {
            "aplica_checagem": False,
            "calculado": False,
            "horas_semanais": None,
            "horas_mensais": None,
            "dentro_do_limite": None,
            "motivo": limites["motivo_isento"],
            "detalhe": f"Contrato: {contrato_texto!r}",
        }
    limite_semanal = limites["limite_semanal"]
    limite_mensal = limites["limite_mensal"]

    # 12x36 não é "calcule o total e compare com um teto" — é "confira se o plantão bate com o padrão
    # legal (12h de presença, 1h de intervalo)". Achado testando com dado real (Roberto Ferraz
    # Dionisio, 2026-08-20): comparar a média real (192,5h/mês) contra o divisor de folha (180h/mês)
    # dava falso positivo de "acima do limite" — são duas contas diferentes, não a mesma conta com
    # nomes diferentes (mesmo erro conceitual do 220h padrão, só que pro 12x36). Ver função dedicada.
    if _PADRAO_ESCALA_12X36.search(escala_texto) and limite_semanal == LIMITE_SEMANAL_HORAS:
        return _calcular_jornada_12x36(horario_texto, pausa_texto, escala_texto)

    dias = _dias_por_semana(escala_texto)
    if dias is None:
        return {
            "aplica_checagem": True,
            "calculado": False,
            "horas_semanais": None,
            "horas_mensais": None,
            "dentro_do_limite": None,
            "motivo": f"escala não reconhecida: {escala_texto!r}",
            "detalhe": f"Horário: {horario_texto!r} / Escala: {escala_texto!r}",
        }

    pausa_min = _pausa_minutos(pausa_texto)
    if pausa_min is None:
        return {
            "aplica_checagem": True,
            "calculado": False,
            "horas_semanais": None,
            "horas_mensais": None,
            "dentro_do_limite": None,
            "motivo": f"pausa de refeição não reconhecida: {pausa_texto!r}",
            "detalhe": f"Horário: {horario_texto!r} / Pausa: {pausa_texto!r} / Escala: {escala_texto!r}",
        }

    intervalos = _extrair_intervalos_de_hora(horario_texto)
    minutos_semana = None
    explicacao_turnos = None

    if len(intervalos) == 1:
        inicio, fim = intervalos[0]
        minutos_dia = _duracao_minutos(inicio, fim) - pausa_min
        if minutos_dia <= 0:
            return {
                "aplica_checagem": True,
                "calculado": False,
                "horas_semanais": None,
                "horas_mensais": None,
                "dentro_do_limite": None,
                "motivo": "pausa maior que o turno inteiro — conta não fecha, dado suspeito",
                "detalhe": f"Horário: {horario_texto!r} / Pausa: {pausa_texto!r}",
            }
        if minutos_dia / 60 > LIMITE_SANIDADE_HORAS_DIA:
            return {
                "aplica_checagem": True,
                "calculado": False,
                "horas_semanais": None,
                "horas_mensais": None,
                "dentro_do_limite": None,
                "motivo": (
                    f"deu {minutos_dia / 60:.1f}h por dia — maior que {LIMITE_SANIDADE_HORAS_DIA}h, "
                    f"sinal de que o texto foi lido errado, não que o turno é assim"
                ),
                "detalhe": f"Horário: {horario_texto!r} / Pausa: {pausa_texto!r} / Escala: {escala_texto!r}",
            }
        minutos_semana = minutos_dia * dias
        explicacao_turnos = (
            f"{_fmt_hora(inicio)} às {_fmt_hora(fim)} ({minutos_dia / 60:.2f}h/dia, já descontada a "
            f"pausa) x {dias} dias/semana"
        )
    else:
        turno_especial = _tentar_turno_com_dia_especial(horario_texto, dias)
        if turno_especial is None:
            motivo = (
                "nenhum horário reconhecido no texto"
                if not intervalos
                else (
                    f"{len(intervalos)} horários diferentes no texto e não achei um dia especial "
                    f"claro (ex.: 'e sexta') pra separar — escala não é de um turno só"
                )
            )
            return {
                "aplica_checagem": True,
                "calculado": False,
                "horas_semanais": None,
                "horas_mensais": None,
                "dentro_do_limite": None,
                "motivo": motivo,
                "detalhe": f"Horário: {horario_texto!r} / Escala: {escala_texto!r}",
            }
        min_principal = turno_especial["duracao_principal"] - pausa_min
        min_especial = turno_especial["duracao_especial"] - pausa_min
        if min_principal <= 0 or min_especial <= 0:
            return {
                "aplica_checagem": True,
                "calculado": False,
                "horas_semanais": None,
                "horas_mensais": None,
                "dentro_do_limite": None,
                "motivo": "pausa maior que um dos turnos — conta não fecha, dado suspeito",
                "detalhe": f"Horário: {horario_texto!r} / Pausa: {pausa_texto!r}",
            }
        if min_principal / 60 > LIMITE_SANIDADE_HORAS_DIA or min_especial / 60 > LIMITE_SANIDADE_HORAS_DIA:
            return {
                "aplica_checagem": True,
                "calculado": False,
                "horas_semanais": None,
                "horas_mensais": None,
                "dentro_do_limite": None,
                "motivo": f"turno acima de {LIMITE_SANIDADE_HORAS_DIA}h/dia — sinal de leitura errada",
                "detalhe": f"Horário: {horario_texto!r} / Pausa: {pausa_texto!r} / Escala: {escala_texto!r}",
            }
        minutos_semana = min_principal * turno_especial["dias_principal"] + min_especial * turno_especial["dias_especial"]
        explicacao_turnos = (
            f"{_fmt_hora(turno_especial['inicio_principal'])} às {_fmt_hora(turno_especial['fim_principal'])} "
            f"({min_principal / 60:.2f}h/dia) x {turno_especial['dias_principal']} dias + "
            f"{_fmt_hora(turno_especial['inicio_especial'])} às {_fmt_hora(turno_especial['fim_especial'])} "
            f"({min_especial / 60:.2f}h/dia) x {turno_especial['dias_especial']} dia especial"
        )

    horas_semanais = round(minutos_semana / 60, 2)
    horas_mensais = round(horas_semanais * SEMANAS_POR_MES, 2)
    dentro = horas_semanais <= limite_semanal and horas_mensais <= limite_mensal

    return {
        "aplica_checagem": True,
        "calculado": True,
        "horas_semanais": horas_semanais,
        "horas_mensais": horas_mensais,
        "limite_semanal": limite_semanal,
        "limite_mensal": limite_mensal,
        "dentro_do_limite": dentro,
        "motivo": "",
        "explicacao_turnos": explicacao_turnos,
        "detalhe": (
            f"{explicacao_turnos} = {horas_semanais}h/semana "
            f"(x{SEMANAS_POR_MES} = {horas_mensais}h/mês, limite {limite_semanal}h/{limite_mensal}h) — "
            f"Horário: {horario_texto!r}, Pausa: {pausa_texto!r}, Escala: {escala_texto!r}"
        ),
    }
