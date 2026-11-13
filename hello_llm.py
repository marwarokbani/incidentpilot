import httpx

reponse = httpx.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "qwen2.5:3b",
        "messages": [
    {"role": "system", "content": "Tu es une ingénieure SRE expérimentée. Réponds en 2 phrases maximum."},
    {"role": "user", "content": "Mon API renvoie des erreurs 500 depuis 10 minutes. Par quoi je commence ?"},
],
        "stream": False,
        "options": {"temperature": 1.0},
    },
    timeout=120,
)

donnees = reponse.json()
print(donnees["message"]["content"])