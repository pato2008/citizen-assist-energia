"""Assistente de energia em linha de comando (módulo Energia do Citizen Assist AI).

Conversa simples em português: pergunta o perfil do banho da família, calcula, compara
alternativas e responde com recomendações, referências e limitações. Trata entradas
inválidas sem travar e NÃO pede dados pessoais (nome, endereço, CPF, nº de cliente).

Uso:
    python assistente_energia.py            # conversa interativa
    python assistente_energia.py --demo     # demonstração automática (usada no vídeo)
    python assistente_energia.py --json --pessoas 4 --minutos 8     # saída JSON (integração)
"""
import argparse
import sys

from .api import consultar_energia
from .calculos import EntradaInvalida, Perfil, ler_numero
from .parametros import Parametros
from .recomendacao import AVISO, LIMITACOES, _fmt_num, _fmt_rs

LARGURA = 78
MENU = """O que você quer fazer?
  1) Analisar o gasto do chuveiro elétrico e comparar alternativas (solar x hábito)
  2) De onde vêm os números? (fontes)
  3) Limitações deste assistente
  4) Como funciona
  0) Sair"""

PALAVRAS = (
    ("0", ("sair", "tchau", "encerrar", "fechar")),
    ("2", ("fonte", "referên", "referen", "origem", "de onde")),
    ("3", ("limita", "garant", "confi", "erro", "certeza")),
    ("4", ("como funciona", "ajuda", "help", "explica")),
    ("1", ("chuveiro", "conta", "gasta", "gasto", "econom", "solar", "vale", "compensa", "renov", "energia", "luz", "banho")),
)


def interpretar_menu(texto):
    """Escolhe a opção do menu a partir de um número ou de palavras-chave."""
    t = texto.strip().lower()
    if t in ("0", "1", "2", "3", "4"):
        return t
    for opcao, palavras in PALAVRAS:
        if any(w in t for w in palavras):
            return opcao
    return None


def _linha(char="=", n=LARGURA):
    return char * n


NOMES_CURTOS = {
    "A0": "A0 Chuveiro elétrico (situação atual)",
    "A1": "A1 Banho mais curto (hábito)",
    "A2": "A2 Aquecedor solar + apoio elétrico (R)",
    "A3": "A3 Banho curto + aquecedor solar (R)",
}


def tabela_comparacao(resultado):
    linhas = ["%-44s %8s %10s %10s %9s" % ("Alternativa (mesma necessidade: banho quente)", "kWh/ano", "Custo/ano", "Invest.", "Retorno")]
    for c in resultado["cenarios"]:
        nome = NOMES_CURTOS[c["id"]]
        if c["id"] == "A0":
            retorno = "-"
        elif c["id"] == "A1":
            retorno = "imediato" if c["economia_bruta_ano_rs"] > 0.5 else "-"
        elif not c["viavel"]:
            retorno = "inviável"
        else:
            retorno = "%s anos" % _fmt_num(c["payback_anos"], 1) if c["payback_anos"] else "nunca"
        invest = _fmt_rs(c["investimento_rs"]) if c["investimento_rs"] else "R$ 0"
        linhas.append("%-44s %8s %10s %10s %9s" % (nome[:44], _fmt_num(c["kwh_ano"]), _fmt_rs(c["custo_ano_rs"]).replace("R$ ", "R$"),
                                                   invest.replace("R$ ", "R$"), retorno))
    linhas.append("(R) = fonte renovável (energia solar). Retorno = investimento / economia líquida por ano.")
    return linhas


def texto_resultado(resposta, p):
    """Linhas de texto para o usuário a partir da resposta de consultar_energia()."""
    if resposta["erro"]:
        return ["Não consegui calcular: " + resposta["erro"]]
    r = resposta["resultado"]
    e = r["entrada"]
    saida = [_linha("-"), "SEU PERFIL (valores informados ou do cenário de referência)"]
    saida.append("- %d pessoa(s), %s banho(s) por pessoa por dia, %s min por banho, chuveiro de %s W" % (
        e["pessoas"], _fmt_num(e["banhos_por_pessoa_dia"], 2), _fmt_num(e["minutos_por_banho"]), _fmt_num(e["potencia_w"])))
    origem_tarifa = "informada por você" if r["tarifa_foi_informada"] else "média estimada 2026 com tributos (R7)"
    saida.append("- Valor do kWh: %s (%s)" % (_fmt_rs(r["tarifa_rs_kwh"]), origem_tarifa))
    saida.append("")
    saida.append("RESULTADO PARA 12 MESES")
    saida.append("- Seu chuveiro elétrico consome ≈ %s kWh por mês, cerca de %s por mês." % (
        _fmt_num(r["consumo_base_mes_kwh"]), _fmt_rs(r["custo_base_mes_rs"])))
    alerta = r["checagens"].get("alerta")
    if alerta:
        saida.append("- ATENÇÃO: " + alerta)
    saida.append("")
    saida.extend(tabela_comparacao(r))
    saida.append("")
    saida.append("RECOMENDAÇÕES")
    for i, rec in enumerate(resposta["recomendacoes"], 1):
        saida.append("%d. %s" % (i, rec["titulo"]))
        saida.append("   " + rec["texto"])
    saida.append("")
    saida.append("REFERÊNCIAS USADAS: " + ", ".join(resposta["referencias"].keys()) + " (opção 2 do menu mostra a lista completa)")
    saida.append("LIMITES: " + LIMITACOES[0])
    saida.append("         " + LIMITACOES[1])
    saida.append(AVISO)
    saida.append(_linha("-"))
    return saida


