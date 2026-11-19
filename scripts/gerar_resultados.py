"""Gera os resultados do cenário-base: CSVs em dados/, gráficos em docs/img/ e as tabelas dos
documentos docs/02, docs/03 e docs/05 (para que os números dos documentos sejam sempre os do código).

Uso (na raiz do repositório):   python scripts/gerar_resultados.py
Requer: matplotlib (pip install matplotlib). Os gráficos são opcionais: --sem-graficos.
"""
import csv
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from energia.calculos import Perfil, acumulado_liquido, cenario, sensibilidade_payback_a2, simular  # noqa: E402
from energia.parametros import Parametros  # noqa: E402
from energia.recomendacao import LIMITACOES, _fmt_num, _fmt_rs  # noqa: E402

DADOS = os.path.join(RAIZ, "dados")
DOCS = os.path.join(RAIZ, "docs")
IMG = os.path.join(DOCS, "img")
TARIFA_BASE = 1.10      # R$/kWh (média estimada 2026 com tributos, arredondada: 0,849 / 0,771 = 1,1012)
TARIFAS = (0.74, 0.85, 1.10, 1.30)
INVESTIMENTOS = (3000, 4500, 6000)
REDUCOES = (0.50, 0.66, 0.70)

# paleta categórica validada (slots 1-4) e tokens de tinta
AZUL, LARANJA, AQUA, AMARELO = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
TINTA, TINTA2, GRADE, SUPERFICIE = "#0b0b0b", "#52514e", "#e3e2de", "#fcfcfb"


def md_tabela(cabecalho, linhas, alinhamento=None):
    alinhamento = alinhamento or ["---"] * len(cabecalho)
    out = ["| " + " | ".join(cabecalho) + " |", "| " + " | ".join(alinhamento) + " |"]
    for linha in linhas:
        out.append("| " + " | ".join(str(x) for x in linha) + " |")
    return "\n".join(out)


def anos(valor):
    return "nunca" if valor is None else _fmt_num(valor, 1) + " anos"


def escrever(caminho, texto):
    with open(caminho, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto.rstrip() + "\n")


