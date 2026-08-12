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

## Jornada de trabalho por tipo de contrato — pesquisa de 2026-08-12

Pedido do Kevin: conferir automaticamente se a jornada está dentro de 44h semanais / 220h mensais,
sempre alertando quando não estiver. Antes de implementar, pesquisei (5 agentes em paralelo) se esse
limite vale igual pra todo tipo de contrato — não vale. Achado real na planilha: **221 admissões
"INTERMITENTE" e 84 "ESTÁGIO"** (mais casos de "aprendiz" dentro do contrato ESTÁGIO, identificáveis
só pelo texto do cargo) — todas seriam julgadas erradas pelo limite padrão.

**220h/mês não é um teto legal independente.** É o divisor de folha (CLT art. 64: salário-hora =
salário ÷ 220), derivado de 44h/semana × 5. O limite legal de verdade é o semanal (44h, CF art. 7º,
XIII) e o diário (8h, CLT art. 58, até 10h com compensação — banco de horas até 6 meses por acordo
individual, até 1 ano por acordo/convenção coletiva, CLT art. 59 e 59-A). Continuamos comparando
contra 220h/mês porque foi pedido e é referência útil, mas registrando aqui que não é a fonte legal
primária.
Fontes: CF art. 7º XIII; CLT art. 58, 59, 59-A, 64;
[AMATRA4 — o divisor 220](https://www.amatra4.org.br/artigos-2/artigos/o-divisor-220-e-o-limite-mensal-de-horas-trabalhadas/);
[Conjur — prorrogação, compensação e banco de horas](https://conjur.com.br/2024-fev-08/jornada-de-trabalho-prorrogacao-compensacao-e-banco-de-horas/).

**Estágio (Lei 11.788/2008, art. 10): 30h semanais** (ensino superior, técnico ou médio regular) ou
**20h semanais** (educação especial / EJA fundamental) — nunca 44h. Hora extra e banco de horas são
**proibidos em qualquer hipótese**; extrapolar o limite descaracteriza o estágio em vínculo
empregatício. A skill usa 30h/150h como padrão (não dá pra distinguir a modalidade de 20h pelos campos
do formulário — limitação conhecida, registrada aqui).
Fonte: [Lei 11.788/2008, art. 10](https://www.jusbrasil.com.br/legislacao/93117/lei-do-estagio-lei-11788-08).

**Menor aprendiz (Lei 10.097/2000): 6h diárias**, ou até 8h se já concluiu o ensino fundamental
(exceção não detectável pelos campos do formulário — usa-se o limite mais restrito). **Proibida
prorrogação e compensação de jornada em qualquer hipótese.** Nesta planilha, aprendiz não tem um
`CONTRATO:` próprio — aparece com `CONTRATO: ESTÁGIO` e a palavra "aprendiz" só no texto do `CARGO:`
(ex.: "JOVEM APRENDIZ - VENDEDOR", "AUXILIAR DE VENDAS APRENDIZ"). A skill detecta isso pelo texto do
cargo e aplica 6h/dia (30h/semana) em vez de 30h padrão do estágio comum — que dão o mesmo número por
coincidência (6h × 5 = 30h), mas a regra de "nunca hora extra" é checada à parte, direto nos campos de
acordo de compensação/prorrogação.
Fonte: [Lei 10.097/2000](https://www2.camara.leg.br/legin/fed/lei/2000/lei-10097-19-dezembro-2000-365495-publicacaooriginal-1-pl.html).

**Trabalho intermitente (CLT art. 452-A): sem teto legal de jornada agregada.** A lei regula a forma
de convocação (mínimo 3 dias corridos de antecedência, resposta em 1 dia útil) e a remuneração mínima
por hora, mas é silenciosa quanto a um limite semanal/mensal total — o total de horas no mês varia
conforme quantas convocações o trabalhador aceita. Aplicar 44h/220h aqui gera falso positivo. A skill
**não faz a checagem de jornada** pra esse tipo de contrato — nem "dentro" nem "acima", simplesmente
não se aplica.
Fonte: [CLT art. 452-A](https://www.jusbrasil.com.br/topicos/173000167/artigo-452a-do-decreto-lei-n-5452-de-01-de-maio-de-1943);
Portaria MTP nº 671/2021.

**Horista** é forma de remuneração (pago por hora), não um tipo de contrato à parte — segue o limite
normal de 44h/220h do CLT comum. Nenhuma regra especial necessária.
Fonte: [Pontotel — horista](https://www.pontotel.com.br/horista/).

**Tempo parcial (CLT art. 58-A): 30h/semana sem hora extra, ou 26h/semana com até 6h extras** (150h ou
130h/mês, respectivamente) — **não é detectável pelos campos do formulário desta planilha** (não existe
uma marcação "regime parcial", precisaria vir de um campo dedicado que a empresa preenche). Limitação
conhecida, não implementada — se aparecer um caso real que dependa disso, registrar aqui.
Fonte: [CLT art. 58-A](https://modeloinicial.com.br/lei/CLT/consolidacao-leis-trabalho/art-58a).

**Teletrabalho sem controle de jornada (CLT art. 62, III e art. 75-B §3º)**: fica fora do capítulo de
duração do trabalho — campo de horário vazio ou genérico é esperado, não é dado faltando, **desde que**
não haja controle de horário pelo empregador (ponto eletrônico, exigência de login em horário fixo). Se
houver controle, as regras normais (44h/220h) voltam a valer. **Não implementado** — o formulário não
tem um campo que diga "é teletrabalho com/sem controle de jornada"; limitação conhecida.
Fonte: [Conjur — home office e horas extras](https://conjur.com.br/2025-out-24/trabalho-em-home-office-e-o-direito-as-horas-extras/).