def texto_fontes(p):
    saida = ["FONTES (consultadas em 18/11/2026):"]
    for rid in sorted(p.referencias):
        ref = p.referencias[rid]
        saida.append("[%s] %s" % (rid, ref["citacao"]))
        saida.append("     %s" % ref["url"])
        saida.append("     Usamos: %s" % ref["usamos"])
    estimados = [k for k, v in p.parametros.items() if v["tipo"] in ("estimado", "premissa")]
    saida.append("")
    saida.append("Dados ESTIMADOS/PREMISSAS (não são medições): " + ", ".join(sorted(estimados)))
    saida.append("Cada parâmetro tem origem e unidade em dados/parametros.json.")
    return saida


def texto_limitacoes():
    return ["LIMITAÇÕES:"] + ["- " + t for t in LIMITACOES] + ["", AVISO]


def texto_como_funciona():
    return [
        "COMO FUNCIONA: energia (kWh) = potência (kW) x tempo (h). Para o chuveiro: potência x minutos por banho x banhos por dia x 30.",
        "Comparamos a MESMA necessidade (banho quente da família) em 12 meses: A0 atual, A1 banho mais curto,",
        "A2 aquecedor solar com apoio elétrico (renovável) e A3 = A1 + A2. Custo = kWh x tarifa; retorno = investimento / economia líquida.",
        "Não pedimos nome, endereço, CPF nem número de cliente. Você só informa números sobre o banho e a conta.",
    ]


class Assistente:
    def __init__(self, entrada=input, saida=print, parametros=None, max_tentativas=3):
        self.entrada = entrada
        self.saida = saida
        self.p = parametros or Parametros.padrao()
        self.max_tentativas = max_tentativas

    # ---- utilidades de diálogo ----
    def dizer(self, linhas):
        if isinstance(linhas, str):
            linhas = [linhas]
        for linha in linhas:
            self.saida(linha)

    def perguntar_numero(self, pergunta, campo, padrao=None, opcional=False):
        """Pergunta um número validando faixa; Enter usa o padrão. Repete até acertar (ou desiste)."""
        for _ in range(self.max_tentativas):
            sufixo = " [Enter = %g]" % padrao if padrao is not None else (" [Enter para pular]" if opcional else "")
            resposta = self.entrada("%s%s: " % (pergunta, sufixo)).strip()
            if resposta == "":
                return padrao if padrao is not None else None
            try:
                valor = ler_numero(resposta, campo)
                return int(valor) if campo == "pessoas" and valor == int(valor) else valor
            except EntradaInvalida as erro:
                self.dizer("  ! " + str(erro))
        if padrao is None:
            self.dizer("  Vou pular esta pergunta e continuar.")
        else:
            self.dizer("  Vou usar o valor de referência (%g) para continuar." % padrao)
        return padrao

    def perguntar_sim_nao(self, pergunta, padrao=True):
        for _ in range(self.max_tentativas):
            resposta = self.entrada("%s (s/n) [Enter = %s]: " % (pergunta, "s" if padrao else "n")).strip().lower()
            if resposta == "":
                return padrao
            if resposta in ("s", "sim"):
                return True
            if resposta in ("n", "nao", "não"):
                return False
            self.dizer("  ! Responda com s (sim) ou n (não).")
        return padrao

    # ---- fluxos ----
    def coletar_perfil(self):
        d = self.p
        self.dizer(["", "Vou fazer algumas perguntas sobre o banho da sua família (só números, sem dados pessoais).",
                    "Se não souber, aperte Enter para usar o valor de referência."])
        pessoas = self.perguntar_numero("Quantas pessoas moram na casa", "pessoas", d.v("pessoas"))
        minutos = self.perguntar_numero("Quantos minutos dura um banho, em média", "minutos_por_banho", d.v("minutos_por_banho"))
        banhos = self.perguntar_numero("Quantos banhos cada pessoa toma por dia", "banhos_por_pessoa_dia", d.v("banhos_por_pessoa_dia"))
        potencia = self.perguntar_numero("Potência do chuveiro em watts (está na etiqueta do chuveiro)", "potencia_w", d.v("potencia_chuveiro_w"))
        tarifa = self.perguntar_numero("Valor do kWh na sua conta de luz, em R$ (ex.: 1,10)", "tarifa_rs_kwh", None, opcional=True)
        conta = self.perguntar_numero("Consumo total do último mês na conta, em kWh", "consumo_conta_kwh_mes", None, opcional=True)
        pode = self.perguntar_sim_nao("A casa é sua ou você tem autorização para instalar equipamento no telhado?", True)
        sol = self.perguntar_sim_nao("O telhado/laje recebe sol direto na maior parte do dia, sem sombra de prédios ou árvores?", True)
        return Perfil(pessoas=pessoas, minutos_por_banho=minutos, banhos_por_pessoa_dia=banhos, potencia_w=potencia,
                      tarifa_rs_kwh=tarifa, consumo_conta_kwh_mes=conta, pode_instalar=pode, tem_sol_no_telhado=sol)

    def analisar(self):
        perfil = self.coletar_perfil()
        resposta = consultar_energia(perfil, self.p)
        self.dizer(texto_resultado(resposta, self.p))

    def executar(self):
        self.dizer([_linha(), "Citizen Assist AI - módulo ENERGIA (água quente do banho e conta de luz)", _linha(), AVISO, ""])
        while True:
            self.dizer(["", MENU])
            try:
                escolha = self.entrada("Digite o número ou escreva sua pergunta: ")
            except EOFError:
                break
            opcao = interpretar_menu(escolha)
            if opcao == "0":
                self.dizer("Até mais! Lembre-se: são estimativas, confira os valores da sua conta.")
                break
            if opcao == "1":
                self.analisar()
            elif opcao == "2":
                self.dizer(texto_fontes(self.p))
            elif opcao == "3":
                self.dizer(texto_limitacoes())
            elif opcao == "4":
                self.dizer(texto_como_funciona())
            else:
                self.dizer("Não entendi. Tente um número do menu ou palavras como 'solar', 'chuveiro', 'fontes' ou 'limitações'.")


