"""Outils communs à tous les générateurs de scénarios."""
import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

START = datetime(2026, 11, 10, 14, 0, tzinfo=timezone.utc)  # début de l'enregistrement
DURATION = 60                                               # minutes enregistrées
SERVICES = ["orders-api", "payments-api", "gateway"]


def ts(minute, second=0):
    """Minute relative -> horodatage, ex. ts(35, 12) donne '2026-11-10T14:35:12Z'."""
    moment = START + timedelta(minutes=minute, seconds=second)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def log(minute, second, service, level, msg):
    """Une ligne de log, sous forme de dictionnaire."""
    return {"ts": ts(minute, second), "service": service, "level": level, "msg": msg}


def background_logs(rng):
    """Le bruit : ce que les services écrivent quand tout va bien."""
    logs = []
    for minute in range(DURATION):
        for _ in range(rng.randint(8, 15)):          # 8 à 15 lignes par minute
            ms = rng.randint(20, 180)
            level, msg = rng.choice([
                ("INFO", f"GET /orders/{rng.randint(1000, 9999)} 200 in {ms}ms"),
                ("INFO", f"POST /orders 201 in {ms}ms"),
                ("INFO", "health check ok"),
                ("WARN", f"slow query on products ({rng.randint(500, 900)}ms)"),  # fausse piste
            ])
            logs.append(log(minute, rng.randint(0, 59), rng.choice(SERVICES), level, msg))
    return logs


def write_scenario(folder, logs, metric_rows, commits, truth):
    """Écrit les 4 fichiers d'un scénario dans son dossier."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    logs.sort(key=lambda ligne: ligne["ts"])        # ordre chronologique
    with open(folder / "logs.jsonl", "w", encoding="utf-8") as f:
        for ligne in logs:
            f.write(json.dumps(ligne, ensure_ascii=False) + "\n")

    with open(folder / "metrics.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ts", "service", "metric", "value"])
        writer.writeheader()
        writer.writerows(metric_rows)

    (folder / "commits.json").write_text(json.dumps(commits, indent=2, ensure_ascii=False), encoding="utf-8")
    (folder / "truth.json").write_text(json.dumps(truth, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{folder.name} : {len(logs)} lignes de logs, {len(metric_rows)} mesures, {len(commits)} commits")
