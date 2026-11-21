"""Scénario s01 : un commit oublie de fermer les connexions à la base."""
import random

from scenario_kit import DURATION, background_logs, log, ts, write_scenario

DEPLOY_AT = 20      # minute du déploiement fautif (14:20)
SATURATED_AT = 35   # minute où le pool de connexions est plein (14:35)
POOL_SIZE = 10


def incident_logs(rng):
    """La panne : orders-api n'obtient plus de connexion, le gateway propage l'erreur."""
    logs = []
    for minute in range(SATURATED_AT, DURATION):
        waiting = 5 + (minute - SATURATED_AT) * 3          # la file d'attente s'allonge
        for _ in range(rng.randint(4, 9)):
            second = rng.randint(0, 58)
            logs.append(log(minute, second, "orders-api", "ERROR",
                            f"TimeoutError: could not acquire DB connection within 5s "
                            f"(pool size={POOL_SIZE}, in use={POOL_SIZE}, waiting={waiting})"))
            logs.append(log(minute, second + 1, "gateway", "ERROR",
                            "upstream orders-api returned 500"))   # symptôme, pas la cause
    return logs


def metrics(rng):
    """Une mesure par minute pour chaque métrique d'orders-api."""
    rows = []
    for minute in range(DURATION):
        if minute < DEPLOY_AT:
            in_use = rng.randint(2, 4)                                       # normal
        else:
            in_use = min(POOL_SIZE, 3 + round((minute - DEPLOY_AT) * 0.5))   # la fuite
        en_panne = minute >= SATURATED_AT
        valeurs = {
            "db_connections_in_use": in_use,
            "http_error_rate": round(rng.uniform(0.25, 0.45) if en_panne else rng.uniform(0, 0.01), 3),
            "latency_p95_ms": rng.randint(4800, 5200) if en_panne else rng.randint(80, 160),
            "cpu_percent": rng.randint(15, 30),                              # reste normal
        }
        for nom, valeur in valeurs.items():
            rows.append({"ts": ts(minute), "service": "orders-api", "metric": nom, "value": valeur})
    return rows


COMMITS = [
    {"sha": "9f8e7d6", "service": "payments-api", "deployed_at": ts(5),
     "message": "feat: add retry on payment provider timeout",
     "diff": "+ @retry(times=3, backoff=0.5)\n  def charge(order): ..."},
    {"sha": "a1b2c3d", "service": "orders-api", "deployed_at": ts(DEPLOY_AT),
     "message": "perf: reuse DB session across handlers",
     "diff": "  def get_order(order_id):\n      session = pool.acquire()\n-     try:\n"
             "-         return session.get(Order, order_id)\n-     finally:\n-         session.close()\n"
             "+     return session.get(Order, order_id)  # session kept for reuse"},
    {"sha": "4c5d6e7", "service": "payments-api", "deployed_at": ts(30),
     "message": "chore: bump pydantic 2.9.1 -> 2.9.2",
     "diff": "- pydantic==2.9.1\n+ pydantic==2.9.2"},          # le plus récent, mais innocent
]

TRUTH = {
    "id": "s01-db-connection-leak",
    "category": "connection_leak",
    "culprit_commit": "a1b2c3d",
    "root_cause": "Le commit a1b2c3d supprime session.close() dans orders-api : chaque requête garde "
                  "sa connexion, le pool de 10 se remplit en 15 minutes, puis les requêtes expirent.",
    "red_herrings": ["commit 4c5d6e7, plus récent mais sur payments-api",
                     "WARN slow query, déjà présents avant l'incident",
                     "erreurs du gateway, qui ne font que propager celles d'orders-api"],
}


if __name__ == "__main__":
    rng = random.Random(1)      # graine fixe : les mêmes fichiers à chaque exécution
    logs = background_logs(rng) + incident_logs(rng)
    write_scenario("scenarios/s01-db-connection-leak", logs, metrics(rng), COMMITS, TRUTH)
