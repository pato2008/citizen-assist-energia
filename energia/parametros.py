"""Carrega os parâmetros do módulo Energia (valor, unidade, tipo, origem e referência).

Todos os números usados nos cálculos ficam em dados/parametros.json, cada um com a
sua origem. Assim é possível auditar (e trocar) qualquer premissa sem mexer no código.
"""
import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO_PARAMETROS = os.path.join(RAIZ, "dados", "parametros.json")


class Parametros:
    def __init__(self, dados):
        self.meta = dados["meta"]
        self.parametros = dados["parametros"]
        self.referencias = dados["referencias"]

    @classmethod
    def padrao(cls, caminho=CAMINHO_PARAMETROS):
        with open(caminho, encoding="utf-8") as arquivo:
            return cls(json.load(arquivo))

    def v(self, nome):
        """Valor numérico do parâmetro."""
        return self.parametros[nome]["valor"]

    def tarifa_com_tributos(self):
        """Tarifa com tributos 'por dentro': T / (1 - (ICMS + PIS/Cofins))."""
        aliquota = (self.v("icms_pct") + self.v("pis_cofins_pct")) / 100.0
        return self.v("tarifa_sem_tributos_rs_kwh") / (1.0 - aliquota)

    def tarifa_padrao(self):
        """Tarifa usada quando a pessoa não informa a da sua conta (R$/kWh, com tributos,
        mais o adicional da bandeira em vigor)."""
        return self.tarifa_com_tributos() + self.v("bandeira_adicional_rs_100kwh") / 100.0

    def referencia(self, rid):
        r = self.referencias[rid]
        return "[%s] %s %s Acesso em %s." % (rid, r["citacao"], r["url"], r["acesso"])