def csv_cenarios(res):
    campos = ["id", "nome", "renovavel", "kwh_mes", "kwh_ano", "custo_mes_rs", "custo_ano_rs", "investimento_rs",
              "manutencao_ano_rs", "economia_bruta_ano_rs", "economia_liquida_ano_rs", "payback_anos",
              "beneficio_liquido_horizonte_rs", "co2_evitado_kg_ano", "agua_economizada_l_mes"]
    with open(os.path.join(DADOS, "resultado_cenario_base.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(campos)
        for c in res["cenarios"]:
            w.writerow([round(c[k], 4) if isinstance(c[k], float) else c[k] for k in campos])


def csv_sensibilidade(linhas):
    with open(os.path.join(DADOS, "sensibilidade_payback_a2.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tarifa_rs_kwh", "investimento_rs", "reducao_solar", "economia_liquida_ano_rs", "payback_anos"])
        for x in linhas:
            w.writerow([x["tarifa_rs_kwh"], x["investimento_rs"], x["reducao"], round(x["economia_liquida_ano_rs"], 2),
                        "" if x["payback_anos"] is None else round(x["payback_anos"], 2)])


def csv_acumulado(series, anos_h):
    with open(os.path.join(DADOS, "custo_acumulado_10_anos.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ano"] + list(series))
        for a in range(anos_h + 1):
            w.writerow([a] + [round(series[k][a], 2) for k in series])


# ----------------------------------------------------------------------------- gráficos
def graficos(res, series, p):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter

    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": TINTA, "axes.labelcolor": TINTA2,
                         "xtick.color": TINTA2, "ytick.color": TINTA2, "axes.edgecolor": GRADE,
                         "figure.facecolor": SUPERFICIE, "axes.facecolor": SUPERFICIE, "savefig.facecolor": SUPERFICIE})
    milhar = FuncFormatter(lambda v, _: _fmt_num(v))

    def base_ax(w=7.2, h=3.9):
        fig, ax = plt.subplots(figsize=(w, h), dpi=200)
        for lado in ("top", "right", "left"):
            ax.spines[lado].set_visible(False)
        ax.spines["bottom"].set_color(GRADE)
        ax.grid(axis="y", color=GRADE, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.tick_params(length=0)
        return fig, ax

    # Fig 1 - custo anual de energia por alternativa
    fig, ax = base_ax()
    nomes = ["A0\nChuveiro atual", "A1\nBanho de 6 min", "A2\nSolar + apoio", "A3\nBanho curto + solar"]
    valores = [c["custo_ano_rs"] for c in res["cenarios"]]
    barras = ax.bar(range(4), valores, width=0.42, color=AZUL)
    for i, (b, v) in enumerate(zip(barras, valores)):
        ax.text(b.get_x() + b.get_width() / 2, v + 25, _fmt_rs(v).replace("R$ ", "R$"), ha="center", va="bottom", fontsize=9, color=TINTA)
        if i > 0:
            eco = res["cenarios"][0]["custo_ano_rs"] - v
            ax.text(b.get_x() + b.get_width() / 2, v / 2, "-" + _fmt_rs(eco).replace("R$ ", "R$"), ha="center", va="center", fontsize=8.5, color="white")
    ax.set_xticks(range(4))
    ax.set_xticklabels(nomes, fontsize=8.5)
    ax.yaxis.set_major_formatter(milhar)
    ax.set_ylabel("R$ por ano (só energia elétrica)", fontsize=9)
    ax.set_title("Custo anual de energia do banho quente (família de 4, tarifa R$ %s/kWh)" % _fmt_num(TARIFA_BASE, 2), fontsize=10, loc="left", color=TINTA)
    ax.set_ylim(0, max(valores) * 1.15)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "fig1_custo_anual.png"))
    plt.close(fig)

    # Fig 2 - custo acumulado (investimento + energia + manutenção)
    fig, ax = base_ax(7.2, 4.2)
    cores = {"A0": AZUL, "A1": LARANJA, "A2": AQUA, "A3": AMARELO}
    rotulos = {"A0": "A0 chuveiro atual", "A1": "A1 banho de 6 min", "A2": "A2 solar + apoio", "A3": "A3 banho curto + solar"}
    h = res["horizonte_anos"]
    for cid, serie in series.items():
        ax.plot(range(h + 1), serie, color=cores[cid], linewidth=2, solid_capstyle="round")
    # rótulos diretos na ponta (com separação mínima para não colidir)
    pontas = sorted(((series[c][-1], c) for c in series))
    ajustados, minimo = [], 520
    for y, cid in pontas:
        if ajustados and y - ajustados[-1][0] < minimo:
            y = ajustados[-1][0] + minimo
        ajustados.append((y, cid))
    for y, cid in ajustados:
        ax.text(h + 0.15, y, rotulos[cid], color=TINTA, fontsize=8.5, va="center")
    pb = cenario(res, "A2")["payback_anos"]
    if pb and pb <= h:
        ya = series["A0"][0] + (series["A0"][1] - series["A0"][0]) * pb
        ax.vlines(pb, 0, ya, colors=TINTA2, linestyles=(0, (2, 3)), linewidth=1)
        ax.plot([pb], [ya], marker="o", markersize=8, color=AQUA, markeredgecolor=SUPERFICIE, markeredgewidth=2, zorder=5)
        ax.text(pb + 0.12, 600, "retorno do solar (A2 x A0)\n≈ %s" % anos(pb), fontsize=8.5, color=TINTA2, va="bottom")
    ax.set_xlim(0, h + 3.4)
    ax.set_ylim(0, max(s[-1] for s in series.values()) * 1.1)
    ax.set_xticks(range(0, h + 1, 2))
    ax.yaxis.set_major_formatter(milhar)
    ax.set_xlabel("anos", fontsize=9)
    ax.set_ylabel("R$ acumulados (investimento + energia + manutenção)", fontsize=8.5)
    ax.set_title("Custo acumulado em 10 anos para a mesma necessidade (banho quente)", fontsize=10, loc="left", color=TINTA)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "fig2_custo_acumulado.png"))
    plt.close(fig)

    # Fig 3 - sensibilidade do retorno do solar à tarifa e ao investimento
    fig, ax = base_ax(7.2, 4.0)
    tarifas = [0.60 + 0.05 * i for i in range(0, 17)]  # 0,60 .. 1,40
    for inv, cor in zip(INVESTIMENTOS, (AZUL, LARANJA, AQUA)):
        ys = []
        for t in tarifas:
            r = simular(Perfil(tarifa_rs_kwh=t), p, investimento_solar=inv)
            ys.append(cenario(r, "A2")["payback_anos"])
        ax.plot(tarifas, ys, color=cor, linewidth=2, label="investimento %s" % _fmt_rs(inv).replace(",00", ""))
        ax.text(tarifas[-1] + 0.01, ys[-1], _fmt_rs(inv).replace(",00", ""), fontsize=8.5, va="center", color=TINTA)
    ax.axhline(p.v("horizonte_anos"), color=TINTA2, linewidth=1, linestyle=(0, (2, 3)))
    ax.text(1.0, p.v("horizonte_anos") + 0.4, "horizonte de %d anos (vida útil mínima do boiler)" % p.v("horizonte_anos"), fontsize=8.5, color=TINTA2)
    virgula = FuncFormatter(lambda v, _: ("%g" % round(v, 2)).replace(".", ","))
    ax.xaxis.set_major_formatter(virgula)
    ax.yaxis.set_major_formatter(virgula)
    ax.set_xlim(0.58, 1.52)
    ax.set_ylim(0, 22)
    ax.set_xlabel("valor do kWh na conta (R$)", fontsize=9)
    ax.set_ylabel("retorno do solar (anos)", fontsize=9)
    ax.set_title("Retorno do aquecedor solar (A2) x tarifa e investimento (redução 66%, família de 4)", fontsize=10, loc="left", color=TINTA)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "fig3_sensibilidade_retorno.png"))
    plt.close(fig)


