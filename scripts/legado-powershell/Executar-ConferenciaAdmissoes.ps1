<#
.SINOPSE
    Script de entrada. Encadeia leitura -> casamento -> conferência e imprime um resumo legível:
    o que está pronto para lançar, o que está pendente (com o motivo) e o que ficou ambíguo
    (aguardando escolha humana). Nunca mistura os três grupos.

.USO
    powershell -File .\Executar-ConferenciaAdmissoes.ps1 -CaminhoArquivo "C:\...\FORMULÁRIO DE ADMISSÃO - EXTERNO.xlsx"

    Parâmetro opcional -IncluirTodosOsStatus: por padrão, só processa admissões cujo status (coluna
    "DOC PENDENTE" na aba EMPRESA) não é SIM/CANCELOU/DESISTIU/DUPLICADO/EM AUDITORIA (ver
    references/regras-conferencia.md). Passe esse switch para processar tudo, inclusive o que já foi
    marcado concluído.

    Parâmetro opcional -DataCorte (padrão: 2026-08-11, decisão do Kevin nesta data): só processa
    admissões da aba EMPRESA cujo "Carimbo de data/hora" é dessa data em diante. O backlog antigo (como
    o caso do Alisson, de 2025, ainda sem status de conclusão) fica de fora — é tratado à parte, não por
    esta rotina. Passe uma data diferente (formato yyyy-MM-dd) pra mudar o corte, ou combine com
    -IncluirTodosOsStatus e uma data bem antiga pra ver o backlog inteiro se precisar revisá-lo algum dia.
#>

param(
    [Parameter(Mandatory = $true)][string]$CaminhoArquivo,
    [switch]$IncluirTodosOsStatus,
    [string]$DataCorte = "2026-08-11"
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$pasta = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $pasta "Ler-PlanilhaAdmissao.ps1")
. (Join-Path $pasta "Casar-Admissoes.ps1")
. (Join-Path $pasta "Conferir-Admissao.ps1")

$ColStatusEmpresa = "DOC PENDENTE"
$ColCarimboEmpresa = "Carimbo de data/hora"
$ColStatusFuncionario = "FEITO?"
$StatusQueNaoGeramTrabalho = @("SIM", "CANCELOU", "DESISTIU", "DUPLICADO", "EM AUDITORIA")

function Test-StatusAtivo {
    param([string]$Status)
    return [string]::IsNullOrWhiteSpace($Status) -or ($StatusQueNaoGeramTrabalho -notcontains $Status.Trim().ToUpperInvariant())
}

# Carimbo de data/hora do Google Forms vem como serial do Excel (dias desde 1899-12-30).
$epocaExcel = [datetime]"1899-12-30"
$serialDataCorte = ([datetime]$DataCorte - $epocaExcel).TotalDays

Write-Host "Lendo $CaminhoArquivo ..."
$dados = Get-PlanilhaAdmissao -CaminhoArquivo $CaminhoArquivo
Write-Host "  EMPRESA: $($dados.Empresa.Count) linhas | FUNCIONARIO: $($dados.Funcionario.Count) linhas"

$empresaParaProcessar = $dados.Empresa
$funcionarioParaProcessar = $dados.Funcionario
if (-not $IncluirTodosOsStatus) {
    # Só a EMPRESA é filtrada por status: é a aba que Kevin usa como referência de "feito ou não".
    # A FUNCIONARIO é casada por inteiro (sem filtro de status próprio) porque não temos confirmação
    # de que a coluna FEITO? da aba FUNCIONARIO é mantida em sincronia com a da EMPRESA — ver
    # references/estrutura-planilha.md. Filtrar os dois lados de forma independente arriscava perder
    # uma resposta válida do funcionário só porque o status daquela aba ficou desatualizado.
    $empresaParaProcessar = @($dados.Empresa | Where-Object { Test-StatusAtivo $_.$ColStatusEmpresa })
    $puladasEmpresa = $dados.Empresa.Count - $empresaParaProcessar.Count
    Write-Host "  EMPRESA: $puladasEmpresa linha(s) já concluída/cancelada/duplicada/desistida — não processadas."

    # Corte por data (decisão do Kevin, 2026-08-11): backlog antigo sem status de conclusão (ex.: o
    # caso do Alisson, de 2025) fica de fora do dia a dia — não é processado por esta rotina.
    $antesDoCorteEmpresa = @($empresaParaProcessar | Where-Object { [double]$_.$ColCarimboEmpresa -lt $serialDataCorte })
    $empresaParaProcessar = @($empresaParaProcessar | Where-Object { [double]$_.$ColCarimboEmpresa -ge $serialDataCorte })
    Write-Host "  EMPRESA: $($antesDoCorteEmpresa.Count) linha(s) anteriores a $DataCorte, ainda sem status de conclusão — backlog antigo, fora do escopo desta rotina."
    Write-Host "  (use -IncluirTodosOsStatus e/ou -DataCorte pra revisar o backlog antigo se precisar algum dia)"
}

