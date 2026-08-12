# Instalar esta skill numa máquina nova

Passo a passo pra deixar a skill `admissao-clt` funcionando em outro computador.

## 1. Baixar os arquivos

Dentro da pasta de skills do Claude Code (`C:\Users\<seu-usuário>\.claude\skills\`), rode:

```bash
git clone https://github.com/kevinmassardi-s/Skill-Admiss-o.git admissao-clt
```

Sem git instalado, dá pra baixar o ZIP direto do GitHub (botão "Code" → "Download ZIP") e extrair
numa pasta chamada `admissao-clt` dentro de `.claude\skills\`.

**Confira o nome da pasta.** Tem que ser exatamente `admissao-clt` — é por esse nome que o Claude Code
encontra a skill.

## 2. Instalar Python e as bibliotecas

Os scripts em `scripts/*.py` precisam de Python 3.12+ e da biblioteca `openpyxl`. Num PowerShell:

```powershell
winget install --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
```

Depois de instalar (pode precisar abrir um PowerShell novo pra reconhecer o comando):

```powershell
python -m pip install --upgrade pip openpyxl
```

## 3. Logar na conta do Google no Chrome dessa máquina

A planilha vive no Google Sheets, na conta corporativa `kevin.massardi@rtcountdigital.com.br` (pasta
"ADMISSÃO GERAL"). O Claude usa o Chrome de verdade da máquina pra baixar a versão atual — então essa
conta precisa estar logada no Chrome do PC novo (Menu do Google → Adicionar conta, se ainda não tiver).

Isso **não** vem com o repositório — é uma sessão de navegador local, específica de cada máquina.

## 4. Testar

Peça pro Claude "confere as admissões pendentes" (ou invoque a skill diretamente: `/admissao-clt`).
Ele deve reconhecer a skill pelo `SKILL.md`, baixar a planilha atual (com sua confirmação) e rodar
`scripts/executar_conferencia.py`.

## Opcional: lembrete diário de manhã

Se quiser o mesmo lembrete automático que existe na máquina original (Claude abre sozinho ao ligar o
PC + pergunta se quer conferir admissões às 7h nos dias úteis), isso precisa ser configurado de novo
nessa máquina — não é algo que vem no repositório. Peça pro Claude configurar, ele sabe como (foi feito
uma vez, em 2026-08-12, com um atalho na pasta de Inicialização do Windows + uma tarefa agendada).