# ----------------------------------------------------------------------------- documentos
def doc_parametros(p):
    linhas = []
    for nome, it in p.parametros.items():
        valor = _fmt_num(it["valor"], 3).rstrip("0").rstrip(",") if isinstance(it["valor"], float) else _fmt_num(it["valor"])
        linhas.append(["`%s`" % nome, valor, it["unidade"], it["tipo"].upper(), it["origem"], ", ".join(it["ref"]) or "-"])
    tabela = md_tabela(["Parâmetro", "Valor", "Unidade", "Tipo", "Origem / justificativa", "Ref."], linhas)
    return """# 2. Dados utilizados, origem e premissas

Todos os números do módulo estão em [`dados/parametros.json`](../dados/parametros.json), cada um com **valor, unidade, tipo e origem**.
Para trocar uma premissa basta editar o arquivo; o código, os testes e esta tabela usam o mesmo JSON.

* **PÚBLICO**: valor lido de uma fonte pública (referência indicada, consultada em 18/11/2026).
* **ESTIMADO / PREMISSA**: valor assumido pela equipe com justificativa. **São estimativas, não medições.**
* **CALCULADO**: obtido a partir de dados públicos por conta simples (descrita na origem).

**Período de referência:** 12 meses (ano típico); retorno do investimento em 10 anos. **Moeda:** R$ (reais de 2026, sem inflação).
**Unidades:** potência em W, energia em kWh, tarifa em R$/kWh, tempo em minutos, emissões em kg de CO2.

## 2.1 Tabela de parâmetros

""" + tabela + """

## 2.2 O que NÃO é dado real (e por quê)

1. **Perfil do cenário de referência** (4 pessoas, 1 banho por pessoa por dia, 8 min): é uma família hipotética, coerente com o estudo R2 e com a faixa mais comum de tempo de banho da pesquisa R4. Cada pessoa pode informar o seu.
2. **Investimento do aquecedor solar (R$ 4.500)**: ponto médio da faixa publicada pelo IDEC (R$ 3.000 a R$ 6.000). Orçamentos reais variam.
3. **Redução de 66% do consumo elétrico do chuveiro**: vem de **um estudo de caso** (R2) e fica entre o cenário conservador da equipe (50%) e a promessa do fabricante (70%).
4. **Manutenção de 1% ao ano**: reserva da equipe; as fontes só dizem que a manutenção é pouca.
5. **Tarifa**: valor médio nacional estimado para 2026. A tarifa da sua distribuidora (e descontos como a tarifa social) muda o resultado, por isso o assistente pergunta o valor do kWh da sua conta.

## 2.3 Fórmulas e constantes físicas

Não há constante física "escondida": o modelo usa apenas energia = potência x tempo (Wh = W x h). A comparação com o calor necessário para esquentar a água (m x c x ΔT) foi substituída pelo teste de ordem de grandeza com a energia por coletor da etiqueta PBE/Inmetro (ver `docs/03_calculos_e_comparacao.md`, seção 3.7).
"""