$casamento = Get-AdmissoesCasadas -Empresa $empresaParaProcessar -Funcionario $funcionarioParaProcessar

$resultados = @($casamento.Casados | ForEach-Object { Confirmar-Admissao -Par $_ })

# CPF duplicado entre pessoas diferentes do mesmo lote: achado real de 2026-08-11 — duas admissões
# distintas (Auany Vieira Pereira e Wandrey Juneo Oliveira Cardoso) tinham o MESMO CPF reconstruído.
# Abrindo o documento de cada uma, só uma estava certa — a outra tinha o CPF de outra pessoa colado na
# linha errada. Essa checagem pega esse tipo de erro sem precisar abrir imagem toda vez: se dois nomes
# diferentes caem no mesmo CPF, pelo menos um está errado, então os dois viram pendência.
$gruposPorCpf = $resultados | Where-Object { $_.CpfValido } | Group-Object -Property CpfValido
foreach ($grupo in $gruposPorCpf) {
    if ($grupo.Count -gt 1) {
        foreach ($r in $grupo.Group) {
            $r.Pendencias += "CPF ($($r.CpfValido)) repetido em outra admissão deste lote ($(($grupo.Group | Where-Object { $_ -ne $r } | ForEach-Object { $_.NomeColaborador }) -join ', ')) — CPF não pode ser o mesmo pra pessoas diferentes; confirmar com o documento antes de lançar qualquer uma das duas"
        }
    }
}

$prontas = @($resultados | Where-Object { $_.Pendencias.Count -eq 0 })
$comPendencia = @($resultados | Where-Object { $_.Pendencias.Count -gt 0 })

Write-Host ""
Write-Host "========================================"
Write-Host "PRONTAS PARA LANÇAR NO DOMÍNIO: $($prontas.Count)"
Write-Host "========================================"
foreach ($r in $prontas) {
    Write-Host ""
    Write-Host $r.Resumo
}

Write-Host ""
Write-Host "========================================"
Write-Host "COM PENDÊNCIA: $($comPendencia.Count)"
Write-Host "========================================"
foreach ($r in $comPendencia) {
    Write-Host ""
    Write-Host "$($r.NomeColaborador) — $($r.NomeEmpresa)"
    foreach ($p in $r.Pendencias) { Write-Host "  - $p" }
}

Write-Host ""
Write-Host "========================================"
Write-Host "AMBÍGUAS (mais de um candidato — escolha manual): $($casamento.Ambiguos.Count)"
Write-Host "========================================"
foreach ($amb in $casamento.Ambiguos) {
    Write-Host ""
    Write-Host "Empresa: $($amb.Empresa.'EMPRESA: (RAZÃO SOCIAL)') / Funcionário: $($amb.Empresa.'NOME COMPLETO DO FUNCIONÁRIO:')"
    Write-Host "  Candidatos na aba FUNCIONARIO (linha): $(($amb.Candidatos | ForEach-Object { $_._Linha }) -join ', ')"
}

Write-Host ""
Write-Host "========================================"
Write-Host "SEM PAR NA ABA FUNCIONARIO: $($casamento.SemParFuncionario.Count)"
Write-Host "========================================"
foreach ($e in $casamento.SemParFuncionario) {
    Write-Host "  Linha $($e._Linha): $($e.'NOME COMPLETO DO FUNCIONÁRIO:') / $($e.'EMPRESA: (RAZÃO SOCIAL)')"
}

Write-Host ""
Write-Host "========================================"
Write-Host "SEM PAR NA ABA EMPRESA: $($casamento.SemParEmpresa.Count)"
Write-Host "(inclui respostas antigas de FUNCIONARIO cuja EMPRESA já foi concluída — número alto aqui"
Write-Host " é esperado e não é necessariamente uma pendência de hoje)"
Write-Host "========================================"
foreach ($f in $casamento.SemParEmpresa) {
    Write-Host "  Linha $($f._Linha): $($f.'NOME COMPLETO:') / $($f.'NOME DA EMPRESA: (RAZAO SOCIAL)')"
}
