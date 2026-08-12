# Estrutura da planilha de admissão

Baseado no arquivo de exemplo `FORMULÁRIO DE ADMISSÃO - EXTERNO.xlsx` (inspecionado em 2026-08-11).
Se o arquivo real divergir do que está aqui, **confie no arquivo, não neste documento** — e atualize
este arquivo depois.

## Onde a planilha vive de verdade

É um **Google Sheets nativo** (não um arquivo subido), na conta corporativa
`kevin.massardi@rtcountdigital.com.br`, pasta **ADMISSÃO GERAL**, dono Luis Telles.

- ID da planilha: `1ZjTF1cMjbQmvhx1_qV06EnASK_f8kOJnfMHDa-xI2FA`
- Link de edição: `https://docs.google.com/spreadsheets/d/1ZjTF1cMjbQmvhx1_qV06EnASK_f8kOJnfMHDa-xI2FA/edit`
- Link de exportação direta em `.xlsx` (baixa sempre a versão mais atual, sem precisar abrir e ir em
  Arquivo → Download): `https://docs.google.com/spreadsheets/d/1ZjTF1cMjbQmvhx1_qV06EnASK_f8kOJnfMHDa-xI2FA/export?format=xlsx`

**Não existe sincronização automática desse arquivo pro computador do Kevin hoje** — nem pelo Google
Drive para Desktop (a conta logada nele é diferente da corporativa que tem acesso a esta planilha),
nem por nenhum outro mecanismo. Toda vez que for conferir admissões, o caminho é: abrir o link de
exportação acima (pede login na conta `@rtcountdigital.com.br` se a sessão não estiver ativa) e baixar
o `.xlsx` gerado — baixar arquivo é uma ação que pede confirmação explícita do Kevin antes de cada vez,
não é para automatizar silenciosamente.

## Abas do workbook

| Aba | Uso |
|---|---|
| `EMPRESA` | **Relevante.** Formulário preenchido pelo cliente: dados contratuais. |
| `FUNCIONARIO` | **Relevante.** Formulário preenchido pelo colaborador: dados pessoais + documentos. |
| `EMPRESA - RPA` | Fora de escopo — fluxo de prestador de serviço (RPA), Kevin não realiza. |
| `PRESTADOR - RPA` | Fora de escopo — mesmo motivo. |
| `ANTIGA FUNCIONARIO` | Só histórico. Formato antigo do formulário, não recebe dado novo. |
| `LEGENDA` | Vocabulário de status (ver abaixo) e lista de nomes usada em dropdown. |
| `KAROL`, `ISABELA`, `LUANA`, `LETICIA` | Filas pessoais antigas, de quando o processo era dividido
  entre 4 pessoas. Todas saíram do processo (3 saíram da empresa, 1 não realiza mais). Não usar como
  fonte — são cópias, a fonte é sempre `EMPRESA`/`FUNCIONARIO`. |
| `FUNCIONARIO ond`, `RPA` | Não investigadas a fundo — não pareceram relevantes ao processo atual. Se
  surgir dúvida, perguntar a Kevin antes de assumir que são lixo ou que são fonte. |

## Como localizar o cabeçalho

**O cabeçalho não está sempre na mesma linha.** Na aba `EMPRESA` do arquivo de exemplo, a linha 1
está vazia (painel congelado com `ySplit=2`) e os nomes das colunas ficam na linha 2 — os dados
começam na linha 3. Na aba `FUNCIONARIO`, os nomes já estão na linha 1 e os dados começam na linha 2.

Isso não é acidente do arquivo de exemplo — é o tipo de coisa que muda quando alguém reorganiza a
planilha. **Não fixe o número da linha do cabeçalho no código.** A âncora confiável é a coluna
`Carimbo de data/hora`, que o Google Forms sempre gera automaticamente: procure, nas primeiras 5
linhas de cada aba, a linha que contém essa string, e trate essa linha como cabeçalho.

## Colunas da aba EMPRESA

| Coluna | Conteúdo |
|---|---|
| `RESP` | Responsável pela admissão (hoje sempre Kevin; coluna histórica). |
| `DOC PENDENTE` | **Coluna de status** — ver vocabulário abaixo. |
| `Carimbo de data/hora` | Timestamp da resposta do formulário — âncora do cabeçalho. |
| `EMPRESA: (RAZÃO SOCIAL)` | Nome da empresa cliente. |
| `NOME COMPLETO DO FUNCIONÁRIO:` | Nome do colaborador — chave para casar com a aba FUNCIONARIO. |
| `DATA DE ADMISSÃO:` | |
| `SALÁRIO DO FUNCIONÁRIO:` | |
| `CARGO:` | |
| `HORÁRIO DE TRABALHO:` | Texto livre — não tentar somar horas automaticamente (ver SKILL.md). |
| `PAUSA REFEIÇÃO` | |
| `ESCALA:` | |
| `CONTRATO:` | Tipo de contrato (ex.: PRAZO INDETERMINADO, experiência). |
| `ASO - EXAME MÉDICO ADMISSIONAL:` | **Fora de escopo.** Link do documento, mas o processo não trata disso. |
| `DESCONTO DE 6% DE VALE TRANSPORTE?` | Sinalizador de VT. |
| `Confirmação de Exame médico` | |
| `...adiantamento salarial (vale)...` | Sinalizador de adiantamento. |
| `Comentários adicionais:` | |
| `Acordo de compensação de horas` | Sinalizador — se presente, gerar termo de compensação. |
| `Acordo de prorrogação de horas` | Sinalizador — se presente, gerar termo de prorrogação. |
| `DESCRIÇÃO DA FUNÇÃO:` | |
| `Possui deficiência?` | |
| `OBSERVAÇÃO` | |