def doc_referencias(p):
    linhas = []
    for rid, r in p.referencias.items():
        linhas.append("**[%s]** %s  \n<%s>  \nAcesso em %s.  \n*O que usamos:* %s\n" % (rid, r["citacao"], r["url"], r["acesso"], r["usamos"]))
    return """# 5. Referências

Todas as fontes abaixo foram **abertas e lidas em 18/11/2026**. Os valores citados foram conferidos nas páginas indicadas; as
fontes secundárias (notícia, boletim, loja) estão sinalizadas e devem ser conferidas no órgão oficial antes de decisões reais.

""" + "\n".join(linhas) + """
## Onde conferir os valores atuais (não usado nos cálculos)

* Tarifa e bandeira da sua distribuidora: conta de luz e site da ANEEL (<https://www.gov.br/aneel>).
* Etiqueta de eficiência de coletores solares: tabelas PBE/Inmetro (<https://www.gov.br/inmetro>).

## Limitações das fontes

* [R2] é um estudo acadêmico com premissas próprias (2 banhos de 15 min por pessoa, tarifa de R$ 0,41/kWh, preços de 2020); usamos dele só a **proporção** de redução e a ordem de grandeza do investimento.
* [R3] é material de fabricante (a promessa de 70% é propaganda); usado apenas como limite superior e para a energia da etiqueta PBE.
* [R6] e [R7] são fontes secundárias; [R7] traz valor médio **nacional**.
* [R4]: valores lidos das tabelas 362 a 367 do estado de São Paulo (PPH 2019); o PDF é público e deve ser aberto para conferência.
* [R8]: apenas 4 meses de 2025; não representa a média anual.
"""


