"""Cálculos do módulo Energia: consumo do chuveiro elétrico e comparação de alternativas.

Necessidade comparada: água quente do banho da família (mesmo período de referência
para todas as alternativas: 12 meses; retorno do investimento em um horizonte de
10 anos). Fórmula base (energia = potência x tempo):

    E_mes [kWh] = P [kW] x t_banho [h] x banhos_por_dia x dias_do_mes
"""
from dataclasses import dataclass, asdict
import math

from .parametros import Parametros

MESES = 12


class EntradaInvalida(ValueError):
    """Entrada fora do que o assistente consegue tratar (mensagem já em linguagem simples)."""


# (mínimo, máximo, rótulo amigável)
LIMITES = {
    "pessoas": (1, 12, "pessoas"),
    "minutos_por_banho": (1, 40, "minutos por banho"),
    "banhos_por_pessoa_dia": (0.25, 4, "banhos por pessoa por dia"),
    "potencia_w": (1000, 8500, "potência do chuveiro (W)"),
    "tarifa_rs_kwh": (0.20, 3.00, "valor do kWh (R$)"),
    "consumo_conta_kwh_mes": (20, 2000, "consumo mensal da conta (kWh)"),
}


@dataclass
class Perfil:
    pessoas: int = 4
    minutos_por_banho: float = 8
    banhos_por_pessoa_dia: float = 1.0
    potencia_w: float = 5500
    tarifa_rs_kwh: float = None          # None -> usa a tarifa padrão dos parâmetros
    consumo_conta_kwh_mes: float = None  # opcional (para checar coerência)
    pode_instalar: bool = True           # imóvel próprio ou com autorização para instalar
    tem_sol_no_telhado: bool = True      # telhado/laje com sol direto, sem sombra


def ler_numero(valor, nome):
    """Converte texto/número (aceita vírgula decimal) e confere a faixa permitida do campo."""
    minimo, maximo, rotulo = LIMITES[nome]
    if isinstance(valor, bool):
        raise EntradaInvalida("«%s»: valor inválido. Digite apenas números." % rotulo)
    try:
        numero = float(str(valor).replace(",", ".").strip())
    except (TypeError, ValueError):
        raise EntradaInvalida("Não entendi sua resposta para «%s». Digite apenas números, por exemplo 8." % rotulo)
    if math.isnan(numero) or math.isinf(numero):
        raise EntradaInvalida("«%s»: valor inválido. Digite apenas números." % rotulo)
    if not (minimo <= numero <= maximo):
        raise EntradaInvalida("«%s»: o valor deve estar entre %g e %g (você informou %g)." % (rotulo, minimo, maximo, numero))
    return numero


def validar(perfil):
    """Devolve um Perfil validado/normalizado ou levanta EntradaInvalida."""
    pessoas = ler_numero(perfil.pessoas, "pessoas")
    if pessoas != int(pessoas):
        raise EntradaInvalida("«pessoas»: informe um número inteiro (você informou %g)." % pessoas)
    tarifa = None if perfil.tarifa_rs_kwh is None else ler_numero(perfil.tarifa_rs_kwh, "tarifa_rs_kwh")
    conta = None if perfil.consumo_conta_kwh_mes is None else ler_numero(perfil.consumo_conta_kwh_mes, "consumo_conta_kwh_mes")
    return Perfil(
        pessoas=int(pessoas),
        minutos_por_banho=ler_numero(perfil.minutos_por_banho, "minutos_por_banho"),
        banhos_por_pessoa_dia=ler_numero(perfil.banhos_por_pessoa_dia, "banhos_por_pessoa_dia"),
        potencia_w=ler_numero(perfil.potencia_w, "potencia_w"),
        tarifa_rs_kwh=tarifa,
        consumo_conta_kwh_mes=conta,
        pode_instalar=bool(perfil.pode_instalar),
        tem_sol_no_telhado=bool(perfil.tem_sol_no_telhado),
    )


# ----------------------------- fórmulas puras ---------------------------------
def energia_mensal_kwh(potencia_w, minutos_por_banho, banhos_por_dia, dias_mes=30):
    """E = P x t x n x dias  (kWh por mês)."""
    return potencia_w / 1000.0 * (minutos_por_banho / 60.0) * banhos_por_dia * dias_mes


def custo_rs(kwh, tarifa_rs_kwh):
    return kwh * tarifa_rs_kwh


