# Versão anterior (PowerShell) — arquivada em 2026-08-11

Estes quatro scripts foram a primeira versão da skill, construída e validada com dado real (caso do
Alisson, o achado do CPF duplicado entre Auany e Wandrey, etc.).

Foram substituídos pelos equivalentes em Python (`../ler_planilha.py`, `../casar_admissoes.py`,
`../conferir_admissao.py`, `../executar_conferencia.py`) por um motivo só: **velocidade**. No mesmo
arquivo real, a versão PowerShell levava ~60 segundos; a versão Python leva ~2 segundos — quase 30x
mais rápido, porque processa a planilha inteira em bloco em vez de célula por célula.

Toda a lógica de negócio (regras de documento, CPF/PIS, dependente, corte de data, CPF duplicado) é a
mesma nas duas versões — a reescrita foi testada contra os mesmos casos reais antes de substituir.

Mantidos aqui só como referência histórica. Não há necessidade de rodar estes scripts — se algum dia a
máquina não tiver Python disponível, é possível reativá-los, mas a versão Python é a atual.
