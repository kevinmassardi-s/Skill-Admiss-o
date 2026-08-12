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
SEMANAS_POR_MES = 5

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
]


def _extrair_intervalos_de_hora(texto: str) -> list[tuple[int, int]]:
    """Devolve lista de (minutos_inicio, minutos_fim) — pode ter mais de um se o texto citar mais
    de um horário diferente (isso já é sinal de complexidade, tratado por quem chama)."""
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
            intervalos.append((inicio, fim))
    return intervalos


def _duracao_minutos(inicio: int, fim: int) -> int:
    """Trata virada de meia-noite: se fim <= início, soma 24h (ex.: 15:40 às 00:00)."""
    duracao = fim - inicio
    if duracao <= 0:
        duracao += 24 * 60
    return duracao


def _dias_por_semana(escala_texto: str) -> int | None:
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


def calcular_jornada(horario_texto, pausa_texto, escala_texto) -> dict:
    """
    Devolve:
      calculado: bool — se deu pra calcular com confiança
      horas_semanais, horas_mensais: float | None
      dentro_do_limite: bool | None
      motivo: str — por que não deu pra calcular, quando for o caso
      detalhe: str — como o número foi montado, pra Kevin conferir a conta
    """
    horario_texto = str(horario_texto or "")
    escala_texto = str(escala_texto or "")

    intervalos = _extrair_intervalos_de_hora(horario_texto)
    if len(intervalos) != 1:
        motivo = (
            "nenhum horário reconhecido no texto"
            if not intervalos
            else f"{len(intervalos)} horários diferentes no texto — escala não é de um turno só"
        )
        return {
            "calculado": False,
            "horas_semanais": None,
            "horas_mensais": None,
            "dentro_do_limite": None,
            "motivo": motivo,
            "detalhe": f"Horário: {horario_texto!r} / Escala: {escala_texto!r}",
        }

    dias = _dias_por_semana(escala_texto)
    if dias is None:
        return {
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
            "calculado": False,
            "horas_semanais": None,
            "horas_mensais": None,
            "dentro_do_limite": None,
            "motivo": f"pausa de refeição não reconhecida: {pausa_texto!r}",
            "detalhe": f"Horário: {horario_texto!r} / Pausa: {pausa_texto!r} / Escala: {escala_texto!r}",
        }

    inicio, fim = intervalos[0]
    minutos_dia = _duracao_minutos(inicio, fim) - pausa_min
    if minutos_dia <= 0:
        return {
            "calculado": False,
            "horas_semanais": None,
            "horas_mensais": None,
            "dentro_do_limite": None,
            "motivo": "pausa maior que o turno inteiro — conta não fecha, dado suspeito",
            "detalhe": f"Horário: {horario_texto!r} / Pausa: {pausa_texto!r}",
        }
    if minutos_dia / 60 > LIMITE_SANIDADE_HORAS_DIA:
        return {
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

    horas_semanais = round(minutos_dia * dias / 60, 2)
    horas_mensais = round(horas_semanais * SEMANAS_POR_MES, 2)
    dentro = horas_semanais <= LIMITE_SEMANAL_HORAS and horas_mensais <= LIMITE_MENSAL_HORAS

    return {
        "calculado": True,
        "horas_semanais": horas_semanais,
        "horas_mensais": horas_mensais,
        "dentro_do_limite": dentro,
        "motivo": "",
        "detalhe": (
            f"{minutos_dia / 60:.2f}h/dia x {dias} dias/semana = {horas_semanais}h/semana "
            f"(x{SEMANAS_POR_MES} = {horas_mensais}h/mês) — Horário: {horario_texto!r}, "
            f"Pausa: {pausa_texto!r}, Escala: {escala_texto!r}"
        ),
    }
