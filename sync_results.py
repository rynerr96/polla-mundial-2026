import os
import re
import html
import requests
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from supabase import create_client


PERU_TZ = ZoneInfo("America/Lima")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

ELNINE_BASE_URL = "https://api.elnine.com.ar/schedule"


TEAM_ALIASES = {
    "mexico": "mexico",
    "méxico": "mexico",

    "sudafrica": "sudafrica",
    "sudáfrica": "sudafrica",
    "south africa": "sudafrica",

    "republica de corea": "corea del sur",
    "república de corea": "corea del sur",
    "corea del sur": "corea del sur",
    "south korea": "corea del sur",

    "republica checa": "republica checa",
    "república checa": "republica checa",
    "czech republic": "republica checa",
    "czechia": "republica checa",

    "canada": "canada",
    "canadá": "canada",

    "bosnia": "bosnia y herzegovina",
    "bosnia & herzergovina": "bosnia y herzegovina",
    "bosnia & herzegovina": "bosnia y herzegovina",
    "bosnia y herzegovina": "bosnia y herzegovina",

    "catar": "qatar",
    "qatar": "qatar",

    "suiza": "suiza",
    "switzerland": "suiza",

    "estados unidos": "estados unidos",
    "usa": "estados unidos",
    "united states": "estados unidos",

    "turquia": "turquia",
    "turquía": "turquia",
    "turkey": "turquia",

    "paises bajos": "paises bajos",
    "países bajos": "paises bajos",
    "netherlands": "paises bajos",

    "curazao": "curazao",
    "curaçao": "curazao",

    "costa de marfil": "costa de marfil",
    "ivory coast": "costa de marfil",

    "cabo verde": "cabo verde",
    "cape verde": "cabo verde",

    "arabia saudita": "arabia saudita",
    "saudi arabia": "arabia saudita",

    "nueva zelanda": "nueva zelanda",
    "new zealand": "nueva zelanda",

    "inglaterra": "inglaterra",
    "england": "inglaterra",

    "escocia": "escocia",
    "scotland": "escocia",

    "alemania": "alemania",
    "germany": "alemania",

    "espana": "espana",
    "españa": "espana",
    "spain": "espana",

    "marruecos": "marruecos",
    "morocco": "marruecos",

    "haiti": "haiti",
    "haití": "haiti",

    "japon": "japon",
    "japón": "japon",
    "japan": "japon",

    "belgica": "belgica",
    "bélgica": "belgica",
    "belgium": "belgica",

    "egipto": "egipto",
    "egypt": "egipto",

    "irak": "irak",
    "iraq": "irak",

    "polonia": "polonia",
    "poland": "polonia",
}


def normalize_team(name: str) -> str:
    if name is None:
        return ""

    value = str(name).strip().lower()

    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n",
        "ç": "c",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    return TEAM_ALIASES.get(value, value)


def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def read_fixture():
    df = pd.read_csv("fixture.csv")
    df["partido"] = df["partido"].astype(int)
    df["fecha"] = df["fecha"].astype(str)
    return df


def get_existing_results():
    supabase = get_supabase()
    data = supabase.table("results").select("match_id").execute().data or []
    return {int(item["match_id"]) for item in data}


def fetch_schedule(date_value: str):
    response = requests.get(
        ELNINE_BASE_URL,
        params={"date": date_value},
        headers={
            "accept": "application/json",
            "user-agent": "Mozilla/5.0"
        },
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


def save_result(match_id: int, goals_a: int, goals_b: int):
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


def find_api_match(row, api_matches):
    team_a = normalize_team(row["equipo_1"])
    team_b = normalize_team(row["equipo_2"])

    for item in api_matches:
        if item.get("tournamentCalendarSlug") != "fifa-world-cup":
            continue

        home = normalize_team(item.get("homeTeam", {}).get("name"))
        away = normalize_team(item.get("awayTeam", {}).get("name"))

        same_order = home == team_a and away == team_b
        reverse_order = home == team_b and away == team_a

        if same_order or reverse_order:
            return item, reverse_order

    return None, False


def sync_results():
    fixture = read_fixture()
    existing_results = get_existing_results()

    dates = sorted(fixture["fecha"].dropna().unique().tolist())

    updated = 0
    checked = 0

    for date_value in dates:
        try:
            schedule = fetch_schedule(date_value)
        except Exception as e:
            print(f"Error consultando fecha {date_value}: {repr(e)}")
            continue

        api_matches = schedule.get("matches", [])

        day_fixture = fixture[fixture["fecha"] == date_value]

        for _, row in day_fixture.iterrows():
            match_id = int(row["partido"])

            if match_id in existing_results:
                continue

            api_match, reverse_order = find_api_match(row, api_matches)
            checked += 1

            if not api_match:
                print(
                    f"No se encontró partido API para N° {match_id}: "
                    f"{row['equipo_1']} vs {row['equipo_2']} / fecha {date_value}"
                )
                continue

            status = api_match.get("status")
            period = api_match.get("period")
            home_score = api_match.get("homeScore")
            away_score = api_match.get("awayScore")

            print(
                f"N° {match_id}: {row['equipo_1']} vs {row['equipo_2']} | "
                f"API status={status}, period={period}, marcador={home_score}-{away_score}"
            )

            if status == "finished" and period in ["FT", "AET", "PEN"]:
                if home_score is None or away_score is None:
                    continue

                if reverse_order:
                    goals_a = away_score
                    goals_b = home_score
                else:
                    goals_a = home_score
                    goals_b = away_score

                save_result(match_id, goals_a, goals_b)
                updated += 1
                existing_results.add(match_id)

                print(f"Resultado guardado: partido {match_id} = {goals_a}-{goals_b}")

    print(f"Sincronización terminada. Revisados: {checked}. Actualizados: {updated}.")


if __name__ == "__main__":
    sync_results()
