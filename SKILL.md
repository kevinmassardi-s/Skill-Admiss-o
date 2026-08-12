---
name: admissao-clt
description: >
  Apoia o cadastro de admissão de colaborador CLT num departamento pessoal de contabilidade: lê a
  planilha de formulários (abas EMPRESA e FUNCIONARIO), casa a resposta da empresa com a do
  colaborador, confere as regras (documentos obrigatórios, CPF de dependente, VT, adiantamento,
  prorrogação/compensação de horas) e devolve um resumo pronto para digitar no Domínio e abrir o
  processo no Acessórias. Use sempre que aparecer "admissão", "admitir colaborador", "novo
  funcionário", "cadastro de admissão", "FORMULÁRIO DE ADMISSÃO", ficha de admissão, ou quando a
  pessoa mencionar casar a aba EMPRESA com a aba FUNCIONARIO, conferir documentos de admissão, ou
  preparar o cadastro para lançar no Domínio. Não cobre RPA/prestador de serviço (processo à parte,
  fora de escopo) nem o exame admissional (ASO).
---

# Cadastro de admissão (CLT)

## O que este processo entrega

Toda empresa cliente que contrata um colaborador CLT preenche dois formulários do Google — um a
própria empresa, outro o colaborador — que caem na mesma planilha, em abas separadas. Alguém do DP
precisa juntar as duas respostas da mesma pessoa, conferir se está tudo certo, cadastrar no Domínio,
gerar os documentos e abrir/concluir o processo no Acessórias.

Hoje isso é feito por uma pessoa só (Kevin), caçando informação em duas abas e seis links de
documento por admissão, cerca de 50 vezes por mês. O erro que este processo evita não é o cadastro em
si — isso continua manual, porque nem Domínio nem Acessórias têm importação. É evitar que a **conferência**
seja o gargalo: documento faltando ou CPF de dependente ausente só aparece hoje quando o eSocial já
rejeitou o evento.

## Os princípios que sustentam isto

**Nunca casar EMPRESA com FUNCIONARIO pelo nome sozinho, sem checar.** É o único critério disponível
hoje — não existe uma chave única entre os dois formulários — mas nome erra: maiúscula/minúscula
diferente, nome social vs. civil, homônimos entre clientes diferentes. Quando houver mais de um
candidato plausível, ou nenhum, a skill apresenta as opções e pergunta — nunca escolhe sozinha. Ver
`references/casamento-empresa-funcionario.md`.

**Não calcular o que exige leitura de texto livre.** O horário de trabalho vem como frase solta
("Segunda a quinta 08:00 às 18:00, sexta até 17:00") e precisa respeitar o teto de 220h semanais. Essa
conta continua com Kevin — tentar somar automaticamente a partir de texto livre arrisca inventar um
número errado com aparência de certo. A skill mostra o horário em destaque para conferência, não
calcula a soma.

**Documento faltando é pendência, não suposição.** Se um link de documento está vazio, a skill relata
"faltando" e diz qual. Nunca assume que "provavelmente foi enviado por fora" ou que não é necessário.

**Cargo sem CBO não é bloqueio.** Confirmado por Kevin — ao contrário do que pareceria natural, isso
não exige julgamento aqui. Não sinalizar isso como pendência.

**A planilha (Google Forms + Sheets) não muda.** A automação lê o que já existe; não propõe trocar de
sistema de captação nem editar as respostas na origem.

**ASO e RPA ficam fora.** O exame admissional (aba EMPRESA) e qualquer prestador via RPA (abas
`EMPRESA - RPA` / `PRESTADOR - RPA`) não fazem parte deste processo.

## O fluxo

Rodar tudo de uma vez (script de entrada):

```
python scripts/executar_conferencia.py --caminho "C:\...\FORMULÁRIO DE ADMISSÃO - EXTERNO.xlsx"
```

Precisa de Python com `openpyxl` instalado (`pip install openpyxl`) — já configurado nesta máquina em
2026-08-11. Reescrito em Python nessa data porque a primeira versão (PowerShell, arquivada em
`scripts/legado-powershell/`) levava ~60s no arquivo real; a versão Python leva ~2s.

