# 4. Justificativas das recomendações (custos, viabilidade e impactos ambientais)

Os números abaixo são os do cenário-base (família de 4, banho de 8 min, chuveiro de 5.500 W, kWh a R$ 1,10), calculados em
[`03_calculos_e_comparacao.md`](03_calculos_e_comparacao.md). Para outros perfis o assistente recalcula.

## 4.1 Quadro-resumo

| | **A1 Banho mais curto (hábito)** | **A2 Aquecedor solar + apoio elétrico (renovável)** |
| --- | --- | --- |
| **Custo** | R$ 0. Economia de R$ 290,40 por ano (264 kWh). | Investimento estimado de R$ 4.500 (faixa R$ 3.000 a R$ 6.000 [R1]) e manutenção de ≈ R$ 45 por ano. Economia líquida de R$ 721,66 por ano. |
| **Retorno** | Imediato. | 6,2 anos (faixa na sensibilidade: 3,4 a 13,2 anos conforme tarifa e preço). Dentro do intervalo de 2 a 7 anos citado pelo IDEC [R1]. |
| **Viabilidade** | Depende só do hábito. Barreira: conforto e costume (mudança de comportamento). | Exige imóvel próprio ou autorização, telhado/laje com sol sem sombra, caixa d'água a até 5 m do reservatório em sistema de baixa pressão [R1], instalador habilitado e capital inicial (barreira para famílias de baixa renda). |
| **Impacto ambiental** | 264 kWh a menos por ano (≈ 6,5 kg de CO2) e 1.200 L de água a menos por mês. | Substitui ≈ 66% da eletricidade do chuveiro por energia solar: 697 kWh por ano a menos (≈ 17 kg de CO2 com o fator médio da rede). O CO2 evitado é pequeno porque a rede brasileira emite pouco [R8]; o ganho principal é financeiro. Fabricação e descarte do equipamento **não** foram quantificados. |
| **Quando recomendar** | Sempre que o banho passar de 6 min. | Quando há condições físicas **e** o retorno é ≤ 10 anos (vale pedir orçamentos); retorno entre 10 e 15 anos = "retorno lento"; acima de 15 anos = "longo demais". |
| **Principal risco** | Economia menor se a pessoa já toma banhos curtos. | A economia real pode ser menor que 66% (sombra, orientação, dias nublados). O cenário conservador (50%) leva o retorno a 8,4 anos. |

**A3 (A1 + A2)** reduz o consumo anual de 1.056 para ≈ 269 kWh, mas quem já adotou o banho curto ganha menos com o solar: o retorno do solar **sobre o A1**
sobe para 8,5 anos. Por isso o assistente apresenta o hábito primeiro e o investimento depois.

## 4.2 Regras de decisão do assistente

| Condição (a partir dos dados informados) | Recomendação mostrada |
| --- | --- |
| Minutos por banho > 6 | "Primeiro passo (custo zero): banho de 6 minutos" com economia em kWh, R$ e litros. |
| Minutos por banho ≤ 6 | "Seu tempo de banho já é curto": sem incentivo a reduzir mais. |
| Sem autorização para instalar **ou** sem sol no telhado | "Aquecedor solar: não é recomendado agora", com o motivo. |
| Solar viável e economia líquida ≤ 0 | "Não compensa financeiramente com estes dados". |
| Solar viável e retorno ≤ 10 anos | "Vale pedir orçamentos". |
| Solar viável e retorno entre 10 e 15 anos | "Retorno lento": só com subsídio/financiamento ou se pretende ficar no imóvel. |
| Solar viável e retorno > 15 anos | "Retorno longo demais: não recomendamos investir". |
| Chuveiro estimado > 60% da conta informada | Alerta de possível exagero (posição "verão" ou banho curto). |
| Chuveiro estimado > 100% da conta informada | Dado recusado como incoerente; o assistente pede para conferir potência, tempo e nº de banhos. |

Os limites de 10 e 15 anos vêm da vida útil mínima do boiler (10 anos) e do coletor (15 anos) [R1].

## 4.3 O que o assistente se recusa a afirmar

* Que o solar "sempre compensa": para 2 pessoas e tarifa de R$ 1,10 o retorno estimado é de 13,3 anos.
* Que a economia é garantida: toda resposta traz "estimativa, não garantia" e as limitações.
* Que o CO2 evitado é grande: com o fator médio atual da rede, é pequeno (ver seção 4.1).
* Valores de tarifa social, financiamento ou subsídios: não estão no modelo; ele orienta a conferir com a distribuidora.

## 4.4 Coerência entre os cálculos e as respostas do assistente

Cada afirmação do assistente vem de um campo do resultado de `consultar_energia()`, e cada fórmula tem teste com valor calculado à mão:

| O assistente diz... | Vem de... | Teste que confere |
| --- | --- | --- |
| "gasta ≈ 88 kWh por mês" | `energia_mensal_kwh(5500, 8, 4, 30)` | `TestFormulas.test_energia_mensal` |
| "R$ 1.161,60 por ano" | `custo_ano_rs` de A0 | `TestCenarioBase.test_custos_anuais_com_tarifa_1_10` |
| "retorno de ≈ 6,2 anos" | `4500 / 721,656` | `TestCenarioBase.test_economia_e_payback_do_solar` |
| "sobre o banho curto sobe para ≈ 8,5 anos" | `payback_sobre_a1_anos` | `TestCenarioBase.test_payback_do_solar_sobre_o_habito` |
| "solar não recomendado agora" | `viavel = False` | `TestRegrasEEntradas.test_sem_autorizacao_ou_sem_sol_torna_solar_inviavel` |
| mensagens de erro | `EntradaInvalida` | `TestRegrasEEntradas.test_entradas_invalidas` |
| fontes citadas | `referencias` do JSON | `TestParametros.test_todo_parametro_tem_origem_tipo_e_referencia_valida` |

## 4.5 Comparação com o que as fontes dizem

* **Retorno:** o IDEC [R1] fala em 2 a 7 anos; nosso cenário-base dá 6,2 anos. Com tarifas baixas (R$ 0,74) e investimento de R$ 6.000 sai 13,2 anos, fora da faixa do IDEC, o que mostra que a faixa depende do perfil.
* **Redução do consumo:** o estudo [R2] mediu 66% (11 para 3,75 kWh por dia) e o fabricante [R3] promete "até 70%"; usamos 66% como base e 50% como cenário conservador.
* **Energia do coletor:** um coletor classe A produz ≈ 1,4x a demanda do chuveiro do cenário-base [R3], coerente com reduções altas, mas limitadas por dias nublados e apoio elétrico.

## 4.6 O que mudaria as recomendações

1. Tarifa menor que ≈ R$ 0,75 ou consumo de chuveiro baixo (poucas pessoas, banhos curtos): o solar deixa de compensar.
2. Preço do sistema fora da faixa R$ 3.000 a R$ 6.000, ou subsídio/financiamento a juros baixos.
3. Redução real do consumo abaixo de 50% (sombra, orientação ruim): retorno acima de 8,4 anos.
4. Alternativas não analisadas aqui (por exemplo, painel fotovoltaico para todo o consumo da casa ou chuveiro a gás) exigiriam novos dados e novas fontes.
