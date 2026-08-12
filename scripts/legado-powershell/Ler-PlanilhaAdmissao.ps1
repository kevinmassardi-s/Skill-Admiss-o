<#
.SINOPSE
    Lê as abas EMPRESA e FUNCIONARIO de um arquivo .xlsx de admissão e devolve as linhas como
    objetos PowerShell, com o cabeçalho localizado automaticamente pela coluna "Carimbo de data/hora"
    (âncora que o Google Forms sempre gera, mesmo que a linha do cabeçalho mude — ver
    references/estrutura-planilha.md).

    Não depende de Excel, ImportExcel nem Python — só .NET (System.IO.Compression), que já vem com o
    Windows. Lê o .xlsx como o zip que ele é, por baixo do formato.

.ENTRADA
    Caminho de um arquivo .xlsx no formato do FORMULÁRIO DE ADMISSÃO (abas EMPRESA e FUNCIONARIO).

.SAÍDA
    Hashtable: @{ Empresa = @(<PSCustomObject por linha>); Funcionario = @(<PSCustomObject por linha>) }
    Cada objeto tem uma propriedade por coluna, nomeada com o texto do cabeçalho (sem alterações) e
    também uma propriedade "_Linha" com o número da linha na planilha original (para o Kevin conseguir
    achar a linha exata se precisar checar na mão).

.USO
    . .\Ler-PlanilhaAdmissao.ps1
    $dados = Get-PlanilhaAdmissao -CaminhoArquivo "C:\...\FORMULÁRIO DE ADMISSÃO - EXTERNO.xlsx"
    $dados.Empresa.Count
    $dados.Funcionario | Select-Object -First 1
#>

Add-Type -AssemblyName System.IO.Compression.FileSystem

function Get-XlsxXml {
    param([System.IO.Compression.ZipArchive]$Zip, [string]$EntryName)
    $entry = $Zip.GetEntry($EntryName)
    if (-not $entry) { return $null }
    $stream = $entry.Open()
    $reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::UTF8)
    $content = $reader.ReadToEnd()
    $reader.Close()
    $stream.Close()
    [xml]$xml = $content
    return $xml
}

function Get-SharedStrings {
    param([System.IO.Compression.ZipArchive]$Zip)
    $xml = Get-XlsxXml -Zip $Zip -EntryName "xl/sharedStrings.xml"
    if (-not $xml) { return @() }
    $strings = @()
    foreach ($si in $xml.sst.si) {
        $strings += [string]$si.InnerText
    }
    return $strings
}