def doc_calculos(res, series, p, sens, sens_pessoas, sens_reducao):
    a0, a1, a2, a3 = (cenario(res, c) for c in ("A0", "A1", "A2", "A3"))
    e = res["entrada"]
    t = res["tarifa_rs_kwh"]
    h = res["horizonte_anos"]
    s = res["reducao_solar"]
    inv = res["investimento_solar_rs"]
    passo = []
    passo.append("**A0 (situação atual)**  \n`E = 5,5 kW x (8/60 h) x 4 banhos/dia x 30 dias = %s kWh/mês`  ->  `x 12 = %s kWh/ano`  ->  `x R$ %s = %s por ano`"
                 % (_fmt_num(a0["kwh_mes"]), _fmt_num(a0["kwh_ano"]), _fmt_num(t, 2), _fmt_rs(a0["custo_ano_rs"])))
    passo.append("**A1 (banho de 6 minutos)**  \n`E = 5,5 kW x (6/60 h) x 4 x 30 = %s kWh/mês`  ->  `%s kWh/ano`  ->  `%s por ano`; economia = %s - %s = **%s por ano** (25%%)."
                 % (_fmt_num(a1["kwh_mes"]), _fmt_num(a1["kwh_ano"]), _fmt_rs(a1["custo_ano_rs"]), _fmt_rs(a0["custo_ano_rs"]), _fmt_rs(a1["custo_ano_rs"]), _fmt_rs(a1["economia_bruta_ano_rs"])))
    passo.append("**A2 (aquecedor solar com apoio elétrico)**  \n`kWh/ano = 1.056 x (1 - 0,66) = %s`  ->  `custo = %s por ano`; economia bruta = %s; manutenção = 1%% x %s = %s; **economia líquida = %s por ano**; **retorno = %s / %s = %s**."
                 % (_fmt_num(a2["kwh_ano"], 2), _fmt_rs(a2["custo_ano_rs"]), _fmt_rs(a2["economia_bruta_ano_rs"]), _fmt_rs(inv), _fmt_rs(a2["manutencao_ano_rs"]),
                    _fmt_rs(a2["economia_liquida_ano_rs"]), _fmt_rs(inv), _fmt_rs(a2["economia_liquida_ano_rs"]), anos(a2["payback_anos"])))
    passo.append("**A3 (A1 + A2)**  \n`kWh/ano = 792 x (1 - 0,66) = %s`  ->  `custo = %s por ano`; economia líquida sobre A0 = %s por ano (retorno %s). **Sobre A1** (quem já adotou o banho curto) a economia líquida do solar é %s por ano e o retorno sobe para **%s**."
                 % (_fmt_num(a3["kwh_ano"], 2), _fmt_rs(a3["custo_ano_rs"]), _fmt_rs(a3["economia_liquida_ano_rs"]), anos(a3["payback_anos"]),
                    _fmt_rs(a3["economia_liquida_sobre_a1_ano_rs"]), anos(a3["payback_sobre_a1_anos"])))

    tab = md_tabela(
        ["Alternativa", "kWh/ano", "Custo de energia/ano", "Investimento", "Economia líquida/ano", "Retorno", "Ganho líquido em %d anos" % h, "CO2 evitado (kg/ano)", "Água economizada (L/mês)"],
        [[c["id"] + " " + c["nome"] + (" (renovável)" if c["renovavel"] else ""), _fmt_num(c["kwh_ano"]), _fmt_rs(c["custo_ano_rs"]),
          _fmt_rs(c["investimento_rs"]) if c["investimento_rs"] else "-", _fmt_rs(c["economia_liquida_ano_rs"]) if c["id"] != "A0" else "-",
          "-" if c["id"] == "A0" else ("imediato" if c["id"] == "A1" else anos(c["payback_anos"])),
          _fmt_rs(c["beneficio_liquido_horizonte_rs"]) if c["id"] != "A0" else "-", _fmt_num(c["co2_evitado_kg_ano"], 1), _fmt_num(c["agua_economizada_l_mes"])]
         for c in res["cenarios"]])

    # sensibilidade
    por_tarifa = {}
    for x in sens:
        if x["reducao"] == 0.66:
            por_tarifa.setdefault(x["tarifa_rs_kwh"], {})[x["investimento_rs"]] = x["payback_anos"]
    tab_sens = md_tabela(["Valor do kWh"] + [_fmt_rs(i).replace(",00", "") for i in INVESTIMENTOS],
                         [[_fmt_rs(t_).replace("R$ ", "R$ ")] + [anos(por_tarifa[t_][i]) for i in INVESTIMENTOS] for t_ in TARIFAS])
    por_red = {}
    for x in sens:
        if x["tarifa_rs_kwh"] == 1.10 and x["investimento_rs"] == 4500:
            por_red[x["reducao"]] = x["payback_anos"]
    tab_red = md_tabela(["Redução do consumo do chuveiro"] + ["%d%%" % round(r * 100) for r in REDUCOES],
                        [["Retorno (investimento R$ 4.500, kWh a R$ 1,10)"] + [anos(por_red[r]) for r in REDUCOES]])
    tab_pes = md_tabela(["Pessoas na casa", "Chuveiro (kWh/mês)", "Custo/ano (A0)", "Retorno do solar (A2)"],
                        [[str(n), _fmt_num(x["kwh"]), _fmt_rs(x["custo"]), anos(x["payback"])] for n, x in sens_pessoas.items()])
    ref_idec = "O estudo do IDEC [R1] indica retorno entre 2 e 7 anos; o resultado-base (%s) cai dentro dessa faixa, perto do limite superior." % anos(a2["payback_anos"])

    return """# 3. Cálculos e comparação das alternativas

## 3.1 Necessidade, período e cenário de referência

* **Necessidade (a mesma para todas as alternativas):** água quente para o banho de uma família de %d pessoas.
* **Período de referência comum:** 12 meses; o retorno do investimento é avaliado em um horizonte de %d anos.
* **Cenário-base:** %d pessoas, %s banho/pessoa/dia, %s min por banho, chuveiro elétrico de 5.500 W, kWh a %s (tarifa média estimada 2026 com tributos, arredondada), bandeira verde.
* **Alternativas:** A0 situação atual (comparação) · **A1** banho mais curto (economia por hábito) · **A2** aquecedor solar com apoio elétrico (**fonte renovável**) · **A3** A1 + A2.

## 3.2 Fórmulas

```text
E_mes  [kWh]  = P [kW] x t_banho [h] x banhos_por_dia x 30
custo  [R$]   = E x tarifa [R$/kWh]
A1: mesma fórmula com t_banho = min(t_atual, 6 min)
A2: E_A2 = E_A0 x (1 - r)        r = redução com solar e apoio elétrico (0,66)
manutenção    = 1%% x investimento por ano
economia líquida = (custo_A0 - custo_alternativa) - manutenção
retorno [anos]   = investimento / economia líquida por ano
CO2 evitado [kg] = (E_A0 - E_alternativa) x fator de emissão (0,024725 kg/kWh)
água economizada [L/mês] = (t_A0 - t_A1) x vazão (5 L/min) x banhos_por_dia x 30
```

## 3.3 Cálculo passo a passo (cenário-base)

""" % (e["pessoas"], h, e["pessoas"], _fmt_num(e["banhos_por_pessoa_dia"], 1), _fmt_num(e["minutos_por_banho"]), _fmt_rs(t)) + "\n\n".join(passo) + """

## 3.4 Resultado da comparação (12 meses)

""" + tab + """

![Custo anual de energia](img/fig1_custo_anual.png)

![Custo acumulado em 10 anos](img/fig2_custo_acumulado.png)

**Leitura:** o banho de 6 minutos (A1) é o que mais rende por real investido (custo zero), mas muda o hábito. O aquecedor solar (A2) mantém o banho
como é e economiza mais por ano, porém exige investimento e só se paga em ≈ %s. Juntos (A3), o solar rende menos sobre quem já encurtou o banho (retorno de ≈ %s sobre A1).
%s

## 3.5 Sensibilidade: o que muda o resultado

O retorno do solar (A2) é **muito sensível à tarifa**. Retorno (anos), redução de 66%%, família de 4:

""" % (anos(a2["payback_anos"]), anos(a3["payback_sobre_a1_anos"]), ref_idec) + tab_sens + """

![Sensibilidade do retorno](img/fig3_sensibilidade_retorno.png)

Efeito da **redução** efetivamente obtida (tarifa R$ 1,10; investimento R$ 4.500):

""" + tab_red + """

Efeito do **tamanho da família** (tarifa R$ 1,10; investimento R$ 4.500; redução de 66%; 8 min; mesmo sistema):

""" + tab_pes + """

> Conclusão honesta: com tarifa baixa (R$ 0,74/kWh) e investimento alto, o solar **não** se paga dentro de 10 anos para uma família de 4;
> para famílias pequenas o retorno é bem mais longo. Por isso o assistente pede a tarifa da conta, o número de pessoas e o tempo de banho.

## 3.6 Teste de coerência com a conta de luz

Se a pessoa informa o consumo total da conta (kWh/mês), o assistente compara com o chuveiro estimado: se passa de 60%% da conta, mostra alerta
(provável posição "verão" ou banho curto); se o chuveiro estimado passa de 100%% da conta, o dado é recusado como incoerente.
No cenário-base, 88 kWh/mês correspondem a ≈ 29%% de uma conta de 300 kWh.

## 3.7 Teste de ordem de grandeza do coletor (PBE/Inmetro)

Um coletor classe A da linha consultada [R3] declara **121,4 kWh/mês**. A demanda do chuveiro no cenário-base é **88 kWh/mês**, portanto
um coletor produz ≈ **%s** vezes a demanda. Isso mostra que a **energia disponível não é o fator limitante**; o limite da economia são dias
nublados, uso do apoio elétrico e perdas, motivo pelo qual adotamos redução de 66%% (e não 100%%). O dimensionamento final cabe a um instalador.

## 3.8 Limitações dos cálculos

""" % _fmt_num(res["checagens"]["capacidade_um_coletor_vs_demanda"], 1) + "\n".join("* " + l for l in LIMITACOES) + """
* Não há desconto a valor presente nem reajuste de tarifa; ambos mudariam o retorno (reajustes tendem a encurtá-lo; juros altos, a alongá-lo).
* O modelo considera um chuveiro elétrico sempre na potência nominal; na posição "verão" o consumo real é menor.

## 3.9 Como reproduzir

```bash
python scripts/gerar_resultados.py     # recria CSVs, gráficos e as tabelas deste documento
python -m unittest discover -s tests   # confere as fórmulas com valores calculados à mão
```

Arquivos gerados em [`dados/`](../dados): `resultado_cenario_base.csv`, `sensibilidade_payback_a2.csv`, `custo_acumulado_10_anos.csv`.
"""


