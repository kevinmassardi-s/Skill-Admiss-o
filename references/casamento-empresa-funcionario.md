# Casar a linha da EMPRESA com a linha do FUNCIONARIO

## O problema

Os dois formulários são independentes — não existe hoje uma chave única em comum (nem CPF, nem ID de
admissão) entre a aba `EMPRESA` e a aba `FUNCIONARIO`. O único jeito de saber que uma linha de cada
aba pertence à mesma admissão é o **nome da empresa** e o **nome do colaborador** baterem.

Isso já mostrou ser frágil no arquivo de exemplo: a mesma empresa apareceu como "Ferreira Fabris
comércio e confecções LTDA" numa linha e "Ferreira fabris comércio e confecções Ltda" (minúsculas
diferentes, espaço a mais) noutra. Nome não é uma chave confiável — é só a única disponível.

## Como casar

1. **Normalizar antes de comparar**, nos dois lados (nome da empresa e nome do colaborador):
   - maiúsculas/minúsculas uniformizadas,
   - espaços duplicados colapsados, espaços nas pontas removidos,
   - acentuação preservada (não remover — "José" e "Jose" são sinais diferentes, não normalizar a
     ponto de confundir pessoas distintas).
2. **Casar por igualdade exata pós-normalização** de nome do colaborador + nome da empresa.
3. Se exatamente **um** candidato bate nos dois nomes → casamento automático, aceito.
4. Se **nenhum** candidato bate → registrar como "não casado", nunca inventar o par. Mostrar a Kevin
   as linhas soltas de cada aba (empresa sem funcionário correspondente e vice-versa).
5. Se **mais de um** candidato bate (ex.: duas pessoas com o mesmo nome em clientes diferentes, ou o
   mesmo nome de empresa com grafias diferentes) → não escolher sozinho. Apresentar os candidatos
   (com timestamp de cada resposta, que costuma ser o segundo sinal mais forte — respostas da mesma
   admissão tendem a ter carimbo de data/hora próximo) e perguntar a Kevin qual é o par certo.

## Segunda tentativa, mais solta (só como sugestão)

**Achado real (2026-08-12).** A mesma empresa apareceu grafada de pelo menos 6 jeitos diferentes no
histórico desta planilha: `R G TAVARES DROGARIA LTDA`, `RG TAVARES DROGARIA EIRELI`,
`DROGARIA J G TAVARES LTDA`, `DROGARIA JG TAVARES LTDA`, entre outras variações de espaço e pontuação.
Uma admissão real ficou "sem par" só porque a EMPRESA usou "JG" (sem espaço) e o FUNCIONARIO usou "J G"
(com espaço) — a normalização básica (maiúscula + espaço duplicado) não pegava essa diferença.

Quando a tentativa exata não encontra ninguém, a skill tenta uma segunda vez com o nome da empresa e do
colaborador **sem espaço nenhum** (não só duplicado — todo espaço removido). Se essa segunda tentativa
achar um candidato, ele entra num grupo à parte, **"prováveis"** — nunca é aceito automaticamente,
sempre aparece pra confirmação. É a mesma regra do caso ambíguo: a skill sugere, não decide.

## O que NÃO fazer

- Não usar apenas o primeiro nome ou um "nome parecido" (distância de edição) para casar sozinho —
  isso é exatamente o tipo de casamento por semelhança sem segundo critério que já causou erro em
  outro processo desta base (ver `e-consignado-controle-mensal.md`, caso ATHCO MAINT vs. ATHCO
  EMPREENDIMENTOS). Semelhança pode **sugerir** um candidato para a lista de ambíguos, nunca decidir
  sozinha.
- Não assumir que a ordem das linhas nas duas abas corresponde (a mesma admissão pode chegar em
  qualquer ordem, e uma aba pode ter mais respostas do que a outra por documentos reenviados).
- Não descartar em silêncio uma linha que não casou — ela vira pendência "sem par encontrado", não
  desaparece do relatório.
