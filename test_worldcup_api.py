import requests


URLS_TO_TEST = [
    "https://worldcup2026-api.vercel.app/api/matches",
    "https://worldcup2026-api.vercel.app/api/fixtures",
    "https://worldcup2026-api.vercel.app/api/matches/1",
]


for url in URLS_TO_TEST:
    print("=" * 80)
    print("Probando URL:", url)

    try:
        response = requests.get(url, timeout=30)
        print("STATUS CODE:", response.status_code)
        print("CONTENT TYPE:", response.headers.get("content-type"))

        text = response.text
        print("RESPUESTA PRIMEROS 1000 CARACTERES:")
        print(text[:1000])

    except Exception as e:
        print("ERROR:", repr(e))
