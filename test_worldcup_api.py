import requests


URLS_TO_TEST = [
    "https://fifa.balldontlie.io/api/v1/matches",
    "https://fifa.balldontlie.io/api/v1/matches?year=2026",
    "https://fifa.balldontlie.io/api/v1/games?year=2026",
    "https://fifa.balldontlie.io/api/v1/fixtures?year=2026",
]


for url in URLS_TO_TEST:
    print("=" * 80)
    print("Probando URL:", url)

    try:
        response = requests.get(url, timeout=30)
        print("STATUS CODE:", response.status_code)
        print("CONTENT TYPE:", response.headers.get("content-type"))

        text = response.text
        print("RESPUESTA PRIMEROS 1500 CARACTERES:")
        print(text[:1500])

    except Exception as e:
        print("ERROR:", repr(e))