def main(sem_graficos=False):
    os.makedirs(IMG, exist_ok=True)
    p = Parametros.padrao()
    res = simular(Perfil(tarifa_rs_kwh=TARIFA_BASE), p)
    series = acumulado_liquido(res, res["horizonte_anos"])
    sens = sensibilidade_payback_a2(Perfil(), p, tarifas=TARIFAS, investimentos=INVESTIMENTOS, reducoes=REDUCOES)
    sens_pessoas = {}
    for n in (2, 3, 4, 5):
        r = simular(Perfil(pessoas=n, tarifa_rs_kwh=TARIFA_BASE), p)
        sens_pessoas[n] = {"kwh": r["consumo_base_mes_kwh"], "custo": cenario(r, "A0")["custo_ano_rs"], "payback": cenario(r, "A2")["payback_anos"]}

    csv_cenarios(res)
    csv_sensibilidade(sens)
    csv_acumulado(series, res["horizonte_anos"])
    if not sem_graficos:
        graficos(res, series, p)
    escrever(os.path.join(DOCS, "02_dados_e_premissas.md"), doc_parametros(p))
    escrever(os.path.join(DOCS, "03_calculos_e_comparacao.md"), doc_calculos(res, series, p, sens, sens_pessoas, None))
    escrever(os.path.join(DOCS, "05_referencias.md"), doc_referencias(p))

    print("Cenário-base (família de 4, 8 min, tarifa R$ %.2f/kWh):" % TARIFA_BASE)
    for c in res["cenarios"]:
        print("  %s  %7.1f kWh/ano  %9s/ano  invest. %9s  retorno %s" % (
            c["id"], c["kwh_ano"], _fmt_rs(c["custo_ano_rs"]), _fmt_rs(c["investimento_rs"]), anos(c["payback_anos"]) if c["id"] > "A1" else "-"))
    print("Arquivos gerados em dados/ e docs/ (02, 03, 05) e docs/img/.")


if __name__ == "__main__":
    main(sem_graficos="--sem-graficos" in sys.argv)