## Colunas da aba FUNCIONARIO

| Coluna | Conteúdo |
|---|---|
| `FEITO?` | Status nesta aba (pode divergir do status na EMPRESA — checar os dois). |
| `Carimbo de data/hora` | Âncora do cabeçalho. |
| `NOME DA EMPRESA: (RAZAO SOCIAL)` | Para casar com a aba EMPRESA. |
| `NOME COMPLETO:` | Nome do colaborador — chave para casar com a aba EMPRESA. |
| `E-MAIL:`, `CELULAR:`, `DATA DE NASCIMENTO:` | |
| `RG:`, `PIS:`, `CPF:` | **Atenção:** no arquivo de exemplo, esses campos às vezes chegam como
  número (notação científica, ex. `2.07837E+10`) em vez de texto, o que pode truncar ou distorcer
  dígitos. Ler sempre como texto/string, nunca deixar o Excel/PowerShell reinterpretar como número. |
| `ESTADO CIVIL:`, `SEXO:`, `ESCOLARIDADE:`, `RAÇA OU COR:` | |
| `VALE TRANSPORTE:` | |
| `RG - FRENTE E VERSO:` | Link de documento (Google Drive). |
| `TÍTULO DE ELEITOR:` | Link de documento. |
| `CNH (CASO POSSUA):` | Link de documento — **opcional**, ausência não é pendência. |
| `FOTO 3X4` | Link de documento. |
| `DISPENSA MILITAR:` | Link de documento — só se aplicável (depende de idade/sexo; não tratar
  ausência como pendência automática sem confirmar com Kevin). |
| `COMPROVANTE DE ENDEREÇO COM CEP E BAIRRO:` | Link de documento. |
| `CERTIDÃO DE NASCIMENTO (FILHOS MENORES DE 14 ANOS):` | Presença = colaborador tem dependente. |
| `CPF (FILHOS MENORES DE 14 ANOS):` | **Obrigatório se a certidão acima estiver presente** — regra
  central, ver `references/regras-conferencia.md`. |
| `CERTIDÃO DE CASAMENTO (SE TIVER):` | Opcional. |
| `Possui deficiência?` | |

## Regra fixa: limpar downloads antigos, sem apagar permanente

Confirmado por Kevin (2026-08-12): toda vez que uma versão nova da planilha for baixada, mandar as
versões anteriores pra **Lixeira do Windows** (reversível), nunca apagar permanente. Isso evita
acumular `FORMULÁRIO DE ADMISSÃO - EXTERNO.xlsx`, `(1).xlsx`, `(2).xlsx`... na pasta Downloads.

```powershell
Add-Type -AssemblyName Microsoft.VisualBasic
[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile($caminho, 'OnlyErrorDialogs', 'SendToRecycleBin')
```

Apagar permanente (sem passar pela Lixeira) nunca é feito de forma automática, mesmo com autorização —
é uma regra de segurança fixa, não específica desta skill.

## Regra fixa: nunca editar a planilha original do Drive

**Confirmado por Kevin (2026-08-11): a planilha original no Google Drive nunca é editada por esta
skill** — nem para limpar linha em branco, nem para "arrumar" formatação, nem por motivo de
performance. Qualquer teste ou otimização usa uma **cópia local baixada**, nunca o arquivo vivo. Isso
vale mesmo quando a edição pareceria inofensiva ou benéfica (ex.: apagar linhas de enchimento no fim de
uma aba) — a planilha é operada por outras pessoas em tempo real, e mexer nela por fora é risco
desnecessário. Testes de performance ou de estrutura sempre em arquivo `.xlsx` local, descartável.

## Sistemas de destino (fora da planilha)

- **Domínio** — sistema de folha de pagamento. Cadastro **manual**, sem importação/API confirmada.
  A skill prepara o resumo; não escreve no Domínio.
- **Acessórias** — sistema de gestão de obrigações/tarefas do DP. Abertura de solicitação, processo,
  anexo de relatórios e envio por e-mail são **manuais**, feitos pelo atalho do próprio sistema.
