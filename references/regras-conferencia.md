# Checklist de conferência

Para cada admissão já casada (linha EMPRESA + linha FUNCIONARIO da mesma pessoa), conferir o
seguinte antes de considerar "pronta para lançar no Domínio".

## Status — quais admissões entram na lista de trabalho

A coluna `DOC PENDENTE` (aba EMPRESA) e `FEITO?` (aba FUNCIONARIO) usam o vocabulário da aba
`LEGENDA`: `SIM`, `ANDAMENTO`, `DUPLICADO`, `CANCELOU`, `DESISTIU`, `DOC PENDENTE`, `EM AUDITORIA`.

Confirmado por Kevin: **`SIM` = concluído**, **em branco = não feito**, os demais são autoexplicativos
(estados intermediários ou terminais que não geram trabalho novo). **`EM AUDITORIA` também não entra**
na lista de trabalho — é um estado que já saiu das mãos de Kevin (está em revisão), não uma pendência
para ele agir agora.

Por padrão, a skill trabalha com linhas cujo status **não é `SIM`, `CANCELOU`, `DESISTIU`, `DUPLICADO`
nem `EM AUDITORIA`** — ou seja, em branco, `ANDAMENTO` ou `DOC PENDENTE`. Isso é uma regra de
conveniência, não uma verdade absoluta: se Kevin pedir para revisar algo já marcado `SIM`, a skill
processa normalmente — o filtro é o ponto de partida, não uma trava.

## Corte por data — o backlog antigo fica de fora

**Decisão de Kevin (2026-08-11):** a rotina do dia a dia só processa admissões cujo "Carimbo de
data/hora" (aba EMPRESA) é **de 11/08/2026 em diante**. Existe backlog bem mais antigo (ex.: uma
admissão de 2025, encontrada durante os testes, ainda sem status de conclusão) que fica de fora dessa
rotina — não é ignorado por engano, é uma decisão explícita de escopo. Registros antigos sem status
final não são o foco da conferência do dia a dia; se algum dia for necessário revisar esse backlog, é
um trabalho à parte, deliberado, não algo que a rotina normal deve tentar resolver de passagem.

O parâmetro `--data-corte` do `scripts/executar_conferencia.py` controla essa data — o padrão é
11/08/2026, mas pode mudar se fizer sentido no futuro (por exemplo, avançar o corte periodicamente).

## Documentos obrigatórios (aba FUNCIONARIO)

**Confirmado por Kevin (2026-08-11): só existem dois documentos realmente obrigatórios.** A lista
anterior deste arquivo tinha mais itens como obrigatórios — isso foi uma suposição minha, não algo que
Kevin havia confirmado, e estava errada. Corrigido aqui.

1. **Documento oficial com foto, frente e verso.** Satisfeito por **qualquer um** destes dois campos
   preenchido — não precisam ser os dois:
   - `RG - FRENTE E VERSO:`
   - `CNH (CASO POSSUA):`

   Pendência só se **nenhum dos dois** estiver presente. O órgão emissor do RG (que a documentação do
   Domínio lista como campo relevante — ver `references/base-legal.md`) **não precisa de checagem
   separada**: confirmado por Kevin que ele já aparece na própria foto do documento, seja RG ou CNH.

2. **`COMPROVANTE DE ENDEREÇO COM CEP E BAIRRO:`** — sempre obrigatório. Confirmado por Kevin: a
   finalidade é buscar **CEP, número e complemento** do endereço do colaborador — não é uma exigência
   direta do eSocial (que só valida o campo "município" como dado, sem pedir anexo — ver
   `references/base-legal.md`), é a forma que o escritório usa pra extrair esses dados corretamente.
   **Não precisa estar no nome do colaborador** — confirmado por Kevin (2026-08-11) depois de um teste
   real onde o comprovante era uma correspondência em nome de outra pessoa. É normal o colaborador
   morar num endereço cujo comprovante está em nome de outra pessoa (família, locador). Se algum dia a
   skill vier a abrir esse documento, checar só CEP/número/complemento — nunca sinalizar nome
   diferente como pendência aqui.

