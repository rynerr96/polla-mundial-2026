import requests


URLS_TO_TEST = [
    "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json",
    "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.teams.json",
    "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.groups.json",
]


for url in URLS_TO_TEST:
    print("=" * 80)
    print("Probando URL:", url)

    try:
        response = requests.get(url, timeout=30)
        print("STATUS CODE:", response.status_code)
        print("CONTENT TYPE:", response.headers.get("content-type"))

        text = response.text
        print("RESPUESTA PRIMEROS 2000 CARACTERES:")
        print(text[:2000])

    except Exception as e:
        print("ERROR:", repr(e))
