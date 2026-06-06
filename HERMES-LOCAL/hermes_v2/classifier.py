from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Classification:
    intencao: str
    papel: str
    nivel_urgencia: str
    prioridade: int


CRISIS_TERMS = (
    "suicidio",
    "suicídio",
    "me matar",
    "violencia",
    "violência",
    "abuso",
    "ameaça",
    "ameaca",
    "crise",
    "desespero",
)


def _text(payload: dict) -> str:
    parts = [
        payload.get("tipo_evento"),
        payload.get("fluxo_origem"),
        payload.get("mensagem"),
        payload.get("resumo"),
        payload.get("resumo_ia"),
        payload.get("ultima_intencao"),
    ]
    campos = payload.get("campos")
    if isinstance(campos, dict):
        parts.extend(str(value) for value in campos.values())
    return " ".join(str(part or "") for part in parts).lower()


def _has(text: str, *patterns: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def classify(payload: dict) -> Classification:
    text = _text(payload)

    if any(term in text for term in CRISIS_TERMS):
        return Classification("humano_necessario", "Rute", "Urgente", 1)

    if _has(text, r"humano", r"atendente"):
        return Classification("humano_necessario", "Rute", "Alta", 2)

    if _has(text, r"\bvisitante\b", r"primeira visita", r"consolida"):
        return Classification("visitante", "Caleb", "Alta", 2)

    if _has(text, r"relat[oó]rio.*c[eé]lula", r"presen[cç]a.*membros", r"decis[oõ]es.*f[eé]"):
        return Classification("relatorio_celula", "Caleb", "Normal", 4)

    if _has(text, r"ora[cç][aã]o", r"pedido.*or"):
        return Classification("pedido_oracao", "Rute", "Normal", 3)

    if _has(text, r"aconselhamento", r"aconselhar", r"pastor.*conversar"):
        return Classification("aconselhamento", "Rute", "Alta", 2)

    if _has(text, r"cadastro", r"recadastro", r"atualiza[cç][aã]o cadastral"):
        return Classification("cadastro", "Rute", "Normal", 5)

    if _has(text, r"\bc[eé]lula\b", r"\bg12\b"):
        return Classification("celula_g12", "Caleb", "Normal", 4)

    if _has(text, r"agenda", r"agendar", r"compromisso", r"reuni[aã]o"):
        return Classification("agenda", "Rute", "Normal", 4)

    if _has(text, r"post", r"reels", r"shorts", r"conte[uú]do", r"roteiro"):
        return Classification("conteudo", "Barnabe", "Normal", 5)

    if _has(text, r"vit[oó]rias do dia", r"procrastina", r"foco", r"estudo"):
        return Classification("foco", "Neemias", "Normal", 4)

    return Classification("outro", "Rute", "Normal", 5)
