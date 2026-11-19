# 2. Dados utilizados, origem e premissas

Todos os números do módulo estão em [`dados/parametros.json`](../dados/parametros.json), cada um com **valor, unidade, tipo e origem**.
Para trocar uma premissa basta editar o arquivo; o código, os testes e esta tabela usam o mesmo JSON.

* **PÚBLICO**: valor lido de uma fonte pública (referência indicada, consultada em 18/11/2026).
* **ESTIMADO / PREMISSA**: valor assumido pela equipe com justificativa. **São estimativas, não medições.**
* **CALCULADO**: obtido a partir de dados públicos por conta simples (descrita na origem).

**Período de referência:** 12 meses (ano típico); retorno do investimento em 10 anos. **Moeda:** R$ (reais de 2026, sem inflação).
**Unidades:** potência em W, energia em kWh, tarifa em R$/kWh, tempo em minutos, emissões em kg de CO2.

## 2.1 Tabela de parâmetros

| Parâmetro | Valor | Unidade | Tipo | Origem / justificativa | Ref. |
| --- | --- | --- | --- | --- | --- |
| `pessoas` | 4 | pessoas | PREMISSA | Cenário de referência: família de 4 pessoas (mesmo porte da casa popular do estudo R2). | R2 |
| `banhos_por_pessoa_dia` | 1 | banho/pessoa/dia | ESTIMADO | R4 indica média de 3,58 usos do chuveiro por dia por domicílio em SP; 1 banho por pessoa em uma família de 4 tem a mesma ordem de grandeza. | R4 |
| `minutos_por_banho` | 8 | min | ESTIMADO | Centro da faixa de 6 a 10 minutos, a mais comum em SP (R4). | R4 |
| `potencia_chuveiro_w` | 5.500 | W | PÚBLICO | Potência nominal de chuveiro comum, na posição mais quente (R5, R1). Na posição 'verão' a potência é menor: usar 5.500 W é uma hipótese de consumo alto. | R5, R1 |
| `dias_mes` | 30 | dias | PREMISSA | Convenção de mês de 30 dias. | - |
| `tarifa_sem_tributos_rs_kwh` | 0,849 | R$/kWh | PÚBLICO | Tarifa média residencial B1 estimada para 2026, sem tributos (R$ 849/MWh). | R7 |
| `icms_pct` | 18 | % | PÚBLICO | ICMS médio citado no boletim (R7). | R7 |
| `pis_cofins_pct` | 4,9 | % | PÚBLICO | PIS/Cofins médio citado no boletim (R7). | R7 |
| `bandeira_adicional_rs_100kwh` | 0 | R$/100 kWh | PÚBLICO | Bandeira verde em novembro/2026: sem acréscimo (R6). Na amarela seria R$ 1,885/100 kWh. | R6 |
| `minutos_por_banho_a1` | 6 | min | ESTIMADO | Alternativa A1 (hábito): limite inferior da faixa de 6 a 10 minutos mais comum (R4). Se a pessoa já toma banho mais curto, A1 não gera economia. | R4 |
| `reducao_solar_base` | 0,66 | fração | ESTIMADO | Redução do consumo elétrico do aquecimento de água com aquecedor solar e apoio elétrico: (11 - 3,75) / 11 = 0,659 no estudo R2, arredondada para 0,66. | R2 |
| `reducao_solar_min` | 0,5 | fração | ESTIMADO | Cenário conservador definido pela equipe (dias nublados, sistema mal orientado ou com sombra). | - |
| `reducao_solar_max` | 0,7 | fração | PÚBLICO | 'Economia de até 70%' declarada pelo fabricante (R3). É limite superior de propaganda, não garantia. | R3 |
| `investimento_solar_rs` | 4.500 | R$ | ESTIMADO | Valor central da faixa de R$ 3.000 a R$ 6.000 para sistemas residenciais de baixa pressão (R1). O estudo R2 usou R$ 3.899 (preços de 2020). | R1, R2 |
| `investimento_solar_min` | 3.000 | R$ | PÚBLICO | Limite inferior da faixa do IDEC (R1). | R1 |
| `investimento_solar_max` | 6.000 | R$ | PÚBLICO | Limite superior da faixa do IDEC (R1). | R1 |
| `manutencao_solar_pct_ano` | 1 | % do investimento por ano | ESTIMADO | Sem valor publicado nas fontes: R1 apenas diz que o sistema exige 'pouca manutenção'. A equipe adotou 1% ao ano como reserva. | R1 |
| `vida_util_coletor_anos` | 15 | anos | PÚBLICO | Faixa de 15 a 25 anos (R1); usamos o limite inferior. | R1 |
| `vida_util_boiler_anos` | 10 | anos | PÚBLICO | Faixa de 10 a 15 anos (R1); usamos o limite inferior. | R1 |
| `horizonte_anos` | 10 | anos | PREMISSA | Horizonte de comparação = vida útil mínima do boiler (R1), para não contar benefício além da vida útil do equipamento mais curto. | R1 |
| `pmee_coletor_kwh_mes` | 121,4 | kWh/mês por coletor | PÚBLICO | Coletor '1,5 Maxime', classe A (PBE/Inmetro), área externa 1,46 m² (R3). Usado só como teste de ordem de grandeza. | R3 |
| `fator_emissao_kg_co2_kwh` | 0,025 | kg CO2/kWh | CALCULADO | Média simples de jan-abr/2025: (23,7 + 24,8 + 21,5 + 28,9) / 4 = 24,725 kg/MWh (R8). É o fator MÉDIO da rede, não o marginal. | R8 |
| `vazao_chuveiro_l_min` | 5 | L/min | PREMISSA | Vazão do chuveiro elétrico adotada no estudo R2. | R2 |
| `alerta_chuveiro_pct_da_conta` | 0,6 | fração | ESTIMADO | Heurística da equipe: se o chuveiro estimado passa de 60% do total da conta informada, o assistente pede para conferir potência, tempo e número de banhos. | - |
| `altura_max_caixa_dagua_m` | 5 | m | PÚBLICO | Em sistemas de baixa pressão, a caixa d'água deve ficar a até 5 m de altura do reservatório (R1). | R1 |

## 2.2 O que NÃO é dado real (e por quê)

1. **Perfil do cenário de referência** (4 pessoas, 1 banho por pessoa por dia, 8 min): é uma família hipotética, coerente com o estudo R2 e com a faixa mais comum de tempo de banho da pesquisa R4. Cada pessoa pode informar o seu.
2. **Investimento do aquecedor solar (R$ 4.500)**: ponto médio da faixa publicada pelo IDEC (R$ 3.000 a R$ 6.000). Orçamentos reais variam.
3. **Redução de 66% do consumo elétrico do chuveiro**: vem de **um estudo de caso** (R2) e fica entre o cenário conservador da equipe (50%) e a promessa do fabricante (70%).
4. **Manutenção de 1% ao ano**: reserva da equipe; as fontes só dizem que a manutenção é pouca.
5. **Tarifa**: valor médio nacional estimado para 2026. A tarifa da sua distribuidora (e descontos como a tarifa social) muda o resultado, por isso o assistente pergunta o valor do kWh da sua conta.

## 2.3 Fórmulas e constantes físicas

Não há constante física "escondida": o modelo usa apenas energia = potência x tempo (Wh = W x h). A comparação com o calor necessário para esquentar a água (m x c x ΔT) foi substituída pelo teste de ordem de grandeza com a energia por coletor da etiqueta PBE/Inmetro (ver `docs/03_calculos_e_comparacao.md`, seção 3.7).
