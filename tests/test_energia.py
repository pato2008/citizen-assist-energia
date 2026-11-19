"""Testes automáticos do módulo Energia.  Rode:  python -m unittest discover -s tests -v

Os valores esperados foram calculados À MÃO (calculadora) a partir das fórmulas do README,
não copiados da saída do programa:

    E_mes = P[kW] x t[h] x banhos/dia x 30
    A0: 5,5 kW x (8/60 h) x 4 x 30            = 88 kWh/mês  -> 1.056 kWh/ano
    A1: 5,5 kW x (6/60 h) x 4 x 30            = 66 kWh/mês  ->   792 kWh/ano
    A2: 1.056 x (1 - 0,66)                    = 359,04 kWh/ano
    A3: 792 x (1 - 0,66)                      = 269,28 kWh/ano
    tarifa (com tributos) = 0,849 / (1 - 0,229) = 1,10117 R$/kWh
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from energia import calculos  # noqa: E402
from energia.api import consultar_energia  # noqa: E402
from energia.assistente import Assistente, interpretar_menu  # noqa: E402
from energia.calculos import EntradaInvalida, Perfil, cenario, simular  # noqa: E402
from energia.parametros import Parametros  # noqa: E402


class TestFormulas(unittest.TestCase):
    def test_energia_mensal(self):
        self.assertAlmostEqual(calculos.energia_mensal_kwh(5500, 8, 4, 30), 88.0, places=9)
        self.assertAlmostEqual(calculos.energia_mensal_kwh(5500, 6, 4, 30), 66.0, places=9)
        # exemplo do IDEC (R1): 5.500 W por 1 h/dia durante 30 dias = 165 kWh
        self.assertAlmostEqual(calculos.energia_mensal_kwh(5500, 60, 1, 30), 165.0, places=9)

    def test_custo_e_payback(self):
        self.assertAlmostEqual(calculos.custo_rs(100, 1.10), 110.0)
        self.assertAlmostEqual(calculos.payback_anos(4500, 750), 6.0)
        self.assertIsNone(calculos.payback_anos(4500, 0))
        self.assertIsNone(calculos.payback_anos(4500, -10))

    def test_co2_e_agua(self):
        self.assertAlmostEqual(calculos.co2_kg(1000, 0.025), 25.0)
        # 2 min a menos x 5 L/min x 4 banhos x 30 dias = 1.200 L/mês
        self.assertAlmostEqual(calculos.agua_litros_mes(2, 4, 5, 30), 1200.0)


class TestParametros(unittest.TestCase):
    def setUp(self):
        self.p = Parametros.padrao()

    def test_tarifa_com_tributos(self):
        self.assertAlmostEqual(self.p.tarifa_com_tributos(), 0.849 / (1 - 0.229), places=9)
        self.assertAlmostEqual(self.p.tarifa_com_tributos(), 1.1012, places=3)

    def test_todo_parametro_tem_origem_tipo_e_referencia_valida(self):
        tipos = {"público", "estimado", "premissa", "calculado"}
        for nome, item in self.p.parametros.items():
            self.assertIn(item["tipo"], tipos, nome)
            self.assertTrue(item["origem"].strip(), nome)
            self.assertTrue(item["unidade"].strip(), nome)
            for rid in item["ref"]:
                self.assertIn(rid, self.p.referencias, "%s cita %s inexistente" % (nome, rid))

    def test_fator_de_emissao_e_media_de_4_meses(self):
        self.assertAlmostEqual(self.p.v("fator_emissao_kg_co2_kwh") * 1000, (23.7 + 24.8 + 21.5 + 28.9) / 4, places=6)

    def test_reducao_solar_vem_do_estudo(self):
        self.assertAlmostEqual((11 - 3.75) / 11, 0.659, places=3)
        self.assertEqual(self.p.v("reducao_solar_base"), 0.66)

    def test_referencias_tem_url_e_data(self):
        for rid, ref in self.p.referencias.items():
            self.assertTrue(ref["url"].startswith("http"), rid)
            self.assertEqual(ref["acesso"], "18/11/2026", rid)


class TestCenarioBase(unittest.TestCase):
    def setUp(self):
        self.p = Parametros.padrao()
        self.r = simular(Perfil(tarifa_rs_kwh=1.10), self.p)

    def test_consumos_anuais(self):
        self.assertAlmostEqual(cenario(self.r, "A0")["kwh_ano"], 1056.0, places=6)
        self.assertAlmostEqual(cenario(self.r, "A1")["kwh_ano"], 792.0, places=6)
        self.assertAlmostEqual(cenario(self.r, "A2")["kwh_ano"], 359.04, places=6)
        self.assertAlmostEqual(cenario(self.r, "A3")["kwh_ano"], 269.28, places=6)

    def test_custos_anuais_com_tarifa_1_10(self):
        self.assertAlmostEqual(cenario(self.r, "A0")["custo_ano_rs"], 1161.60, places=2)
        self.assertAlmostEqual(cenario(self.r, "A1")["custo_ano_rs"], 871.20, places=2)
        self.assertAlmostEqual(cenario(self.r, "A2")["custo_ano_rs"], 394.944, places=3)

    def test_economia_e_payback_do_solar(self):
        a2 = cenario(self.r, "A2")
        self.assertAlmostEqual(a2["economia_bruta_ano_rs"], 766.656, places=3)   # 1.161,60 - 394,944
        self.assertAlmostEqual(a2["manutencao_ano_rs"], 45.0, places=6)          # 1% de R$ 4.500
        self.assertAlmostEqual(a2["economia_liquida_ano_rs"], 721.656, places=3)
        self.assertAlmostEqual(a2["payback_anos"], 4500 / 721.656, places=6)     # ~ 6,24 anos
        self.assertAlmostEqual(a2["beneficio_liquido_horizonte_rs"], 721.656 * 10 - 4500, places=3)

    def test_payback_do_solar_sobre_o_habito(self):
        a3 = cenario(self.r, "A3")
        # A1 custa 871,20; A3 custa 269,28 x 1,10 = 296,208 -> ganho 575,0 - 45 de manutenção
        ganho = (871.20 - 296.208) - 45.0
        self.assertAlmostEqual(a3["economia_liquida_sobre_a1_ano_rs"], ganho, places=3)
        self.assertAlmostEqual(a3["payback_sobre_a1_anos"], 4500 / ganho, places=6)
        self.assertGreater(a3["payback_sobre_a1_anos"], cenario(self.r, "A2")["payback_anos"])

    def test_agua_e_co2(self):
        self.assertAlmostEqual(cenario(self.r, "A1")["agua_economizada_l_mes"], 1200.0, places=6)
        self.assertAlmostEqual(cenario(self.r, "A2")["co2_evitado_kg_ano"], (1056 - 359.04) * 0.024725, places=6)

    def test_mesma_necessidade_mesmo_periodo(self):
        # todos os cenários usam 12 meses e a mesma família (banhos/dia iguais)
        for c in self.r["cenarios"]:
            self.assertAlmostEqual(c["kwh_ano"], c["kwh_mes"] * 12, places=9)

    def test_ordem_de_grandeza_do_coletor(self):
        self.assertAlmostEqual(self.r["checagens"]["capacidade_um_coletor_vs_demanda"], 121.4 / 88.0, places=9)

    def test_tarifa_padrao_quando_nao_informada(self):
        r = simular(Perfil(), self.p)
        self.assertFalse(r["tarifa_foi_informada"])
        self.assertAlmostEqual(r["tarifa_rs_kwh"], self.p.tarifa_padrao(), places=9)


class TestRegrasEEntradas(unittest.TestCase):
    def setUp(self):
        self.p = Parametros.padrao()

    def test_banho_ja_curto_nao_gera_economia_no_a1(self):
        r = simular(Perfil(minutos_por_banho=5, tarifa_rs_kwh=1.0), self.p)
        a1 = cenario(r, "A1")
        self.assertEqual(a1["minutos_por_banho"], 5)
        self.assertAlmostEqual(a1["economia_bruta_ano_rs"], 0.0, places=9)

    def test_sem_autorizacao_ou_sem_sol_torna_solar_inviavel(self):
        r1 = simular(Perfil(pode_instalar=False), self.p)
        r2 = simular(Perfil(tem_sol_no_telhado=False), self.p)
        for r in (r1, r2):
            self.assertFalse(cenario(r, "A2")["viavel"])
            self.assertTrue(cenario(r, "A2")["motivo_inviavel"])
        self.assertTrue(cenario(simular(Perfil(), self.p), "A2")["viavel"])

    def test_entradas_invalidas(self):
        casos = [
            Perfil(pessoas=0), Perfil(pessoas=13), Perfil(pessoas=2.5), Perfil(pessoas="abc"),
            Perfil(minutos_por_banho=0), Perfil(minutos_por_banho=90), Perfil(minutos_por_banho=-5),
            Perfil(banhos_por_pessoa_dia=0), Perfil(potencia_w=10), Perfil(potencia_w=99999),
            Perfil(tarifa_rs_kwh=0), Perfil(tarifa_rs_kwh=15), Perfil(consumo_conta_kwh_mes=1),
            Perfil(minutos_por_banho="nan"), Perfil(minutos_por_banho="inf"), Perfil(minutos_por_banho=True),
        ]
        for perfil in casos:
            with self.assertRaises(EntradaInvalida, msg=str(perfil)):
                simular(perfil, self.p)

    def test_virgula_decimal_e_aceita(self):
        r = simular(Perfil(tarifa_rs_kwh="1,10", minutos_por_banho="7,5"), self.p)
        self.assertAlmostEqual(r["tarifa_rs_kwh"], 1.10)
        self.assertAlmostEqual(r["entrada"]["minutos_por_banho"], 7.5)

    def test_chuveiro_maior_que_a_conta_e_recusado(self):
        with self.assertRaises(EntradaInvalida):
            simular(Perfil(consumo_conta_kwh_mes=60), self.p)  # chuveiro estimado = 88 kWh

    def test_alerta_quando_chuveiro_passa_de_60_por_cento_da_conta(self):
        r = simular(Perfil(consumo_conta_kwh_mes=120), self.p)  # 88/120 = 73%
        self.assertIsNotNone(r["checagens"]["alerta"])
        r2 = simular(Perfil(consumo_conta_kwh_mes=400), self.p)  # 22%
        self.assertIsNone(r2["checagens"]["alerta"])

    def test_sensibilidade_payback_cresce_quando_a_tarifa_cai(self):
        linhas = calculos.sensibilidade_payback_a2(Perfil(), self.p, tarifas=(0.74, 1.10), investimentos=(4500,), reducoes=(0.66,))
        baixa = [x for x in linhas if x["tarifa_rs_kwh"] == 0.74][0]["payback_anos"]
        alta = [x for x in linhas if x["tarifa_rs_kwh"] == 1.10][0]["payback_anos"]
        self.assertGreater(baixa, alta)


class TestIntegracaoApi(unittest.TestCase):
    def test_resposta_json_serializavel_com_referencias_e_limitacoes(self):
        resposta = consultar_energia({"pessoas": 4, "minutos_por_banho": 8, "tarifa_rs_kwh": 1.10})
        json.dumps(resposta, ensure_ascii=False)
        self.assertIsNone(resposta["erro"])
        self.assertGreaterEqual(len(resposta["referencias"]), 3)
        self.assertGreaterEqual(len(resposta["limitacoes"]), 3)
        self.assertIn("NÃO são garantia", resposta["aviso"])
        ids = [r["id"] for r in resposta["recomendacoes"]]
        self.assertIn("habito", ids)
        self.assertIn("solar", ids)
        self.assertTrue(all(r["refs"] for r in resposta["recomendacoes"]))   # toda recomendação cita referências

    def test_erro_vira_mensagem_e_nao_excecao(self):
        resposta = consultar_energia({"pessoas": 99})
        self.assertIsNotNone(resposta["erro"])
        self.assertIsNone(resposta["resultado"])

    def test_campo_desconhecido_e_nome_nao_sao_aceitos(self):
        resposta = consultar_energia({"nome": "Maria", "cpf": "000"})
        self.assertIn("desconhecido", resposta["erro"])

    def test_sim_nao_como_texto(self):
        resposta = consultar_energia({"pode_instalar": "não"})
        self.assertFalse(cenario(resposta["resultado"], "A2")["viavel"])

    def test_recomendacao_muda_conforme_o_retorno(self):
        barato = consultar_energia({"tarifa_rs_kwh": 1.50})                     # retorno curto
        caro = consultar_energia({"tarifa_rs_kwh": 0.30, "minutos_por_banho": 5})  # quase não economiza
        titulo = lambda resp: [r["titulo"] for r in resp["recomendacoes"] if r["id"] == "solar"][0]
        self.assertIn("vale pedir orçamentos", titulo(barato))
        self.assertNotIn("vale pedir orçamentos", titulo(caro))


class TestIntegracao(unittest.TestCase):
    def test_esquema_da_ferramenta_bate_com_os_campos_da_api(self):
        from energia.api import CAMPOS
        caminho = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "integracao", "ferramenta_consultar_energia.json")
        with open(caminho, encoding="utf-8") as f:
            ferramenta = json.load(f)
        self.assertEqual(ferramenta["name"], "consultar_energia")
        self.assertEqual(sorted(ferramenta["input_schema"]["properties"]), sorted(CAMPOS))

    def test_roteamento_extrai_numeros_e_chama_o_modulo(self):
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "integracao"))
        import exemplo_roteamento as ex
        perfil = ex.extrair_perfil("Somos 3 pessoas, banho de 10 min, chuveiro de 4500 W, kWh a R$ 0,95")
        self.assertEqual(perfil, {"pessoas": 3, "minutos_por_banho": 10.0, "potencia_w": 4500.0, "tarifa_rs_kwh": 0.95})
        self.assertTrue(ex.eh_pergunta_de_energia("Vale a pena aquecedor solar?"))
        self.assertFalse(ex.eh_pergunta_de_energia("Como renovo meu RG?"))
        texto = "\n".join(ex.responder("Somos 3 pessoas, banho de 10 min, kWh a R$ 0,95. Vale a pena aquecedor solar?"))
        self.assertIn("RECOMENDAÇÕES", texto)


class TestPerfisDoDocumento(unittest.TestCase):
    """Os perfis P1-P4 de docs/01_contexto_publico_necessidade.md precisam se comportar como o documento diz."""

    def titulos(self, resposta):
        return {r["id"]: r["titulo"] for r in resposta["recomendacoes"]}

    def test_p1_casa_propria_4_pessoas(self):
        r = consultar_energia({"pessoas": 4, "minutos_por_banho": 8, "potencia_w": 5500, "tarifa_rs_kwh": 1.10})
        t = self.titulos(r)
        self.assertIn("banho de 6 minutos", t["habito"])
        self.assertIn("vale pedir orçamentos", t["solar"])
        self.assertAlmostEqual(cenario(r["resultado"], "A2")["payback_anos"], 6.24, places=2)

    def test_p2_apartamento_alugado(self):
        r = consultar_energia({"pessoas": 2, "minutos_por_banho": 7, "pode_instalar": False})
        t = self.titulos(r)
        self.assertIn("banho de 6 minutos", t["habito"])
        self.assertIn("não é recomendado agora", t["solar"])
        self.assertNotIn("combinado", t)

    def test_p3_banho_curto_tarifa_baixa(self):
        r = consultar_energia({"pessoas": 3, "minutos_por_banho": 5, "tarifa_rs_kwh": 0.80})
        t = self.titulos(r)
        self.assertIn("já é curto", t["habito"])
        self.assertIn("longo demais", t["solar"])
        self.assertGreater(cenario(r["resultado"], "A2")["payback_anos"], 15)

    def test_p4_entradas_invalidas_viram_mensagem(self):
        self.assertIn("deve estar entre", consultar_energia({"minutos_por_banho": 90})["erro"])
        self.assertIn("deve estar entre", consultar_energia({"tarifa_rs_kwh": 9})["erro"])


class TestAssistenteCLI(unittest.TestCase):
    def rodar(self, entradas):
        it = iter(entradas)
        saida = []
        Assistente(entrada=lambda pergunta: next(it), saida=saida.append).executar()
        return "\n".join(saida)

    def test_menu_por_numero_e_por_palavra(self):
        self.assertEqual(interpretar_menu("1"), "1")
        self.assertEqual(interpretar_menu("vale a pena instalar aquecedor solar?"), "1")
        self.assertEqual(interpretar_menu("quais são as fontes?"), "2")
        self.assertEqual(interpretar_menu("quais as limitações"), "3")
        self.assertEqual(interpretar_menu("sair"), "0")
        self.assertIsNone(interpretar_menu("blablabla"))

    def test_fluxo_completo_com_entradas_invalidas(self):
        texto = self.rodar(["1", "abc", "4", "90", "8", "", "", "1,10", "300", "s", "s", "0"])
        self.assertIn("Não entendi sua resposta", texto)           # texto no lugar de número
        self.assertIn("o valor deve estar entre 1 e 40", texto)     # 90 minutos é recusado
        self.assertIn("RECOMENDAÇÕES", texto)
        self.assertIn("REFERÊNCIAS USADAS", texto)
        self.assertIn("NÃO são garantia", texto)
        self.assertIn("A2 Aquecedor solar", texto)

    def test_desiste_do_campo_apos_tres_erros_e_usa_valor_de_referencia(self):
        texto = self.rodar(["1", "x", "y", "z"] + [""] * 7 + ["0"])
        self.assertIn("Vou usar o valor de referência", texto)
        self.assertIn("RECOMENDAÇÕES", texto)

    def test_opcao_nao_reconhecida_nao_trava(self):
        texto = self.rodar(["asdfgh", "0"])
        self.assertIn("Não entendi", texto)

    def test_assistente_nao_pede_dados_pessoais(self):
        texto = self.rodar(["1"] + [""] * 8 + ["0"]).lower()
        for proibido in ("nome completo", "cpf", "endereço", "endereco", "telefone", "e-mail", "número de cliente"):
            self.assertNotIn(proibido, texto)

    def test_fontes_e_limitacoes(self):
        texto = self.rodar(["fontes", "limitações", "0"])
        for rid in ("[R1]", "[R4]", "[R7]", "[R8]"):
            self.assertIn(rid, texto)
        self.assertIn("LIMITAÇÕES", texto)


if __name__ == "__main__":
    unittest.main(verbosity=2)