1. **Ler a planilha.** `scripts/ler_planilha.py` lê as abas `EMPRESA` e `FUNCIONARIO` do arquivo
   `.xlsx` e devolve as linhas como listas de dicionários, incluindo o status de cada admissão (coluna
   de pendência/feito na aba EMPRESA — ver `references/estrutura-planilha.md` para os nomes exatos e
   como o cabeçalho é localizado).
2. **Casar as respostas da mesma pessoa.** `scripts/casar_admissoes.py` casa cada linha da
   `EMPRESA` com a linha correspondente da `FUNCIONARIO`, por nome normalizado. Ver
   `references/casamento-empresa-funcionario.md` para a lógica e para os casos ambíguos.
3. **Conferir cada admissão casada.** `scripts/conferir_admissao.py` aplica o checklist de
   `references/regras-conferencia.md` (documentos, dependente, CPF/PIS, VT, adiantamento,
   prorrogação/compensação) e monta o resumo pronto para digitar no Domínio.
4. **Cruzar CPF entre admissões do mesmo lote** (feito em `scripts/executar_conferencia.py`, depois
   de conferir cada uma isoladamente): duas pessoas diferentes com o mesmo CPF é sempre erro de dado —
   achado real em 2026-08-11, ver `references/regras-conferencia.md`.
5. **Devolver o relatório.** Três grupos, nunca misturados: prontas para lançar (com o resumo),
   pendentes (com o motivo exato), e ambíguas (com os candidatos, aguardando escolha de Kevin). O
   lançamento em si no Domínio e a abertura/conclusão do processo no Acessórias continuam manuais —
   ver `references/estrutura-planilha.md` sobre por que não há caminho programático até esses dois
   sistemas hoje.

## Onde buscar o resto

- **`references/estrutura-planilha.md`** — nomes exatos das abas e colunas, como o cabeçalho é
  localizado (a planilha já mudou de formato antes — aba `ANTIGA FUNCIONARIO` é a prova), e onde cada
  sistema de destino entra.
- **`references/casamento-empresa-funcionario.md`** — como normalizar nome/empresa, quando aceitar
  automaticamente e quando perguntar.
- **`references/regras-conferencia.md`** — o checklist completo de conferência, com o porquê de cada
  regra e os erros mais comuns hoje (documento faltando, CPF de dependente faltando, CPF do
  colaborador faltando).
- **`references/base-legal.md`** — pesquisa com fonte (Sistema Domínio, leiaute do eSocial S-2200,
  normas da Receita Federal) que valida essas regras. Leia antes de mudar o checklist de conferência,
  e antes de responder qualquer pergunta sobre "isso é exigência legal ou é prática do escritório?".

## Como conduzir a conversa

Kevin é quem faz o processo, não é da área técnica de sistemas — fale em "a linha da empresa" e "a
linha do funcionário", não em "a row do DataFrame". Ao entregar o relatório, separe claramente o que
está pronto do que está pendente: prometer "50 prontas" quando 8 têm documento faltando quebra a
confiança na próxima rodada. Se aparecer um caso que as regras aqui não cobrem, pare e pergunte antes
de decidir sozinho — é assim que uma regra nova entra neste arquivo.

**Sempre traga todos os dados do resumo de `scripts/executar_conferencia.py`, nunca parafraseie.**
Achado real (2026-08-12): descrever em texto corrido "os documentos X, Y e Z estão presentes" parece
equivalente, mas Kevin não consegue clicar em prosa. O mesmo vale pra todos os outros campos (cargo,
salário, horário, CPF/PIS): traga tudo que está no bloco `=== Nome — Empresa ===`, em vez de resumir o
que tem nele. Isso vale pra prontas, pendências e prováveis — qualquer admissão que o Kevin for
trabalhar precisa do conteúdo completo, não de um resumo do resumo.

**Os links de documento têm que ficar clicáveis, não só copiáveis.** Segundo achado real, mesmo dia:
colar o resumo dentro de um bloco de código (` ``` `) imprime o link como texto puro — dá pra copiar,
não dá pra clicar. Formate cada documento como link markdown de verdade:
`[RG - frente e verso](https://drive.google.com/open?id=...)`, um por linha, **fora** de bloco de
código. Só o valor do PIS/CPF reconstruído ou uma pendência pontual pode ficar em code-inline
(` `texto` `) — links de documento, nunca.
