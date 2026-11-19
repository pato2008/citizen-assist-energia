# 1. Contexto: público, necessidade energética e contribuição ao Citizen Assist AI

## 1.1 Público escolhido

**Moradores de residências urbanas que usam chuveiro elétrico e procuram o Citizen Assist AI para entender e reduzir a conta de luz**,
em especial famílias de renda baixa e média, que sentem o peso da tarifa e raramente têm acesso a orientação técnica gratuita e confiável.
O assistente usa linguagem simples, pede apenas números (nada de nome, endereço, CPF ou número de cliente) e mostra de onde vêm os dados.

## 1.2 Necessidade energética abordada

**Água quente do banho.** O chuveiro elétrico transforma toda a eletricidade em calor (efeito Joule), por isso uma potência alta (por exemplo,
5.500 W) multiplicada pelos minutos de banho da família vira um consumo grande. O IDEC descreve o chuveiro como "um dos principais responsáveis pelo
alto consumo de energia em residências brasileiras" [R1], e a pesquisa de posse e hábitos do Procel registra, no estado de São Paulo, banhos
de 6 a 10 minutos como a faixa mais comum e cerca de 3,6 usos do chuveiro por dia por domicílio [R4].

Escolhemos esse uso porque:

1. é **um único equipamento** com potência conhecida, o que permite cálculo transparente (energia = potência x tempo) que o usuário consegue refazer;
2. existe uma **alternativa renovável madura** para exatamente a mesma necessidade (aquecimento solar de água) e uma **alternativa de custo zero** (hábito);
3. a decisão envolve **dinheiro, viabilidade e impacto ambiental**, como pede o enunciado.

## 1.3 Como as orientações contribuem

| A pessoa precisa saber... | O módulo Energia responde com... |
| --- | --- |
| Quanto meu chuveiro gasta? | kWh por mês e por ano e custo em R$, com a potência, o tempo e a tarifa informados. |
| O que posso fazer sem gastar? | Alternativa A1: banho mais curto, com economia em kWh, R$ e litros de água. |
| Compensa um aquecedor solar? | Alternativa A2 (renovável): investimento, economia líquida, retorno e condições de viabilidade. |
| Isso se aplica à minha casa? | Perguntas sobre autorização para instalar e sol no telhado; sem isso o solar é "não recomendado agora". |
| Posso confiar? | Fontes com data de consulta, parâmetros marcados como estimados e limitações em toda resposta. |

## 1.4 Perfis de uso (hipotéticos) usados nos testes

| Perfil | Descrição | O que esperamos do assistente |
| --- | --- | --- |
| **P1** | Casa própria, 4 pessoas, banho de 8 min, chuveiro de 5.500 W, kWh a R$ 1,10, telhado com sol. | Recomenda o banho de 6 min e sugere pedir orçamentos de solar (retorno ≈ 6,2 anos). |
| **P2** | Apartamento alugado, 2 pessoas, banho de 7 min, sem autorização para instalar. | Recomenda só o hábito; solar "não recomendado agora" e explica o motivo. |
| **P3** | Casa própria, 3 pessoas, banho de 5 min, kWh a R$ 0,80. | Reconhece que o banho já é curto; solar com retorno longo, sem incentivar a compra. |
| **P4** | Entrada inválida: "90 minutos de banho" ou "tarifa R$ 9". | Explica o erro em linguagem simples e pergunta de novo, sem travar. |

## 1.5 Relação com o Citizen Assist AI

O Citizen Assist AI é o assistente digital do grupo; cada disciplina contribui com um módulo testável separadamente. A contribuição de
**Soluções em Energias Renováveis e Sustentáveis** é este repositório: o módulo `energia/`, a base de dados e premissas (`dados/`), a documentação
dos cálculos (`docs/`) e a integração (`integracao/`). Detalhes em [`07_integracao_citizen_assist.md`](07_integracao_citizen_assist.md).

## 1.6 O que este módulo não faz

* Não é canal oficial de nenhuma distribuidora e não confirma descontos (como a tarifa social) nem concessão de serviços.
* Não projeta ou dimensiona sistemas solares (isso é função de instalador habilitado).
* Não coleta dados pessoais; guarda nada além do que a pessoa digita durante a conversa.
