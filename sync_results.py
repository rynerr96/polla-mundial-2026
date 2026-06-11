import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from supabase import create_client


PERU_TZ = ZoneInfo("America/Lima")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
API_FOOTBALL_KEY = os.environ["API_FOOTBALL_KEY"]

API_BASE_URL = "https://v3.football.api-sports.io"


# OJO:
# Esta lista la vamos a completar bien después, cuando confirmemos los fixture_id reales de API-Football.
# Por ahora dejamos una lista vacía para probar conexión sin modificar resultados.
MATCH_MAP = {
    # Ejemplo futuro:
    # 1: 123456,
    # 2: 123457,
}


def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_api_fixture(api_fixture_id: int):
    headers = {
        "x-apisports-key": API_FOOTBALL_KEY
    }

    params = {
        "id": api_fixture_id
    }

    response = requests.get(
        f"{API_BASE_URL}/fixtures",
        headers=headers,
        params=params,
        timeout=30
    )

    response.raise_for_status()
    data = response.json()

    return data.get("response", [])


def save_result_to_supabase(match_id: int, goals_a: int, goals_b: int):
    supabase = get_supabase()
    now = datetime.now(PERU_TZ).isoformat(timespec="seconds")

    payload = {
        "match_id": int(match_id),
        "goals_a": int(goals_a),
        "goals_b": int(goals_b),
        "updated_at": now,
    }

    supabase.table("results").upsert(
        payload,
        on_conflict="match_id"
    ).execute()


def sync_results():
    if not MATCH_MAP:
        print("MATCH_MAP está vacío. Conexión lista, pero todavía no hay partidos enlazados.")
        return

    updated = 0

    for match_id, api_fixture_id in MATCH_MAP.items():
        fixtures = get_api_fixture(api_fixture_id)

        if not fixtures:
            print(f"No se encontró fixture API para partido interno {match_id}.")
            continue

        item = fixtures[0]

        status_short = item["fixture"]["status"]["short"]
        home_goals = item["goals"]["home"]
        away_goals = item["goals"]["away"]

        print(
            f"Partido interno {match_id} / API {api_fixture_id} "
            f"estado={status_short} marcador={home_goals}-{away_goals}"
        )

        # FT = Full Time / partido finalizado
        # AET = After Extra Time
        # PEN = Penalties
        if status_short in ["FT", "AET", "PEN"] and home_goals is not None and away_goals is not None:
            save_result_to_supabase(match_id, home_goals, away_goals)
            updated += 1

    print(f"Sincronización terminada. Resultados actualizados: {updated}")


if __name__ == "__main__":
    sync_results()
