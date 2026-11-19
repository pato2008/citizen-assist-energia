"""Regras de recomendação do assistente de energia.

As recomendações SEMPRE saem dos números calculados em energia.calculos (nada é escrito
"de cabeça"), citam as referências e dizem as condições/limites das estimativas.
"""
from .calculos import cenario

AVISO = ("Orientação educativa do protótipo Citizen Assist AI. Não é canal oficial da distribuidora, "
         "não coleta dados pessoais e as estimativas NÃO são garantia de economia, geração ou custo.")

LIMITACOES = [
    "Os cálculos usam valores médios (tarifa nacional, potência de 5.500 W, tempo de banho típico). "
    "Informe os dados da SUA conta e do SEU chuveiro para chegar mais perto da realidade.",
    "Retorno do investimento é 'simples': sem juros, sem reajuste de tarifa e sem desconto de tarifa social.",
    "A redução do aquecedor solar (50% a 70%) vem de um estudo de caso e de material de fabricante; "
    "depende de orientação do telhado, sombra, clima e do uso do apoio elétrico.",
    "Preços de sistemas solares variam por região e por fornecedor: peça pelo menos 3 orçamentos.",
    "O fator de emissão usado é o MÉDIO da rede (jan-abr/2025); o efeito real de economizar energia pode ser diferente.",
    "A alternativa A1 (banho mais curto) muda o hábito; as alternativas A2/A3 mantêm o mesmo tempo de banho.",
]

REFERENCIAS_USADAS = {
    "consumo": ["R4", "R5", "R1"],
    "tarifa": ["R7", "R6"],
    "solar": ["R1", "R2", "R3"],
    "ambiental": ["R8", "R2"],
}


def _fmt_rs(valor):
    return "R$ {:,.2f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_num(valor, casas=0):
    return "{:,.{c}f}".format(valor, c=casas).replace(",", "X").replace(".", ",").replace("X", ".")


def _anos(valor):
    return "%s anos" % _fmt_num(valor, 1)


