import httpx

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:3b"


def chat(messages, model=MODEL, temperature=0, schema=None, max_tokens=800, timeout=300):
    """Envoie des messages au modèle. Avec un schéma, force une réponse JSON de cette forme."""
    body = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            # Plafond de tokens générés : empêche le modèle de tourner en boucle indéfiniment
            "num_predict": max_tokens,
        },
    }
    if schema is not None:
        body["format"] = schema

    try:
        reponse = httpx.post(f"{OLLAMA_URL}/api/chat", json=body, timeout=timeout)
    except httpx.TimeoutException:
        raise RuntimeError(
            f"Ollama n'a pas répondu en {timeout}s (modèle en cours de chargement ou machine surchargée ?)"
        ) from None
    reponse.raise_for_status()

    donnees = reponse.json()
    print("Tokens du prompt :", donnees["prompt_eval_count"])
    if donnees.get("done_reason") == "length":
        print(f"Attention : réponse coupée à {max_tokens} tokens")
    return donnees["message"]["content"]
