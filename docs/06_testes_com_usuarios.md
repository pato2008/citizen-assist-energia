# 6. Testes com usuários: registros e ajustes

> **Estado deste arquivo:** protocolo e modelos prontos. Os testes com usuários **não foram realizados** até a data da entrega (18/11/2026); por isso os campos abaixo estão marcados como "não realizado".
> Nenhum resultado foi inventado. Os testes seguem este protocolo e serão registrados aqui quando feitos.

## 6.1 Objetivo

Verificar se pessoas comuns **entendem** e **acham útil** a orientação do assistente de energia (tabela de alternativas, recomendação, fontes e limitações),
e registrar os ajustes feitos a partir dos comentários. **Nenhum dado pessoal é coletado:** os participantes são identificados só por U1, U2, U3...
com faixa etária e tipo de moradia.

## 6.2 Protocolo (≈ 10 minutos por pessoa; recomendado: 5 pessoas, no mínimo 3)

1. **Aviso:** "Estamos testando o assistente, não você. Não precisa dizer nome nem endereço. Pode parar quando quiser."
2. **Tarefa A:** "Descubra quanto o chuveiro da sua casa gasta por mês." (a pessoa roda `python assistente_energia.py`, opção 1, ou o grupo roda e mostra a tela)
3. **Tarefa B:** "Com o resultado, decida se pediria orçamento de aquecedor solar e me diga por quê."
4. **Tarefa C:** "Mostre de onde vêm os números." (opção 2 do menu)
5. **Perguntas** (nota de 1 a 5, onde 1 = discordo totalmente e 5 = concordo totalmente):
   * P1. Entendi a tabela de alternativas.
   * P2. Entendi a recomendação final.
   * P3. As informações me ajudariam a decidir algo na minha casa.
   * P4. Confiaria nas informações (por quê?).
   * P5. Qual palavra, número ou frase foi difícil de entender?
   * P6. O que faltou ou o que você mudaria?
6. **Anote** o que a pessoa disse **com as palavras dela**, o tempo gasto e onde travou (sem interferir antes de ela tentar).

## 6.3 Situações testadas

Use os perfis de [`01_contexto_publico_necessidade.md`](01_contexto_publico_necessidade.md): P1 (casa própria, 4 pessoas), P2 (apartamento alugado),
P3 (banho curto, tarifa baixa) e P4 (entrada inválida). Cada participante testa pelo menos dois.

## 6.4 Registro das sessões

| Participante | Perfil (faixa etária / moradia, sem identificação) | Situação testada | Tempo (min) | P1 | P2 | P3 | P4 | Dificuldades e comentários (frases dela) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| U1 | não realizado | não realizado | não realizado | [ ] | [ ] | [ ] | [ ] | não realizado |
| U2 | não realizado | não realizado | não realizado | [ ] | [ ] | [ ] | [ ] | não realizado |
| U3 | não realizado | não realizado | não realizado | [ ] | [ ] | [ ] | [ ] | não realizado |
| U4 | não realizado | não realizado | não realizado | [ ] | [ ] | [ ] | [ ] | não realizado |
| U5 | não realizado | não realizado | não realizado | [ ] | [ ] | [ ] | [ ] | não realizado |

**Média das notas:** P1 não realizado · P2 não realizado · P3 não realizado · P4 não realizado

## 6.5 Ajustes realizados a partir dos testes

| # | Comentário recebido (quem) | Ajuste feito no assistente ou nos documentos | Onde (arquivo / commit) | Reteste |
| --- | --- | --- | --- | --- |
| 1 | não realizado | não realizado | não realizado | não realizado |
| 2 | não realizado | não realizado | não realizado | não realizado |
| 3 | não realizado | não realizado | não realizado | não realizado |

Exemplos de onde ajustar: palavras em `energia/recomendacao.py` e `energia/assistente.py` (textos), perguntas em `Assistente.coletar_perfil`,
valores em `dados/parametros.json`. Depois de qualquer ajuste, rode `python -m unittest discover -s tests` e `python scripts/gerar_resultados.py`.

## 6.6 Conclusões dos testes

* O que as pessoas entenderam bem: não realizado
* O que gerou dúvida e como resolvemos: não realizado
* Limites desta avaliação (poucas pessoas, conhecidos do grupo, linguagem em português): não realizado
