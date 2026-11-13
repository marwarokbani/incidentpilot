from pathlib import Path

from incidentpilot.llm import chat

from pydantic import BaseModel


SYSTEM = (
    "Tu es une ingénieure SRE qui diagnostique des incidents de production. "
    "Appuie-toi UNIQUEMENT sur les logs fournis. "
    "Si une information manque pour conclure, dis-le au lieu de deviner."
)


class Diagnosis(BaseModel):
    root_cause: str             # la cause racine, en une ou deux phrases
    culprit_commit: str | None  # le sha du commit coupable, ou None s'il n'y en a pas
    evidence: list[str]         # les lignes de log qui prouvent la cause
    fix: str                    # le correctif proposé
    confidence: float           # la confiance du modèle, entre 0 et 1


def diagnose(logs):
    question = (
        f"Voici les logs d'un incident :\n\n{logs}\n\n"
        "Trouve la cause racine. Cite les lignes de log qui la prouvent."
    )
    texte = chat(
        [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}],
        schema=Diagnosis.model_json_schema(),
    )
    return Diagnosis.model_validate_json(texte)


if __name__ == "__main__":
    logs = Path("data/mini_incident_sans_deploy.log").read_text(encoding="utf-8")
    diag = diagnose(logs)
    print("Cause racine :", diag.root_cause)
    print("Commit coupable :", diag.culprit_commit)
    print("Preuves :")
    for ligne in diag.evidence:
        print("  -", ligne)
    print("Correctif :", diag.fix)
    print("Confiance :", diag.confidence)