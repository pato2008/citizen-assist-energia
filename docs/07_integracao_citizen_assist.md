# 7. Integração com o Citizen Assist AI e identificação da contribuição de Energia

## 7.1 O que é a contribuição de Soluções em Energias Renováveis e Sustentáveis

| Pasta / arquivo | Papel |
| --- | --- |
| `energia/` | Módulo Python: cálculos (`calculos.py`), regras de recomendação (`recomendacao.py`), assistente de conversa (`assistente.py`) e ponto de integração (`api.py`). |
| `dados/` | Parâmetros com origem (`parametros.json`) e resultados em CSV. |
| `docs/` | Contexto, dados e premissas, cálculos, justificativas, referências e testes com usuários. |
| `integracao/` | Definição da ferramenta para LLM, fragmento de *system prompt* e exemplo de roteamento. |
| `tests/` | Testes automáticos (valores calculados à mão). |

Se o grupo juntar tudo em um repositório compartilhado, basta copiar essas pastas para uma subpasta (por exemplo, `modulos/energia/`) e manter o README desta pasta.

## 7.2 Como o assistente principal usa o módulo

```text
Pergunta da pessoa ──> assistente principal (LLM)
                         │  reconhece o tema "energia" (conta de luz, chuveiro, solar)
                         ├─ extrai/pergunta os números (pessoas, minutos, tarifa...)
                         ▼
                 consultar_energia(perfil)  <── energia/api.py (testável sozinho)
                         │  devolve JSON: resultado, recomendacoes, referencias, limitacoes, erro
                         ▼
        o assistente redige a resposta SEM alterar os números e mostra fontes e limites
```

* **Ferramenta:** [`integracao/ferramenta_consultar_energia.json`](../integracao/ferramenta_consultar_energia.json) (esquema JSON para *function/tool calling*).
* **Instruções ao modelo:** [`integracao/prompt_energia.md`](../integracao/prompt_energia.md).
* **Exemplo executável sem chave de API:** `python integracao/exemplo_roteamento.py "Somos 4 pessoas, banho de 10 min, kWh a R$ 0,95. Vale a pena aquecedor solar?"`.

## 7.3 Contrato da resposta (`consultar_energia`)

```json
{
  "modulo": "energia", "versao": "1.0", "aviso": "...",
  "erro": null,
  "resultado": {"entrada": {...}, "tarifa_rs_kwh": 1.10, "consumo_base_mes_kwh": 88.0, "cenarios": [ {"id": "A0", ...}, {"id": "A1", ...}, {"id": "A2", ...}, {"id": "A3", ...} ], "checagens": {...}},
  "recomendacoes": [ {"id": "habito", "titulo": "...", "texto": "...", "refs": ["R4", "R5", "R1"]}, ... ],
  "referencias": {"R1": {"citacao": "...", "url": "...", "acesso": "18/11/2026"}, ...},
  "limitacoes": ["..."]
}
```

Em caso de entrada inválida, `erro` traz a mensagem em linguagem simples e `resultado` é `null` (a função nunca levanta exceção para o assistente).

## 7.4 Testar a contribuição de Energia separadamente

```bash
python -m unittest discover -s tests -v             # 40 testes
python assistente_energia.py --demo                 # demonstração de conversa
python assistente_energia.py --json --pessoas 4 --minutos 8 --tarifa 1,10     # JSON da integração
python -m energia.api '{"pessoas": 4, "minutos_por_banho": 8}'                 # mesma chamada que o assistente principal faz
```