**Obrigatório condicional — dependente:**
- A presença da `CERTIDÃO DE NASCIMENTO (FILHOS MENORES DE 14 ANOS):` é o sinal de que há dependente
  (não existe uma pergunta separada "tem dependente?" no formulário).
- **Ter só a certidão de nascimento não basta — precisa de prova do CPF do dependente.** Confirmado por
  Kevin: essa prova pode vir de duas formas —
  - a própria certidão já contém o CPF impresso, **ou**
  - existe também um documento com foto que mostra o CPF do dependente.

  Na prática, o formulário tem uma coluna dedicada pra isso — `CPF (FILHOS MENORES DE 14 ANOS):` — e é
  ela que a skill confere. Se essa coluna estiver vazia mas a certidão parecer conter o CPF visível (ou
  exista outro documento com o CPF), **isso é uma checagem visual que só Kevin consegue fazer olhando o
  documento** — a skill sinaliza como pendência "confirmar CPF do dependente" nesse caso, não como
  "documento faltando" cego. Ver seção "O que exige julgamento humano" no SKILL.md.

**Explicitamente NÃO obrigatórios — ausência nunca é pendência:**
- Título de eleitor
- Foto 3x4
- Dispensa militar
- Certidão de casamento

## RG igual ao CPF não é erro — é a CIN

**Achado real (2026-08-12).** No caso do Alexsandro Neves Mota do Monte, RG e CPF na planilha vieram
com o **mesmo número** (`447.162.598-54` nos dois). A primeira reação foi tratar como suspeito (erro
de digitação, ou cópia errada) — estava errado. O documento anexado era uma **CIN (Carteira de
Identidade Nacional)**, o novo modelo de identidade do governo federal (gov.br) que **unifica RG e CPF
no mesmo número de registro**. Isso é esperado e correto para quem já tirou a CIN, não uma pendência.

**Não sinalizar RG == CPF como suspeito.** Se um dia isso virar uma checagem automática, ela precisa
saber distinguir "RG copiado errado do CPF" de "documento é CIN" — e hoje a única forma confiável de
saber qual dos dois é abrindo o documento. Não decidir isso por dedução.

## Dados pessoais (aba FUNCIONARIO)

- **CPF do colaborador é obrigatório e precisa estar legível como texto.** Ver o alerta em
  `references/estrutura-planilha.md` sobre esse campo chegar como número em notação científica — se
  isso acontecer, é sinal de erro de formatação da planilha, não um CPF realmente diferente; sinalizar
  como pendência "conferir CPF — formato suspeito", nunca tentar reconstruir o número.
- **PIS não é mais obrigatório** (confirmado por Kevin em 2026-08-11, depois de pesquisa: desde o
  Decreto 9.723/2019 o CPF substituiu o PIS como identificador no eSocial — ver
  `references/base-legal.md`). Se vier preenchido, ótimo — ainda vale checar o formato (mesmo risco de
  notação científica). Se vier vazio, **não é pendência**.

## Dados contratuais (aba EMPRESA)

- **Horário de trabalho:** exibir o texto literal em destaque. **Não somar horas automaticamente** —
  é texto livre e a conta de 220h semanais fica com Kevin (ver princípio em `SKILL.md`).
- **Vale-transporte:** exibir o valor do sinalizador de desconto de 6%, sem interpretar.
- **Adiantamento salarial:** exibir o valor do sinalizador, sem interpretar.
- **Prorrogação de horas / compensação de horas:** exibir se o sinalizador está presente — isso
  determina se o termo correspondente precisa ser gerado no Domínio. Não decidir sozinho se o termo é
  necessário além do que o sinalizador já indica.
- **Cargo sem CBO:** **não é pendência.** Confirmado por Kevin — só bate a informação e lança.
- **ASO (exame médico admissional):** **fora de escopo.** Não incluir no relatório de conferência,
  mesmo que a coluna esteja preenchida ou vazia.

## CPF duplicado entre pessoas diferentes do lote

**Achado real (2026-08-11).** Testando um lote real, duas admissões diferentes — Auany Vieira Pereira
e Wandrey Juneo Oliveira Cardoso, mesma empresa — reconstruíram o **mesmo CPF** a partir da notação
científica. Abrindo o RG/CNH de cada uma: o CPF do Wandrey estava certo; o da Auany era, na verdade,
uma cópia errada do CPF do Wandrey colada na linha dela. A planilha em si tinha o dado errado — não era
só formatação.

