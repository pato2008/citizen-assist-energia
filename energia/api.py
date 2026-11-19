"""Ponto de integração do módulo Energia com o assistente Citizen Assist AI.

O assistente principal (outras disciplinas) chama consultar_energia() com o perfil da
pessoa e recebe um dicionário JSON-serializável com números, recomendações, referências
e limitações. A parte de ENERGIA pode ser testada separadamente (ver tests/).

    >>> from energia.api import consultar_energia
    >>> r = consultar_energia({"pessoas": 4, "minutos_por_banho": 8})
    >>> r["erro"] is None
    True
"""
import json
import sys

from .calculos import EntradaInvalida, Perfil, simular
from .parametros import Parametros
from .recomendacao import AVISO, LIMITACOES, recomendar

VERSAO = "1.0"
CAMPOS = ("pessoas", "minutos_por_banho", "banhos_por_pessoa_dia", "potencia_w", "tarifa_rs_kwh",
          "consumo_conta_kwh_mes", "pode_instalar", "tem_sol_no_telhado")
_SIM = {"s", "sim", "y", "yes", "true", "1", "verdadeiro"}
_NAO = {"n", "nao", "não", "no", "false", "0", "falso"}


def _booleano(valor, nome):
    if isinstance(valor, bool):
        return valor
    texto = str(valor).strip().lower()
    if texto in _SIM:
        return True
    if texto in _NAO:
        return False
    raise EntradaInvalida("Responda sim ou não para '%s'." % nome)


def perfil_de_dict(dados):
    """Converte um dicionário em Perfil (campos ausentes usam o cenário de referência)."""
    desconhecidos = [k for k in dados if k not in CAMPOS]
    if desconhecidos:
        raise EntradaInvalida("Campo(s) desconhecido(s): %s. Campos aceitos: %s." % (", ".join(desconhecidos), ", ".join(CAMPOS)))
    perfil = Perfil()
    for chave, valor in dados.items():
        if valor is None:
            continue
        if chave in ("pode_instalar", "tem_sol_no_telhado"):
            valor = _booleano(valor, chave)
        setattr(perfil, chave, valor)
    return perfil


def referencias_usadas(recomendacoes, p):
    ids = []
    for r in recomendacoes:
        for rid in r.get("refs", []):
            if rid not in ids:
                ids.append(rid)
    for rid in ("R7",):  # a tarifa sempre é citada
        if rid not in ids:
            ids.append(rid)
    return {rid: {"citacao": p.referencias[rid]["citacao"], "url": p.referencias[rid]["url"],
                  "acesso": p.referencias[rid]["acesso"]} for rid in sorted(ids)}


def consultar_energia(perfil=None, parametros=None):
    """Resultado completo para um perfil (dict ou Perfil). Nunca levanta exceção por entrada ruim:
    devolve {'erro': mensagem} para o assistente mostrar ao usuário em linguagem simples."""
    p = parametros or Parametros.padrao()
    base = {"modulo": "energia", "versao": VERSAO, "aviso": AVISO, "limitacoes": LIMITACOES}
    try:
        if perfil is None:
            perfil = Perfil()
        elif isinstance(perfil, dict):
            perfil = perfil_de_dict(perfil)
        resultado = simular(perfil, p)
        recomendacoes = recomendar(resultado, p)
    except EntradaInvalida as erro:
        base.update({"erro": str(erro), "resultado": None, "recomendacoes": [], "referencias": {}})
        return base
    base.update({
        "erro": None,
        "resultado": resultado,
        "recomendacoes": recomendacoes,
        "referencias": referencias_usadas(recomendacoes, p),
        "parametros_estimados": sorted(k for k, v in p.parametros.items() if v["tipo"] in ("estimado", "premissa")),
    })
    return base


def main(argv=None):
    """Uso: python -m energia.api '{"pessoas": 4, "minutos_por_banho": 8}'  (imprime JSON)."""
    argv = sys.argv[1:] if argv is None else argv
    dados = json.loads(argv[0]) if argv else {}
    print(json.dumps(consultar_energia(dados), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
