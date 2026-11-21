import json
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from incidentpilot.llm import chat


SYSTEM = (
    "Tu es une ingénieure SRE qui diagnostique des incidents de production. "
    "Appuie-toi UNIQUEMENT sur les logs fournis. "
    "Si une information manque pour conclure, dis-le au lieu de deviner.\n"
    "Règles :\n"
    "- Identifie d'abord le service qui tombe en erreur.\n"
    "- Un commit n'est coupable QUE s'il a été déployé sur CE service. "
    "Un déploiement sur un autre service n'est pas une preuve : dans ce cas, culprit_commit = null.\n"
    "- Dans evidence, recopie les lignes de log mot pour mot, sans les modifier ni les fusionner.\n"
    "- confidence est un nombre entre 0 et 1 (par exemple 0.8), pas un pourcentage."
)


class Diagnosis(BaseModel):
    root_cause: str = Field(description="La cause racine, en une ou deux phrases")
    culprit_commit: str | None = Field(
        description="Le sha du commit déployé sur le service en erreur, ou null s'il n'y en a pas"
    )
    evidence: list[str] = Field(description="Les lignes de log, recopiées à l'identique, qui prouvent la cause")
    fix: str = Field(description="Le correctif proposé")
    confidence: float = Field(ge=0, le=1, description="La confiance, entre 0 et 1")

    @field_validator("culprit_commit", mode="before")
    @classmethod
    def chaine_vide_vers_none(cls, valeur):
        # Les petits modèles écrivent souvent la chaîne "null" au lieu de la valeur JSON null
        if isinstance(valeur, str) and valeur.strip().lower() in {"", "null", "none", "n/a", "aucun"}:
            return None
        return valeur


def diagnose(logs):
    schema = Diagnosis.model_json_schema()
    question = (
        f"Voici les logs d'un incident :\n\n{logs}\n\n"
        "Trouve la cause racine. Cite les lignes de log qui la prouvent.\n"
        f"Réponds en JSON selon ce schéma :\n{json.dumps(schema, ensure_ascii=False)}"
    )
    texte = chat(
        [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}],
        schema=schema,
    )
    return Diagnosis.model_validate_json(texte)


def preuves_inventees(diag, logs):
    """Renvoie les lignes de evidence qui n'existent pas telles quelles dans les logs."""
    lignes_du_log = {ligne.strip() for ligne in logs.splitlines()}
    return [ligne for ligne in diag.evidence if ligne.strip() not in lignes_du_log]


if __name__ == "__main__":
    # La bonne réponse attendue pour chaque fichier de logs
    attendus = {
        "data/mini_incident.log": "a1b2c3d",
        "data/mini_incident_sans_deploy.log": None,  # aucun commit coupable visible
    }

    for fichier, bon_commit in attendus.items():
        logs = Path(fichier).read_text(encoding="utf-8")
        diag = diagnose(logs)

        print("=====", fichier)
        print("Cause racine :", diag.root_cause)
        print("Commit coupable :", diag.culprit_commit)
        print("Preuves :")
        for ligne in diag.evidence:
            print("  -", ligne)
        print("Correctif :", diag.fix)
        print("Confiance :", diag.confidence)

        if diag.culprit_commit == bon_commit:
            print("Commit : CORRECT")
        else:
            print("Commit : FAUX - attendu :", bon_commit)

        inventees = preuves_inventees(diag, logs)
        if inventees:
            print("Preuves : FAUX -", len(inventees), "ligne(s) absente(s) des logs :")
            for ligne in inventees:
                print("  !", ligne)
        else:
            print("Preuves : CORRECT")
        print()