def payback_anos(investimento_rs, economia_liquida_ano_rs):
    """Retorno simples: investimento / economia líquida anual (None se nunca se paga)."""
    if economia_liquida_ano_rs <= 0:
        return None
    return investimento_rs / economia_liquida_ano_rs


def co2_kg(kwh, fator_kg_por_kwh):
    return kwh * fator_kg_por_kwh


def agua_litros_mes(minutos_por_banho, banhos_por_dia, vazao_l_min, dias_mes=30):
    return minutos_por_banho * vazao_l_min * banhos_por_dia * dias_mes


# ----------------------------- cenários ---------------------------------------
def _cenario(cid, nome, renovavel, kwh_mes, minutos, p, perfil, tarifa, base, investimento=0.0,
             reducao=0.0, viavel=True, motivo=None):
    kwh_ano = kwh_mes * MESES
    custo_ano = custo_rs(kwh_ano, tarifa)
    manutencao = investimento * p.v("manutencao_solar_pct_ano") / 100.0
    economia_bruta = base["custo_ano"] - custo_ano
    economia_liquida = economia_bruta - manutencao
    horizonte = p.v("horizonte_anos")
    banhos_dia = perfil.pessoas * perfil.banhos_por_pessoa_dia
    agua_base = agua_litros_mes(perfil.minutos_por_banho, banhos_dia, p.v("vazao_chuveiro_l_min"), p.v("dias_mes"))
    agua_cen = agua_litros_mes(minutos, banhos_dia, p.v("vazao_chuveiro_l_min"), p.v("dias_mes"))
    return {
        "id": cid,
        "nome": nome,
        "renovavel": renovavel,
        "viavel": viavel,
        "motivo_inviavel": motivo,
        "minutos_por_banho": minutos,
        "reducao_eletrica_solar": reducao,
        "kwh_mes": kwh_mes,
        "kwh_ano": kwh_ano,
        "custo_mes_rs": custo_ano / MESES,
        "custo_ano_rs": custo_ano,
        "investimento_rs": investimento,
        "manutencao_ano_rs": manutencao,
        "economia_bruta_ano_rs": economia_bruta,
        "economia_liquida_ano_rs": economia_liquida,
        "payback_anos": payback_anos(investimento, economia_liquida) if investimento > 0 else (0.0 if economia_liquida > 0 else None),
        "beneficio_liquido_horizonte_rs": economia_liquida * horizonte - investimento,
        "co2_evitado_kg_ano": co2_kg(base["kwh_ano"] - kwh_ano, p.v("fator_emissao_kg_co2_kwh")),
        "agua_economizada_l_mes": agua_base - agua_cen,
    }


