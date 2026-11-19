"""Módulo Energia do Citizen Assist AI (disciplina: Soluções em Energias Renováveis e Sustentáveis)."""


def consultar_energia(*args, **kwargs):
    """Atalho para energia.api.consultar_energia (import preguiçoso, para `python -m energia.api` funcionar sem avisos)."""
    from .api import consultar_energia as _consultar
    return _consultar(*args, **kwargs)
