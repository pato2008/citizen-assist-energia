"""Exemplo de integração: como o assistente principal encaminha uma pergunta de energia ao módulo.

Num assistente com LLM, o modelo extrai os números da frase e chama a ferramenta `consultar_energia`
(ver ferramenta_consultar_energia.json). Aqui, para poder TESTAR a integração sem chave de API, a
extração é feita por expressões regulares simples.

    python integracao/exemplo_roteamento.py "Somos 4 pessoas, banho de 10 min, kWh a R$ 0,95. Vale a pena aquecedor solar?"
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from energia.api import consultar_energia  # noqa: E402
from energia.assistente import texto_resultado  # noqa: E402
from energia.parametros import Parametros  # noqa: E402

PALAVRAS_ENERGIA = ("energia", "luz", "chuveiro", "solar", "kwh", "conta de", "renovável", "renovavel")


def eh_pergunta_de_energia(texto):
    t = texto.lower()
    return any(p in t for p in PALAVRAS_ENERGIA)


def extrair_perfil(texto):
    """Extrai números da frase (substitui, neste exemplo, a extração feita pelo LLM)."""
    t = texto.lower().replace(",", ".")
    perfil = {}
    achou = re.search(r"(\d+)\s*pessoas", t)
    if achou:
        perfil["pessoas"] = int(achou.group(1))
    achou = re.search(r"(\d+(?:\.\d+)?)\s*min", t)
    if achou:
        perfil["minutos_por_banho"] = float(achou.group(1))
    achou = re.search(r"(\d{4})\s*w\b", t)
    if achou:
        perfil["potencia_w"] = float(achou.group(1))
    achou = re.search(r"r\$\s*(\d+(?:\.\d+)?)", t)
    if achou:
        perfil["tarifa_rs_kwh"] = float(achou.group(1))
    return perfil


def responder(pergunta):
    if not eh_pergunta_de_energia(pergunta):
        return ["(Esta pergunta não é de energia: o assistente principal usaria outro módulo.)"]
    resposta = consultar_energia(extrair_perfil(pergunta))
    return texto_resultado(resposta, Parametros.padrao())


if __name__ == "__main__":
    texto = " ".join(sys.argv[1:]) or "Somos 4 pessoas, banho de 10 min, kWh a R$ 0,95. Vale a pena aquecedor solar?"
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    print("\n".join(responder(texto)))
