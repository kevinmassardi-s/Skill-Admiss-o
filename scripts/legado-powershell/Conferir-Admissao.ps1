<#
.SINOPSE
    Aplica o checklist de references/regras-conferencia.md a uma admissão já casada (par
    Empresa/Funcionario) e devolve pendências + um resumo pronto para digitar no Domínio.

    Não calcula horas semanais a partir do horário de trabalho (é texto livre — ver o princípio em
    SKILL.md) e não trata cargo sem CBO ou ASO como pendência (confirmado fora de escopo).

.ENTRADA
    Um par @{ Empresa = <obj>; Funcionario = <obj> }, como vem em .Casados de Get-AdmissoesCasadas.

.SAÍDA
    PSCustomObject:
      NomeColaborador, NomeEmpresa
      Pendencias   -> @(string)   # vazio = nada pendente
      Resumo       -> string multilinha, pronto para copiar campo a campo no Domínio

.USO
    . .\Conferir-Admissao.ps1
    $resultado = Confirmar-Admissao -Par $casamento.Casados[0]
#>

# Nomes exatos das colunas, conforme references/estrutura-planilha.md — ajuste aqui se o formulário
# mudar o texto da pergunta.
$script:ColEmpresaCargo = "CARGO:"
$script:ColEmpresaDataAdmissao = "DATA DE ADMISSÃO:"
$script:ColEmpresaSalario = "SALÁRIO DO FUNCIONÁRIO:"
$script:ColEmpresaHorario = "HORÁRIO DE TRABALHO:"
$script:ColEmpresaPausa = "PAUSA REFEIÇÃO"
$script:ColEmpresaEscala = "ESCALA:"
$script:ColEmpresaContrato = "CONTRATO:"
$script:ColEmpresaVT = "DESCONTO DE 6% DE VALE TRANSPORTE?"
$script:ColEmpresaAdiantamento = "O colaborador terá adiantamento salarial (vale) a partir do mês da admissão independente de ter 15 dias trabalhados?"
$script:ColEmpresaCompensacao = "Acordo de compensação de horas"
$script:ColEmpresaProrrogacao = "Acordo de prorrogação de horas"

$script:ColFuncCPF = "CPF:"
$script:ColFuncPIS = "PIS:"
$script:ColFuncRG = "RG:"

# Confirmado por Kevin (2026-08-11): só dois documentos são realmente obrigatórios — ver
# references/regras-conferencia.md. "Documento oficial com foto" é satisfeito por QUALQUER UM destes
# dois campos (não precisam ser os dois):
$script:ColDocRG = "RG - FRENTE E VERSO:"
$script:ColDocCNH = "CNH (CASO POSSUA):"
# Sempre obrigatório:
$script:ColDocComprovanteEndereco = "COMPROVANTE DE ENDEREÇO COM CEP E BAIRRO:"

# Documentos que aparecem no resumo (pra Kevin ver o link), mas NUNCA viram pendência se faltarem.
$script:DocumentosInformativos = @(
    "TÍTULO DE ELEITOR:",
    "FOTO 3X4",
    "DISPENSA MILITAR:",
    "CERTIDÃO DE CASAMENTO (SE TIVER):"
)

$script:ColCertidaoDependente = "CERTIDÃO DE NASCIMENTO (FILHOS MENORES DE 14 ANOS):"
$script:ColCpfDependente = "CPF (FILHOS MENORES DE 14 ANOS):"

function Resolve-DocumentoPessoal {
    <# CPF/PIS às vezes chegam do Excel em notação científica (ex.: 4.6780914835E10) porque a célula
       foi digitada/lida como número, não como texto. Testado com um caso real (RG físico do
       colaborador, 2026-08-11): os dígitos por baixo da notação científica bateram exatamente com o
       CPF real. Isso é seguro de reconstruir automaticamente PORQUE CPF/PIS têm 11 dígitos — um double
       representa qualquer inteiro de até 15-16 dígitos sem perda, então reconstruir um número de 11
       dígitos nunca arredonda errado. Não é "inventar dado": é desfazer uma formatação que o Excel
       aplicou, não adivinhar um dígito que não existe.

       Se a reconstrução não der exatamente 11 dígitos, não é mais um problema de formatação — é um
       dado genuinamente errado, e isso continua sendo pendência de verdade. #>
    param([string]$Valor)

    if ([string]::IsNullOrWhiteSpace($Valor)) {
        return [pscustomobject]@{ Valor = ""; Reconstruido = $false; Valido = $false }
    }

    if ($Valor -match '[eE][+-]?[0-9]+') {
        $numero = [double]::Parse($Valor, [System.Globalization.CultureInfo]::InvariantCulture)
        $digitosReconstruidos = $numero.ToString("F0", [System.Globalization.CultureInfo]::InvariantCulture)
        if ($digitosReconstruidos.Length -eq 11) {
            return [pscustomobject]@{ Valor = $digitosReconstruidos; Reconstruido = $true; Valido = $true }
        }
        return [pscustomobject]@{ Valor = $Valor; Reconstruido = $true; Valido = $false }
    }

    $digitos = ($Valor -replace '[^0-9]', '')
    return [pscustomobject]@{ Valor = $Valor; Reconstruido = $false; Valido = ($digitos.Length -eq 11) }
}

