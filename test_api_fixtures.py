import os
import requests


API_FOOTBALL_KEY = os.environ["API_FOOTBALL_KEY"]

url = "https://v3.football.api-sports.io/fixtures"

headers = {
    "x-apisports-key": API_FOOTBALL_KEY
}

params = {
    "league": 1,
    "season": 2026
}

response = requests.get(url, headers=headers, params=params, timeout=30)

print("STATUS CODE:", response.status_code)

data = response.json()

print("ERRORS:", data.get("errors"))
print("RESULTS:", data.get("results"))

fixtures = data.get("response", [])

if not fixtures:
    print("No se encontraron partidos para league=1 season=2026.")
else:
    print(f"Partidos encontrados: {len(fixtures)}")

    for item in fixtures[:20]:
        fixture_id = item["fixture"]["id"]
        fecha = item["fixture"]["date"]
        estado = item["fixture"]["status"]["short"]
        home = item["teams"]["home"]["name"]
        away = item["teams"]["away"]["name"]
        goles_home = item["goals"]["home"]
        goles_away = item["goals"]["away"]

        print(
            f"fixture_id={fixture_id} | {fecha} | {estado} | "
            f"{home} {goles_home} - {goles_away} {away}"
        )