def simular(perfil, p=None, reducao_solar=None, investimento_solar=None):
    """Compara 4 cenários para a MESMA necessidade (banho quente da família) em 12 meses:

    A0 situação atual (chuveiro elétrico) | A1 banho mais curto (economia por hábito)
    A2 aquecedor solar com apoio elétrico (renovável) | A3 = A1 + A2

    Devolve um dicionário com a entrada, as checagens e os cenários.
    """
    p = p or Parametros.padrao()
    perfil = validar(perfil)
    tarifa = perfil.tarifa_rs_kwh if perfil.tarifa_rs_kwh is not None else p.tarifa_padrao()
    s = p.v("reducao_solar_base") if reducao_solar is None else reducao_solar
    inv = p.v("investimento_solar_rs") if investimento_solar is None else investimento_solar
    if not (0.0 <= s < 1.0):
        raise EntradaInvalida("A redução com aquecedor solar deve estar entre 0 e 1.")
    if inv < 0:
        raise EntradaInvalida("O investimento não pode ser negativo.")

    banhos_dia = perfil.pessoas * perfil.banhos_por_pessoa_dia
    e0 = energia_mensal_kwh(perfil.potencia_w, perfil.minutos_por_banho, banhos_dia, p.v("dias_mes"))

    checagens = {"consumo_chuveiro_pct_da_conta": None, "alerta": None}
    if perfil.consumo_conta_kwh_mes is not None:
        fracao = e0 / perfil.consumo_conta_kwh_mes
        checagens["consumo_chuveiro_pct_da_conta"] = fracao
        if fracao > 1.0:
            raise EntradaInvalida(
                "O chuveiro estimado (%.0f kWh/mês) consumiria mais do que a conta toda (%.0f kWh/mês). "
                "Confira potência, minutos por banho e número de banhos." % (e0, perfil.consumo_conta_kwh_mes))
        if fracao > p.v("alerta_chuveiro_pct_da_conta"):
            checagens["alerta"] = (
                "O chuveiro estimado seria %.0f%% da sua conta, o que é alto. Se o seu chuveiro costuma ficar na "
                "posição 'verão' ou o banho é mais curto, o consumo real é menor e a economia também." % (fracao * 100))

    minutos_a1 = min(perfil.minutos_por_banho, p.v("minutos_por_banho_a1"))
    e1 = energia_mensal_kwh(perfil.potencia_w, minutos_a1, banhos_dia, p.v("dias_mes"))
    e2 = e0 * (1.0 - s)
    e3 = e1 * (1.0 - s)

    viavel_solar = perfil.pode_instalar and perfil.tem_sol_no_telhado
    motivo = None
    if not perfil.pode_instalar:
        motivo = "sem autorização/propriedade para instalar no telhado"
    elif not perfil.tem_sol_no_telhado:
        motivo = "telhado sem sol direto na maior parte do dia"

    base = {"custo_ano": custo_rs(e0 * MESES, tarifa), "kwh_ano": e0 * MESES}
    cenarios = [
        _cenario("A0", "Situação atual: chuveiro elétrico", False, e0, perfil.minutos_por_banho, p, perfil, tarifa, base),
        _cenario("A1", "Economia por hábito: banho mais curto", False, e1, minutos_a1, p, perfil, tarifa, base),
        _cenario("A2", "Aquecedor solar com apoio elétrico", True, e2, perfil.minutos_por_banho, p, perfil, tarifa, base,
                 investimento=inv, reducao=s, viavel=viavel_solar, motivo=motivo),
        _cenario("A3", "Banho mais curto + aquecedor solar", True, e3, minutos_a1, p, perfil, tarifa, base,
                 investimento=inv, reducao=s, viavel=viavel_solar, motivo=motivo),
    ]

    # Quem já adotou o banho curto (A1) ganha menos com o solar: retorno do solar SOBRE A1.
    a1, a3 = cenarios[1], cenarios[3]
    ganho_a3_sobre_a1 = (a1["custo_ano_rs"] - a3["custo_ano_rs"]) - a3["manutencao_ano_rs"]
    a3["economia_liquida_sobre_a1_ano_rs"] = ganho_a3_sobre_a1
    a3["payback_sobre_a1_anos"] = payback_anos(inv, ganho_a3_sobre_a1) if inv > 0 else None

    pmee = p.v("pmee_coletor_kwh_mes")
    checagens["capacidade_um_coletor_vs_demanda"] = pmee / e0 if e0 > 0 else None
    return {
        "entrada": asdict(perfil),
        "tarifa_rs_kwh": tarifa,
        "tarifa_foi_informada": perfil.tarifa_rs_kwh is not None,
        "consumo_base_mes_kwh": e0,
        "custo_base_mes_rs": e0 * tarifa,
        "reducao_solar": s,
        "investimento_solar_rs": inv,
        "horizonte_anos": p.v("horizonte_anos"),
        "checagens": checagens,
        "cenarios": cenarios,
    }


def cenario(resultado, cid):
    for c in resultado["cenarios"]:
        if c["id"] == cid:
            return c
    raise KeyError(cid)


def sensibilidade_payback_a2(perfil, p=None, tarifas=(0.74, 0.85, 1.10, 1.30),
                             investimentos=(3000, 4500, 6000), reducoes=(0.50, 0.66, 0.70)):
    """Tabela de retorno (anos) do aquecedor solar (A2) variando tarifa, investimento e redução."""
    p = p or Parametros.padrao()
    linhas = []
    for t in tarifas:
        for inv in investimentos:
            for r in reducoes:
                perfil_t = Perfil(**{**asdict(perfil), "tarifa_rs_kwh": t, "pode_instalar": True, "tem_sol_no_telhado": True})
                res = simular(perfil_t, p, reducao_solar=r, investimento_solar=inv)
                c = cenario(res, "A2")
                linhas.append({"tarifa_rs_kwh": t, "investimento_rs": inv, "reducao": r,
                               "economia_liquida_ano_rs": c["economia_liquida_ano_rs"],
                               "payback_anos": c["payback_anos"]})
    return linhas


def acumulado_liquido(resultado, anos):
    """Custo acumulado (investimento + energia + manutenção) de cada cenário ao longo dos anos."""
    series = {}
    for c in resultado["cenarios"]:
        series[c["id"]] = [c["investimento_rs"] + (c["custo_ano_rs"] + c["manutencao_ano_rs"]) * a for a in range(anos + 1)]
    return series
