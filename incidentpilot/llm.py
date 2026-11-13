import httpx

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:3b"


def chat(messages, model=MODEL, temperature=0, schema=None):
    """Envoie des messages au modèle. Avec un schéma, force une réponse JSON de cette forme."""
    body = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if schema is not None:
        body["format"] = schema
    reponse = httpx.post(f"{OLLAMA_URL}/api/chat", json=body, timeout=120)
    reponse.raise_for_status()
    return reponse.json()["message"]["content"]