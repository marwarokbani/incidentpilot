"""Scénario s04 : le fournisseur de paiement externe tombe. Aucun commit n'est coupable."""
import random

from scenario_kit import DURATION, background_logs, log, ts, write_scenario

OUTAGE_AT = 32      # minute où le fournisseur commence à répondre 503 (14:32)


def incident_logs(rng):
    """payments-api reçoit des 503 du fournisseur, le gateway propage l'erreur."""
    logs = []
    for minute in range(OUTAGE_AT, DURATION):
        for _ in range(rng.randint(3, 7)):
            second = rng.randint(0, 58)
            logs.append(log(minute, second, "payments-api", "ERROR",
                            "provider api.paycorp.example returned 503 Service Unavailable"))
            logs.append(log(minute, second + 1, "gateway", "ERROR",
                            "upstream payments-api returned 502"))
    return logs


def metrics(rng):
    rows = []
    for minute in range(DURATION):
        en_panne = minute >= OUTAGE_AT
        valeurs = {
            "provider_error_rate": round(rng.uniform(0.6, 0.9) if en_panne else rng.uniform(0, 0.01), 3),
            "http_error_rate": round(rng.uniform(0.3, 0.5) if en_panne else rng.uniform(0, 0.01), 3),
            "cpu_percent": rng.randint(15, 30),
        }
        for nom, valeur in valeurs.items():
            rows.append({"ts": ts(minute), "service": "payments-api", "metric": nom, "value": valeur})
    return rows


COMMITS = [
    {"sha": "7e8f9a0", "service": "payments-api", "deployed_at": ts(22),   # 10 minutes avant : piège
     "message": "docs: update README for payment flow",
     "diff": "- ## Payment\n+ ## Payment flow"},
]

TRUTH = {
    "id": "s04-provider-outage",
    "category": "dependency_outage",
    "culprit_commit": None,
    "root_cause": "Le fournisseur de paiement externe api.paycorp.example répond 503 depuis 14:32. "
                  "Aucun changement de notre côté n'est en cause.",
    "red_herrings": ["commit 7e8f9a0 sur payments-api 10 minutes avant, qui ne touche que la doc",
                     "erreurs 502 du gateway"],
}


if __name__ == "__main__":
    rng = random.Random(4)
    logs = background_logs(rng) + incident_logs(rng)
    write_scenario("scenarios/s04-provider-outage", logs, metrics(rng), COMMITS, TRUTH)