function Get-SheetFileMap {
    <# Mapeia nome da aba (ex.: "EMPRESA") -> arquivo interno (ex.: "sheet1.xml"), passando pelo
       relacionamento r:id, em vez de assumir que a ordem das abas bate com a numeração dos arquivos. #>
    param([System.IO.Compression.ZipArchive]$Zip)
    $wb = Get-XlsxXml -Zip $Zip -EntryName "xl/workbook.xml"
    $rels = Get-XlsxXml -Zip $Zip -EntryName "xl/_rels/workbook.xml.rels"

    $ridParaArquivo = @{}
    foreach ($rel in $rels.Relationships.Relationship) {
        $ridParaArquivo[$rel.Id] = $rel.Target -replace '^/?xl/', ''
    }

    $nsMgr = New-Object System.Xml.XmlNamespaceManager($wb.NameTable)
    $nsMgr.AddNamespace("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")

    $mapa = @{}
    foreach ($sheet in $wb.workbook.sheets.sheet) {
        $rid = $sheet.GetAttribute("id", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")
        $arquivo = $ridParaArquivo[$rid]
        if ($arquivo -and -not $arquivo.StartsWith("worksheets/")) { $arquivo = "worksheets/$arquivo" }
        $mapa[$sheet.name] = $arquivo
    }
    return $mapa
}

function Get-ColunaDaCelula {
    param([string]$RefCelula)
    return ($RefCelula -replace '[0-9]', '')
}

function Get-ValorCelula {
    param($Celula, [string[]]$SharedStrings)
    if (-not $Celula) { return "" }
    $tipo = $Celula.t
    if ($tipo -eq 's') {
        $idx = [int]$Celula.v
        if ($idx -ge 0 -and $idx -lt $SharedStrings.Count) { return $SharedStrings[$idx] }
        return ""
    }
    if ($tipo -eq 'inlineStr') {
        if ($Celula.is) { return [string]$Celula.is.InnerText }
        return ""
    }
    if ($tipo -eq 'str') {
        return [string]$Celula.v
    }
    if ($Celula.v -ne $null) { return [string]$Celula.v }
    return ""
}

function Get-LinhasDaAba {
    <# Lê uma aba inteira, localiza o cabeçalho pela âncora "Carimbo de data/hora" nas primeiras
       linhas, e devolve as linhas de dados como objetos nomeados pelo texto do cabeçalho. #>
    param(
        [System.IO.Compression.ZipArchive]$Zip,
        [string]$ArquivoDaAba,
        [string[]]$SharedStrings,
        [string]$AncoraCabecalho = "Carimbo de data/hora",
        [int]$MaxLinhasParaProcurarCabecalho = 5,
        [int]$SomenteUltimasNLinhas = 0
    )

    $sheetXml = Get-XlsxXml -Zip $Zip -EntryName "xl/$ArquivoDaAba"
    if (-not $sheetXml) {
        throw "Não encontrei $ArquivoDaAba dentro do arquivo. A planilha pode ter mudado de estrutura — confira à mão."
    }
    $todasLinhas = @($sheetXml.worksheet.sheetData.row)

    $linhaCabecalho = $null
    $numeroLinhaCabecalho = 0
    foreach ($linha in ($todasLinhas | Select-Object -First $MaxLinhasParaProcurarCabecalho)) {
        foreach ($celula in $linha.c) {
            $valor = Get-ValorCelula -Celula $celula -SharedStrings $SharedStrings
            if ($valor -like "*$AncoraCabecalho*") {
                $linhaCabecalho = $linha
                $numeroLinhaCabecalho = [int]$linha.r
                break
            }
        }
        if ($linhaCabecalho) { break }
    }

    if (-not $linhaCabecalho) {
        throw "Não achei a coluna '$AncoraCabecalho' nas primeiras $MaxLinhasParaProcurarCabecalho linhas de $ArquivoDaAba. O formulário pode ter mudado — confira manualmente antes de seguir."
    }

    $colunaParaNome = @{}
    foreach ($celula in $linhaCabecalho.c) {
        $nome = Get-ValorCelula -Celula $celula -SharedStrings $SharedStrings
        if ($nome -ne "") {
            $colunaParaNome[(Get-ColunaDaCelula $celula.r)] = $nome
        }
    }

    $linhasDeDados = @($todasLinhas | Where-Object { [int]$_.r -gt $numeroLinhaCabecalho })

    # Otimização de performance: o Google Forms sempre acrescenta linha nova no fim da aba — nunca
    # insere no meio nem reordena. Então "as últimas N linhas com conteúdo" cobre com folga qualquer
    # corte por data recente, sem precisar montar objeto pra milhares de linhas antigas que vão ser
    # descartadas de qualquer forma pelo filtro de data no orquestrador.
    #
    # Armadilha real encontrada (2026-08-11), duas rodadas:
    # 1) Pegar literalmente "as últimas N linhas por número" dava ZERO resultado — a planilha exportada
    #    tem milhares de linhas em branco "de enchimento" no final (comum em export do Google Sheets).
    # 2) Filtrar só por "tem célula (`<c>`) presente" também não resolveu — essas linhas de enchimento
    #    TÊM `<c>` pra todas as colunas, só que cada uma sem `v` (valor) nenhum dentro. Confirmado
    #    inspecionando o XML bruto: linha vazia tem 29 células, todas com `v` vazio.
    # A correção que funciona: exigir que pelo menos uma célula tenha `v` **não vazio** — essa é a
    # checagem barata de verdade (não decodifica string compartilhada, só olha se existe algo ali).
    if ($SomenteUltimasNLinhas -gt 0) {
        $linhasComValor = @($linhasDeDados | Where-Object {
            $temValor = $false
            foreach ($c in $_.c) { if (-not [string]::IsNullOrEmpty($c.v)) { $temValor = $true; break } }
            $temValor
        })
        if ($linhasComValor.Count -gt $SomenteUltimasNLinhas) {
            $linhasDeDados = @($linhasComValor | Select-Object -Last $SomenteUltimasNLinhas)
        }
        else {
            $linhasDeDados = $linhasComValor
        }
    }

    # Lista .NET em vez de @() += : em PowerShell, += num array recria o array inteiro a cada linha
    # (custo O(n²)) — com milhares de linhas isso domina o tempo de execução sozinho.
    $resultado = [System.Collections.Generic.List[object]]::new()
    foreach ($linha in $linhasDeDados) {
        $obj = [ordered]@{ _Linha = [int]$linha.r }
        $temAlgumValor = $false
        foreach ($celula in $linha.c) {
            $coluna = Get-ColunaDaCelula $celula.r
            $nomeCampo = $colunaParaNome[$coluna]
            if (-not $nomeCampo) { continue }
            $valor = Get-ValorCelula -Celula $celula -SharedStrings $SharedStrings
            if ($valor -ne "") { $temAlgumValor = $true }
            $obj[$nomeCampo] = $valor
        }
        if ($temAlgumValor) { [void]$resultado.Add([pscustomobject]$obj) }
    }
    return $resultado
}

function Get-PlanilhaAdmissao {
    param(
        [Parameter(Mandatory = $true)][string]$CaminhoArquivo,
        # Padrão generoso: a ~50 admissões/mês, 600 linhas cobrem quase um ano de margem além de
        # qualquer corte de data recente. Só existe pra não reprocessar milhares de linhas antigas que
        # o filtro de data ia descartar de qualquer jeito. Passe 0 pra ler a planilha inteira (ex.:
        # numa auditoria do backlog antigo).
        [int]$SomenteUltimasNLinhas = 600
    )

    if (-not (Test-Path $CaminhoArquivo)) {
        throw "Arquivo não encontrado: $CaminhoArquivo"
    }

    $zip = [System.IO.Compression.ZipFile]::OpenRead($CaminhoArquivo)
    try {
        $sharedStrings = Get-SharedStrings -Zip $zip
        $mapaAbas = Get-SheetFileMap -Zip $zip

        foreach ($abaEsperada in @("EMPRESA", "FUNCIONARIO")) {
            if (-not $mapaAbas.ContainsKey($abaEsperada)) {
                throw "A aba '$abaEsperada' não existe neste arquivo. Abas encontradas: $($mapaAbas.Keys -join ', ')"
            }
        }

        $empresa = Get-LinhasDaAba -Zip $zip -ArquivoDaAba $mapaAbas["EMPRESA"] -SharedStrings $sharedStrings -SomenteUltimasNLinhas $SomenteUltimasNLinhas
        $funcionario = Get-LinhasDaAba -Zip $zip -ArquivoDaAba $mapaAbas["FUNCIONARIO"] -SharedStrings $sharedStrings -SomenteUltimasNLinhas $SomenteUltimasNLinhas

        return @{ Empresa = $empresa; Funcionario = $funcionario }
    }
    finally {
        $zip.Dispose()
    }
}