def recomendar(resultado, p):
    """Lista de recomendações [{'id','titulo','texto','refs'}] a partir do resultado de simular()."""
    recs = []
    a0, a1, a2, a3 = (cenario(resultado, c) for c in ("A0", "A1", "A2", "A3"))
    entrada = resultado["entrada"]
    horizonte = resultado["horizonte_anos"]
    vida_boiler = p.v("vida_util_boiler_anos")
    vida_coletor = p.v("vida_util_coletor_anos")

    # 1) Hábito: não custa nada
    if a1["economia_bruta_ano_rs"] > 0.5:
        recs.append({
            "id": "habito", "refs": REFERENCIAS_USADAS["consumo"],
            "titulo": "Primeiro passo (custo zero): banho de %s minutos" % _fmt_num(a1["minutos_por_banho"]),
            "texto": ("Reduzir o banho de %s para %s minutos economiza cerca de %s kWh por ano (≈ %s por ano) e "
                      "%s litros de água por mês. É uma mudança de hábito: o banho fica mais curto."
                      % (_fmt_num(entrada["minutos_por_banho"]), _fmt_num(a1["minutos_por_banho"]),
                         _fmt_num(a0["kwh_ano"] - a1["kwh_ano"]), _fmt_rs(a1["economia_bruta_ano_rs"]),
                         _fmt_num(a1["agua_economizada_l_mes"]))),
        })
    else:
        recs.append({
            "id": "habito", "refs": REFERENCIAS_USADAS["consumo"],
            "titulo": "Seu tempo de banho já é curto",
            "texto": ("Com %s minutos por banho você já está no limite da faixa mais comum (6 a 10 min); "
                      "reduzir mais traz pouca economia." % _fmt_num(entrada["minutos_por_banho"])),
        })

    # 2) Renovável: aquecedor solar
    if not a2["viavel"]:
        recs.append({
            "id": "solar", "refs": ["R1"],
            "titulo": "Aquecedor solar: não é recomendado agora",
            "texto": ("No seu caso há um impedimento (%s). Sem isso o sistema não funciona bem ou não pode ser instalado. "
                      "Se isso mudar, refaça a simulação." % a2["motivo_inviavel"]),
        })
    else:
        pb = a2["payback_anos"]
        if pb is None:
            texto = ("Com os dados informados o aquecedor solar não se paga (a economia anual não cobre a manutenção). "
                     "Só faria sentido com tarifa maior, mais banhos por dia ou subsídio.")
            titulo = "Aquecedor solar: não compensa financeiramente com estes dados"
        elif pb <= horizonte:
            titulo = "Aquecedor solar (renovável): vale pedir orçamentos"
            texto = ("Com investimento de %s e redução de %s%% no consumo do chuveiro, a economia líquida seria de "
                     "≈ %s por ano e o retorno de ≈ %s (dentro de %s anos e da vida útil do boiler, %s anos). "
                     "Ao fim de %s anos o ganho líquido acumulado seria de ≈ %s, sem contar juros."
                     % (_fmt_rs(resultado["investimento_solar_rs"]), _fmt_num(resultado["reducao_solar"] * 100),
                        _fmt_rs(a2["economia_liquida_ano_rs"]), _anos(pb), horizonte, vida_boiler,
                        horizonte, _fmt_rs(a2["beneficio_liquido_horizonte_rs"])))
        elif pb <= vida_coletor:
            titulo = "Aquecedor solar (renovável): retorno lento"
            texto = ("O retorno estimado é de ≈ %s, acima do horizonte de %s anos (e o boiler pode precisar de troca antes "
                     "disso: vida útil de %s a 15 anos). Pode compensar no longo prazo, mas só vale se você pretende ficar no "
                     "imóvel e se houver desconto, financiamento ou subsídio." % (_anos(pb), horizonte, vida_boiler))
        else:
            titulo = "Aquecedor solar: retorno longo demais"
            texto = ("O retorno estimado (≈ %s) passa da vida útil mínima do coletor (%s anos). Com estes dados não "
                     "recomendamos investir." % (_anos(pb), vida_coletor))
        recs.append({"id": "solar", "refs": REFERENCIAS_USADAS["solar"], "titulo": titulo, "texto": texto})

        # combinação A3 e retorno sobre A1
        if a1["economia_bruta_ano_rs"] > 0.5 and a3.get("payback_sobre_a1_anos"):
            recs.append({
                "id": "combinado", "refs": REFERENCIAS_USADAS["solar"],
                "titulo": "Banho curto + solar: o solar rende menos",
                "texto": ("Quem já adotou o banho de %s min gasta menos energia, então o solar economiza menos: o retorno do "
                          "solar sobre o banho curto sobe para ≈ %s. Por isso o hábito vem primeiro e o investimento depois."
                          % (_fmt_num(a1["minutos_por_banho"]), _anos(a3["payback_sobre_a1_anos"]))),
            })

        # viabilidade: checagem de ordem de grandeza do coletor
        cap = resultado["checagens"].get("capacidade_um_coletor_vs_demanda")
        if cap:
            recs.append({
                "id": "dimensionamento", "refs": ["R3"],
                "titulo": "Teste de ordem de grandeza do coletor",
                "texto": ("Um coletor solar classe A (PBE/Inmetro) da linha consultada produz ≈ %s kWh/mês, cerca de %sx o consumo "
                          "mensal estimado do seu chuveiro (%s kWh). Ou seja, a energia disponível não é o limitador; "
                          "o que limita a economia são dias nublados, uso do apoio elétrico e perdas. O dimensionamento final "
                          "deve ser feito por um instalador."
                          % (_fmt_num(p.v("pmee_coletor_kwh_mes"), 1), _fmt_num(cap, 1), _fmt_num(resultado["consumo_base_mes_kwh"]))),
            })

    # 3) Ambiental
    texto_amb = ("O fator médio de emissão da rede elétrica brasileira é baixo (≈ %s kg CO2/MWh em jan-abr/2025), então o CO2 "
                 "evitado ao economizar energia é pequeno" % _fmt_num(p.v("fator_emissao_kg_co2_kwh") * 1000, 1))
    if a2["viavel"]:
        texto_amb += ": ≈ %s kg por ano com o aquecedor solar (A2)" % _fmt_num(a2["co2_evitado_kg_ano"], 1)
    texto_amb += ". O ganho principal é financeiro e de menor demanda de energia"
    if a1["agua_economizada_l_mes"] > 0.5:
        texto_amb += "; o banho mais curto (A1) também economiza ≈ %s litros de água por mês" % _fmt_num(a1["agua_economizada_l_mes"])
    texto_amb += "."
    recs.append({"id": "ambiental", "refs": REFERENCIAS_USADAS["ambiental"], "titulo": "Impacto ambiental", "texto": texto_amb})

    # 4) Cuidados antes de comprar
    if a2["viavel"]:
        recs.append({
            "id": "cuidados", "refs": ["R1", "R3"],
            "titulo": "Antes de comprar",
            "texto": ("Peça pelo menos 3 orçamentos; prefira coletores com etiqueta PBE/Inmetro classe A; em sistema de baixa pressão a "
                      "caixa d'água deve ficar a até %s m do reservatório; confirme com o instalador a orientação e a sombra do telhado."
                      % _fmt_num(p.v("altura_max_caixa_dagua_m"))),
        })
    return recs
