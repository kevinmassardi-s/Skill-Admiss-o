<#
.SINOPSE
    Casa cada linha da aba EMPRESA com a linha correspondente da aba FUNCIONARIO, pela única chave
    disponível hoje: nome da empresa + nome do colaborador, normalizados. Ver
    references/casamento-empresa-funcionario.md para a lógica completa e o porquê de cada decisão.

    Nunca decide sozinho um caso ambíguo (mais de um candidato) — devolve os candidatos para uma
    pessoa escolher.

.ENTRADA
    $Empresa, $Funcionario — arrays de objetos, como devolvidos por Get-PlanilhaAdmissao
    (Ler-PlanilhaAdmissao.ps1).

.SAÍDA
    Hashtable:
      Casados         -> @(@{ Empresa = <obj>; Funcionario = <obj> })
      SemParFuncionario -> @(<obj da EMPRESA sem correspondente>)
      SemParEmpresa     -> @(<obj da FUNCIONARIO sem correspondente>)
      Ambiguos          -> @(@{ Empresa = <obj>; Candidatos = @(<obj da FUNCIONARIO>) })

.USO
    . .\Ler-PlanilhaAdmissao.ps1
    . .\Casar-Admissoes.ps1
    $dados = Get-PlanilhaAdmissao -CaminhoArquivo "..."
    $casamento = Get-AdmissoesCasadas -Empresa $dados.Empresa -Funcionario $dados.Funcionario
#>

# Nomes exatos das colunas-chave, conforme references/estrutura-planilha.md.
# Se o formulário mudar o texto da pergunta, ajuste aqui — não na lógica de casamento abaixo.
$script:CampoNomeFuncionarioNaEmpresa = "NOME COMPLETO DO FUNCIONÁRIO:"
$script:CampoNomeEmpresaNaEmpresa = "EMPRESA: (RAZÃO SOCIAL)"
$script:CampoNomeFuncionarioNoFuncionario = "NOME COMPLETO:"
$script:CampoNomeEmpresaNoFuncionario = "NOME DA EMPRESA: (RAZAO SOCIAL)"

function Get-NomeNormalizado {
    param([string]$Texto)
    if (-not $Texto) { return "" }
    $t = $Texto.Trim()
    $t = $t -replace '\s+', ' '
    return $t.ToUpperInvariant()
}

function Get-AdmissoesCasadas {
    param(
        [Parameter(Mandatory = $true)][array]$Empresa,
        [Parameter(Mandatory = $true)][array]$Funcionario
    )

    foreach ($f in $Funcionario) {
        $f | Add-Member -NotePropertyName _ChaveFuncionario -NotePropertyValue (Get-NomeNormalizado $f.$script:CampoNomeFuncionarioNoFuncionario) -Force
        $f | Add-Member -NotePropertyName _ChaveEmpresa -NotePropertyValue (Get-NomeNormalizado $f.$script:CampoNomeEmpresaNoFuncionario) -Force
        $f | Add-Member -NotePropertyName _Usado -NotePropertyValue $false -Force
    }

    $casados = @()
    $semParFuncionario = @()
    $ambiguos = @()

    foreach ($e in $Empresa) {
        $chaveFuncionario = Get-NomeNormalizado $e.$script:CampoNomeFuncionarioNaEmpresa
        $chaveEmpresa = Get-NomeNormalizado $e.$script:CampoNomeEmpresaNaEmpresa

        $candidatos = @($Funcionario | Where-Object {
            $_._ChaveFuncionario -eq $chaveFuncionario -and $_._ChaveEmpresa -eq $chaveEmpresa
        })

        if ($candidatos.Count -eq 1) {
            $candidatos[0]._Usado = $true
            $casados += @{ Empresa = $e; Funcionario = $candidatos[0] }
        }
        elseif ($candidatos.Count -eq 0) {
            $semParFuncionario += $e
        }
        else {
            $ambiguos += @{ Empresa = $e; Candidatos = @($candidatos) }
        }
    }

    $semParEmpresa = $Funcionario | Where-Object { -not $_._Usado }

    return @{
        Casados           = $casados
        SemParFuncionario = $semParFuncionario
        SemParEmpresa     = $semParEmpresa
        Ambiguos          = $ambiguos
    }
}