function Confirmar-Admissao {
    param([Parameter(Mandatory = $true)][hashtable]$Par)

    $e = $Par.Empresa
    $f = $Par.Funcionario
    $pendencias = @()

    # --- Documentos: só dois são obrigatórios ---
    $temRG = -not [string]::IsNullOrWhiteSpace($f.$script:ColDocRG)
    $temCNH = -not [string]::IsNullOrWhiteSpace($f.$script:ColDocCNH)
    if (-not $temRG -and -not $temCNH) {
        $pendencias += "Documento oficial com foto faltando (nem RG frente/verso, nem CNH)"
    }
    if ([string]::IsNullOrWhiteSpace($f.$script:ColDocComprovanteEndereco)) {
        $pendencias += "Documento faltando: $script:ColDocComprovanteEndereco"
    }

    # --- Dependente: precisa de prova do CPF, não só a certidão ---
    $temCertidaoDependente = -not [string]::IsNullOrWhiteSpace($f.$script:ColCertidaoDependente)
    if ($temCertidaoDependente) {
        $temCpfDependenteAnexado = -not [string]::IsNullOrWhiteSpace($f.$script:ColCpfDependente)
        if (-not $temCpfDependenteAnexado) {
            # Pode ser que o CPF já esteja visível na própria certidão, ou em outro documento com foto
            # que Kevin já tenha — isso só dá pra confirmar olhando o documento. Não é "faltando" cego.
            $pendencias += "Confirmar CPF do dependente: certidão de nascimento anexada, mas a coluna de CPF do filho está vazia — checar se o CPF já aparece na própria certidão ou em outro documento com foto antes de pedir de novo"
        }
    }

    # --- CPF / PIS do colaborador ---
    $cpfResolvido = Resolve-DocumentoPessoal $f.$script:ColFuncCPF
    if ([string]::IsNullOrWhiteSpace($f.$script:ColFuncCPF)) {
        $pendencias += "CPF do colaborador faltando"
    }
    elseif (-not $cpfResolvido.Valido) {
        $pendencias += "CPF do colaborador com dígitos inválidos, não é só formatação (conferir na planilha): '$($f.$script:ColFuncCPF)'"
    }
    # PIS não é mais obrigatório (Kevin, 2026-08-11): desde o Decreto 9.723/2019 o CPF substituiu o
    # PIS como identificador — ver references/base-legal.md. Se vier preenchido, ótimo, e ainda vale
    # checar o formato; se estiver vazio, não é pendência.
    $pisResolvido = Resolve-DocumentoPessoal $f.$script:ColFuncPIS
    if (-not [string]::IsNullOrWhiteSpace($f.$script:ColFuncPIS) -and -not $pisResolvido.Valido) {
        $pendencias += "PIS do colaborador com dígitos inválidos, não é só formatação (conferir na planilha): '$($f.$script:ColFuncPIS)'"
    }

    $nomeColaborador = $f."NOME COMPLETO:"
    $nomeEmpresa = $e."EMPRESA: (RAZÃO SOCIAL)"

    $resumoLinhas = @(
        "=== $nomeColaborador — $nomeEmpresa ===",
        "Cargo: $($e.$script:ColEmpresaCargo)",
        "Data de admissão: $($e.$script:ColEmpresaDataAdmissao)",
        "Salário: $($e.$script:ColEmpresaSalario)",
        "Contrato: $($e.$script:ColEmpresaContrato)",
        "Horário de trabalho (CONFERIR 220h/semana à mão): $($e.$script:ColEmpresaHorario)",
        "Pausa refeição: $($e.$script:ColEmpresaPausa)",
        "Escala: $($e.$script:ColEmpresaEscala)",
        "VT (desconto 6%): $($e.$script:ColEmpresaVT)",
        "Adiantamento salarial: $($e.$script:ColEmpresaAdiantamento)",
        "Acordo de compensação de horas: $($e.$script:ColEmpresaCompensacao)",
        "Acordo de prorrogação de horas: $($e.$script:ColEmpresaProrrogacao)",
        "",
        "RG: $($f.$script:ColFuncRG)   CPF: $($cpfResolvido.Valor)$(if ($cpfResolvido.Reconstruido -and $cpfResolvido.Valido) { ' (reconstruído da notação científica — confira)' })   PIS: $($pisResolvido.Valor)$(if ($pisResolvido.Reconstruido -and $pisResolvido.Valido) { ' (reconstruído da notação científica — confira)' })",
        "Tem dependente: $(if ($temCertidaoDependente) { 'SIM' } else { 'NÃO' })",
        "",
        "Documentos:"
    )
    foreach ($nomeDoc in @($script:ColDocRG, $script:ColDocCNH, $script:ColDocComprovanteEndereco) + $script:DocumentosInformativos) {
        $link = $f.$nomeDoc
        $marca = if ([string]::IsNullOrWhiteSpace($link)) { "(faltando)" } else { $link }
        $resumoLinhas += "  - $nomeDoc $marca"
    }
    if ($temCertidaoDependente) {
        $resumoLinhas += "  - $script:ColCertidaoDependente $($f.$script:ColCertidaoDependente)"
        $resumoLinhas += "  - $script:ColCpfDependente $($f.$script:ColCpfDependente)"
    }

    return [pscustomobject]@{
        NomeColaborador = $nomeColaborador
        NomeEmpresa     = $nomeEmpresa
        Pendencias      = $pendencias
        Resumo          = ($resumoLinhas -join "`n")
        CpfValido       = if ($cpfResolvido.Valido) { $cpfResolvido.Valor } else { $null }
    }
}