def demo():
    """Conversa de demonstração (inclui entradas inválidas) - usada no vídeo."""
    roteiro = iter([
        "quanto gasta meu chuveiro?",      # texto livre -> opção 1
        "abc",                              # pessoas inválido (texto)
        "4",                                # pessoas
        "90",                               # minutos inválido (fora da faixa)
        "8",                                # minutos
        "",                                 # banhos por pessoa (padrão)
        "",                                 # potência (padrão)
        "1,10",                             # tarifa
        "300",                              # consumo total da conta
        "s",                                # pode instalar
        "s",                                # tem sol
        "fontes",                           # opção 2
        "limitações",                       # opção 3
        "sair",
    ])

    def entrada(pergunta):
        resposta = next(roteiro)
        print("%s%s" % (pergunta, resposta))
        return resposta

    Assistente(entrada=entrada).executar()


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="Citizen Assist AI - módulo Energia (banho quente e conta de luz)")
    ap.add_argument("--demo", action="store_true", help="demonstração automática")
    ap.add_argument("--json", action="store_true", help="imprime o resultado em JSON (integração)")
    ap.add_argument("--pessoas", type=str)
    ap.add_argument("--minutos", type=str, help="minutos por banho")
    ap.add_argument("--banhos", type=str, help="banhos por pessoa por dia")
    ap.add_argument("--potencia", type=str, help="potência do chuveiro (W)")
    ap.add_argument("--tarifa", type=str, help="valor do kWh na conta (R$)")
    ap.add_argument("--conta-kwh", type=str, help="consumo mensal da conta (kWh)")
    ap.add_argument("--sem-solar", action="store_true", help="não pode instalar aquecedor solar")
    args = ap.parse_args(argv)

    if args.demo:
        demo()
        return 0
    if args.json or any(v is not None for v in (args.pessoas, args.minutos, args.banhos, args.potencia, args.tarifa, args.conta_kwh)):
        import json
        dados = {"pessoas": args.pessoas, "minutos_por_banho": args.minutos, "banhos_por_pessoa_dia": args.banhos,
                 "potencia_w": args.potencia, "tarifa_rs_kwh": args.tarifa, "consumo_conta_kwh_mes": args.conta_kwh}
        dados = {k: v for k, v in dados.items() if v is not None}
        if args.sem_solar:
            dados["pode_instalar"] = False
        resposta = consultar_energia(dados)
        if args.json:
            print(json.dumps(resposta, ensure_ascii=False, indent=2))
        else:
            print("\n".join(texto_resultado(resposta, Parametros.padrao())))
        return 1 if resposta["erro"] else 0
    Assistente().executar()
    return 0


if __name__ == "__main__":
    sys.exit(main())