**Regra:** depois de resolver o CPF de todo mundo do lote (reconstruído ou não), comparar entre si. Se
duas admissões diferentes caírem no mesmo CPF, **nenhuma das duas** é "pronta" — as duas viram
pendência, com o nome da outra pessoa envolvida, até alguém confirmar com o documento qual está certo.
CPF é único por pessoa; duas pessoas com o mesmo CPF é sempre erro de dado, nunca coincidência legítima.

## Jornada de trabalho — limite varia por tipo de contrato

Pedido do Kevin (2026-08-12): conferir automaticamente jornada semanal/mensal, sempre alertando quando
passar do limite. O limite **não é sempre 44h/220h** — depende do `CONTRATO:` (e, pro caso do
aprendiz, do texto do `CARGO:`). Ver `references/base-legal.md` pra pesquisa completa com fonte.

| Contrato/escala | Limite | Observação |
|---|---|---|
| CLT padrão / horista | 44h semana / 220h mês | Regra geral (CF art. 7º XIII) |
| ESTÁGIO | 30h semana / 150h mês | Lei 11.788/2008 — nunca hora extra |
| ESTÁGIO + cargo com "APRENDIZ" | 6h/dia (30h semana) | Lei 10.097/2000 — nunca hora extra, checado à parte |
| INTERMITENTE | **sem checagem** | CLT art. 452-A não define teto agregado |
| Escala **12x36** | confere o padrão (12h presença), não soma contra teto | Ver seção própria abaixo — 180h/mês é divisor, não teto |

Quando o texto do horário não segue um padrão reconhecido com confiança (mais de um horário no texto,
escala não mapeada, pausa ambígua), a skill **não calcula um número** — vira pendência de "não
consegui calcular, confira manualmente". Isso também conta como o alerta que Kevin pediu: não
conseguir confirmar que está dentro do limite é tratado como não confirmado, nunca como "deve estar
tudo bem".

Tempo parcial e teletrabalho sem controle de jornada têm limites próprios (ver base-legal.md) mas não
são detectáveis pelos campos deste formulário — limitação conhecida, não implementada.

## Escala 12x36 — confere o padrão, não soma contra um teto

**Achado real (2026-08-20).** Diferente dos outros casos, 12x36 não é "some as horas da semana e
compare com um limite" — é "confira se o plantão bate com o padrão legal" (12h de presença, 1h de
intervalo obrigatório = 11h efetivas, alternando 4 e 3 plantões por semana). Guia de referência trazido
por Kevin (fonte: documento gerado por IA a partir do art. 59-A da CLT e Súmula do TST — não veio de
pesquisa própria desta vez, registrado aqui pra rastreabilidade, vale revalidar com fonte oficial se um
dia isso virar ponto de dúvida real).

Tentei primeiro comparar a média mensal real (3,5 plantões x 11h x 5 semanas = **192,5h/mês**) contra o
divisor de folha (**180h/mês**) — deu "ACIMA DO LIMITE" pra um plantão perfeitamente normal, porque
**180h é o divisor usado pra calcular o valor da hora, não um teto de horas trabalhadas** (mesmo erro
conceitual do 220h padrão, ver seção "220h/mês não é teto legal" acima).

**Regra corrigida:** a skill confere se o plantão (texto do horário) bate com ~12h de presença
(tolerância 11h-13h, pra admitir variação de horário de troca) e se tem 1h de intervalo. Se bater,
é **sempre "dentro"**, independente da conta de 192,5h — porque o padrão em si já é o que a lei
autoriza. Se o plantão não bater com ~12h, isso sim é pendência real ("plantão de Xh não bate com o
padrão 12x36 — confira manualmente").

## Formato do resumo "pronto para digitar"

Quando uma admissão passa em todas as checagens (ou sobra só pendência que Kevin já decidiu ignorar),
montar um resumo com os campos na mesma ordem em que aparecem na ficha do Domínio — o objetivo é que
Kevin consiga copiar campo a campo sem caçar informação em duas abas e seis links. Incluir, ao lado de
cada documento, o link do Drive já pronto para abrir.
