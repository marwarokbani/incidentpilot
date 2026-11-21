"""Charger les scénarios. Deux fonctions séparées : ce que le modèle voit, et la bonne réponse."""
import csv
import json
from pathlib import Path

SCENARIOS_DIR = Path("scenarios")

CATEGORIES = {
    "connection_leak", "memory_leak", "bad_config", "dependency_outage",
    "disk_full", "traffic_spike", "code_bug", "certificate_expired",
}


def list_scenarios():
    """Les dossiers de scenarios/, triés par nom (s01, s02...)."""
    return sorted(p for p in SCENARIOS_DIR.iterdir() if p.is_dir())


def load_incident(folder):
    """Tout ce que le modèle a le droit de voir : logs, métriques, commits. Jamais truth.json."""
    folder = Path(folder)
    lignes = (folder / "logs.jsonl").read_text(encoding="utf-8").splitlines()
    logs = [json.loads(ligne) for ligne in lignes if ligne.strip()]
    with open(folder / "metrics.csv", newline="", encoding="utf-8") as f:
        metrics = list(csv.DictReader(f))
    commits = json.loads((folder / "commits.json").read_text(encoding="utf-8"))
    return {"logs": logs, "metrics": metrics, "commits": commits}


def load_truth(folder):
    """La bonne réponse. Elle ne sert qu'à noter le diagnostic."""
    return json.loads((Path(folder) / "truth.json").read_text(encoding="utf-8"))