# Base legal e do sistema — pesquisa de 2026-08-11

Pesquisa feita para validar as regras de `regras-conferencia.md` contra fontes públicas: documentação
oficial do Sistema Domínio, leiaute do eSocial (evento S-2200) e normas da Receita Federal. Cada
afirmação abaixo tem fonte — se alguma regra deste arquivo divergir de uma fonte mais nova, atualize
aqui com a data.

## Correção de premissa

**O Sistema Domínio é da Thomson Reuters, não da TOTVS** — a Thomson Reuters adquiriu a Domínio
Sistemas em 2019. Portal de suporte oficial: `suporte.dominioatendimento.com`.

## CPF de dependente — a regra central deste checklist

**Confirmado, com fonte legal específica.** O CPF do dependente é obrigatório para **todas as idades,
sem piso etário**, sempre que o dependente for declarado para fins de IRRF (`depIRRF = S`) ou como
beneficiário de plano de saúde. Base legal: **Instrução Normativa RFB nº 1.871, de 22/02/2019**, que
eliminou a escala progressiva de idade que a Receita Federal vinha usando antes (14 → 12 → 8 anos,
entre ~2015 e 2017). Desde 2019, vale para qualquer idade, inclusive recém-nascido.

O erro operacional que os sistemas de folha mostram (código **294** no Domínio/Alterdata/Questor:
"o preenchimento do campo CPF dos dependentes é obrigatório") é o reflexo direto dessa norma.

**Achado operacional relevante:** o Domínio **deixa salvar o cadastro sem o CPF do dependente** — o
erro só aparece na hora de **validar/enviar o evento ao eSocial**, não no momento de gravar. Isso é
exatamente o motivo pelo qual a conferência antes de lançar (o que esta skill faz) tem valor: sem ela,
o problema só aparece depois, mais caro de corrigir.

Fontes: IN RFB 1.871/2019 (via [Seteco](https://www.seteco.com.br/irpf-obrigatoriedade-de-cpf-para-dependentes/)),
[erro 294 — Alterdata](https://ajuda.alterdata.com.br/dpbase/esocial-erro-no-evento-s-2200-294-o-preenchimento-do-campo-cpf-dos-dependentes-e-obrigatorio-63584230.html),
[erro 294 — Questor](https://docs.questor.com.br/pt-br/Produtos/Gest%C3%A3oCont%C3%A1bil/FolhadePagamento/eSocial/Inconsist%C3%AAncias_Operacionais_e_Solu%C3%A7%C3%B5es/s-2200-(cpf-dependente)),
[Domínio — código 4976](https://suporte.dominioatendimento.com/central/faces/solucao.html?codigo=4976).

## PIS — confirmado como não obrigatório (decisão de Kevin, 2026-08-11)

Duas pesquisas independentes encontraram indícios de que, desde o **Decreto 9.723/2019**, o **CPF
substituiu o PIS/NIS** como identificador — o eSocial usa o CPF, e o campo PIS no Domínio é tratado
como **opcional**. O leiaute atual do S-2200 não lista mais PIS/PASEP como campo do trabalhador (só
CPF). Fontes:
[Domínio — código 160](https://suporte.dominioatendimento.com/central/faces/solucao.html?codigo=160),
[Domínio — código 6617 (CTPS derivada do CPF, mesma lógica)](https://suporte.dominioatendimento.com/central/faces/solucao.html?codigo=6617).

**Decisão do Kevin:** tirar PIS da lista de pendências. Se vier preenchido, melhor ainda (e a skill
ainda confere o formato) — se faltar, não trava nada. Já aplicado em `scripts/conferir_admissao.py`.

## CTPS — não é mais um campo separado

Confirmado (Domínio, [código 6617](https://suporte.dominioatendimento.com/central/faces/solucao.html?codigo=6617)):
pela Portaria 1.065/2019, os campos de Número e Série da CTPS são preenchidos **a partir do próprio
CPF** (7 primeiros dígitos = número, 4 últimos = série) quando não há carteira física. Isso explica por
que o formulário de admissão não coleta CTPS separadamente — não é uma omissão, é o padrão atual.

## Documento com foto (RG/CNH) e comprovante de endereço

O leiaute do eSocial **não exige anexo de documento**, só os dados — RG, CNH, CTPS física e comprovante
de endereço são prática do escritório de contabilidade para conferir os dados, não exigência do sistema
em si. Isso **não invalida** a regra que Kevin definiu (documento com foto + comprovante de endereço
obrigatórios) — é uma política do escritório, legítima por si só, só não decorre diretamente do eSocial.

Fonte: leiaute S-2200 ([Senior](https://documentacao.senior.com.br/gestao-de-pessoas-hcm/esocial/leiautes/nao-periodicos/s-2200.htm)),
[MOS — Manual de Orientação do eSocial, versão S-1.3 (07/2026)](https://www.gov.br/esocial/pt-br/documentacao-tecnica/manuais/mos-s-1-3-consolidada-ate-a-no-s-1-3-07-2026.pdf).

## Campos que o Domínio valida — resolvidos com Kevin (2026-08-11)

- **RG com órgão emissor**: não precisa de checagem separada. Kevin confirmou que o órgão emissor já
  aparece na própria foto do documento (RG ou CNH) — é dado que ele lê visualmente ao conferir o
  documento, não algo que falta na planilha.
- **Comprovante de endereço**: a finalidade prática é extrair **CEP, número e complemento** do
  endereço — não é uma exigência de anexo do eSocial (que só valida o dado "município" em si), é o
  método do escritório para chegar nesses dados. A regra de exigir esse documento continua válida por
  esse motivo, mesmo sem ser uma exigência direta do leiaute.
- **Município** (naturalidade e endereço) segue sem um campo de texto dedicado no formulário — não
  veio à tona como problema prático, então não é uma pendência aberta, só uma observação que fica
  registrada aqui caso o Domínio comece a recusar validação por causa disso no futuro.

Fonte: [Domínio — Como completar cadastro de Colaborador? (código 9954)](https://suporte.dominioatendimento.com/central/faces/solucao.html?codigo=9954),
[Domínio — Erro 1, campo obrigatório Município (código 4623)](https://suporte.dominioatendimento.com/central/faces/solucao.html?codigo=4623).
