# IncidentPilot

**Un agent IA qui diagnostique les pannes de production.** Il lit les logs, les métriques et les commits récents d'une application, puis propose la cause racine, le commit coupable et un correctif.

Tout tourne en local avec [Ollama](https://ollama.com) : aucune donnée ne quitte la machine.

> 🚧 **Projet en cours.** Le tableau ci-dessous indique ce qui fonctionne déjà et ce qui reste à faire.

## État d'avancement

| Brique | Statut |
| --- | --- |
| Diagnostic par LLM avec sortie JSON structurée et validée | ✅ Fait |
| Scénarios d'incidents réalistes, avec leur bonne réponse | 🔄 En cours : 2 sur 8 |
| Évaluation automatique : taux de bon diagnostic | ⏳ À venir |
| RAG : recherche dans les runbooks et les incidents passés | ⏳ À venir |
| Agent avec outils (logs, métriques, git, RAG) | ⏳ À venir |
| API (FastAPI) et Docker | ⏳ À venir |

## Comment ça marche

```
logs de l'incident ──► prompt (règles SRE + schéma JSON) ──► LLM local (qwen2.5:3b)
                                                                   │
                    diagnostic validé ◄── validation Pydantic ◄── réponse JSON
```

Le modèle répond avec un objet `Diagnosis` : la cause racine, le commit coupable (ou `null` s'il n'y en a pas), les lignes de log qui le prouvent, un correctif et une confiance entre 0 et 1.

**Choix de conception :**

- **Sortie structurée** : le schéma JSON est imposé au modèle, qui ne peut pas répondre en texte libre.
- **Validation stricte** : Pydantic rejette une confiance hors de [0, 1].
- **Détection des hallucinations** : chaque preuve citée est comparée aux vrais logs.
- **Règle métier** : un commit n'est coupable que s'il a été déployé sur le service en panne.

## Scénarios d'incidents

Pour noter un diagnostic, il faut connaître la bonne réponse à l'avance. Chaque scénario est généré par un script et contient environ 1 000 lignes de logs, avec du bruit et des fausses pistes :

```
scenarios/s01-db-connection-leak/
  logs.jsonl     # un événement JSON par ligne
  metrics.csv    # une mesure par minute
  commits.json   # les commits déployés, avec leur diff
  truth.json     # la bonne réponse (jamais montrée au modèle)
```

Scénarios écrits : **s01** (fuite de connexions, commit coupable) et **s04** (panne d'un fournisseur externe, aucun commit coupable).

## Installation

Prérequis : Python 3.10 ou plus, et [Ollama](https://ollama.com).

```bash
ollama pull qwen2.5:3b
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Utilisation

Depuis la racine du projet :

```bash
python scripts/make_s01.py          # générer un scénario
python scripts/make_s04.py
python -m incidentpilot.diagnose    # diagnostiquer les mini-incidents de data/
```

## Structure du projet

```
incidentpilot/
  llm.py          # appel à Ollama
  diagnose.py     # prompt SRE, schéma Diagnosis, détection des hallucinations
  scenarios.py    # chargement d'un scénario
scripts/          # générateurs de scénarios
scenarios/        # scénarios générés
data/             # deux mini-incidents écrits à la main
```

## Stack

**Aujourd'hui :** Python, Ollama, httpx, Pydantic
**Prévu :** LangGraph, sentence-transformers, ChromaDB, FastAPI, Docker

## Limites

- Le modèle (3 milliards de paramètres) tombe encore dans certaines fausses pistes : c'est ce que le RAG et l'agent doivent améliorer.
- Les scénarios sont synthétiques : ils imitent des pannes réelles, mais une vraie production est plus désordonnée.
