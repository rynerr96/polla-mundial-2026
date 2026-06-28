import os
import hashlib
import html
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from supabase import create_client


APP_TITLE = "Polla Mundial 2026"
FIXTURE_PATH = "fixture.csv"

# Puntaje base
PUNTOS_MARCADOR_EXACTO = 10
PUNTOS_RESULTADO_CORRECTO = 5
PUNTOS_GOLES_UN_EQUIPO = 2
PUNTOS_DIFERENCIA_GOLES = 3

ADMIN_CODE = os.getenv("ADMIN_CODE", "admin2026")
PERU_TZ = ZoneInfo("America/Lima")


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)


CUSTOM_CSS = """
<style>
:root {
    --blue-dark: #071638;
    --blue-main: #0b2d6b;
    --green-main: #16a34a;
    --gold-main: #facc15;
    --red-main: #dc2626;
    --card-border: #dbeafe;
    --soft-bg: #f8fafc;
}

html, body, [class*="css"] {
    scroll-behavior: smooth;
}

.main .block-container {
    padding-top: 1.1rem;
    padding-bottom: 2rem;
    max-width: 1420px;
}

[data-testid="stSidebar"] {
    background:
        radial-gradient(circle at top left, rgba(250, 204, 21, .15), transparent 26%),
        linear-gradient(180deg, #071638 0%, #0b2d6b 58%, #0f766e 100%);
    border-right: 1px solid rgba(255,255,255,.08);
}

[data-testid="stSidebar"] * {
    color: white !important;
}

[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: .45rem .5rem;
    border-radius: 14px;
    margin-bottom: .25rem;
    transition: all .18s ease;
}

[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(255,255,255,.12);
    transform: translateX(2px);
}

.sidebar-title {
    font-size: 1.15rem;
    font-weight: 900;
    margin-bottom: .2rem;
    color: white;
}

.sidebar-subtitle {
    color: rgba(255,255,255,.72);
    font-size: .82rem;
    line-height: 1.35;
    margin-bottom: 1rem;
}

.hero {
    padding: 2.1rem 2rem;
    border-radius: 30px;
    background:
        radial-gradient(circle at top right, rgba(250, 204, 21, .34), transparent 27%),
        radial-gradient(circle at bottom left, rgba(34, 197, 94, .32), transparent 24%),
        linear-gradient(135deg, #071638 0%, #0b2d6b 42%, #006847 100%);
    color: white;
    box-shadow: 0 22px 52px rgba(7, 22, 56, 0.24);
    margin-bottom: 1.1rem;
    border: 1px solid rgba(255,255,255,.18);
    position: relative;
    overflow: hidden;
}

.hero:after {
    content: "⚽";
    position: absolute;
    right: 3rem;
    bottom: -2.2rem;
    font-size: 8rem;
    opacity: .12;
    transform: rotate(-18deg);
}

.hero h1 {
    margin: 0;
    font-size: 2.7rem;
    letter-spacing: -0.055em;
    font-weight: 950;
    line-height: 1.05;
}

.hero p {
    margin-top: 0.85rem;
    color: #e0f2fe;
    font-size: 1.05rem;
    max-width: 900px;
    line-height: 1.65;
}

.hero-badge {
    display: inline-block;
    background: rgba(250, 204, 21, .98);
    color: #111827;
    padding: .35rem .8rem;
    border-radius: 999px;
    font-weight: 900;
    font-size: .78rem;
    margin-bottom: .9rem;
    letter-spacing: .04em;
}

.stat-card {
    padding: 1.05rem;
    border-radius: 22px;
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    border: 1px solid #dbeafe;
    box-shadow: 0 10px 26px rgba(15, 23, 42, 0.075);
    transition: all .2s ease;
}

.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 16px 34px rgba(15, 23, 42, 0.11);
}

.stat-card .label {
    color: #64748b;
    font-size: 0.83rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: .04em;
}

.stat-card .value {
    color: #071638;
    font-size: 1.85rem;
    font-weight: 950;
}

.small-note {
    color: #64748b;
    font-size: 0.92rem;
}










.match-card {
    border-radius: 24px;
    padding: 1rem 1.1rem;
    background:
        linear-gradient(180deg, rgba(255,255,255,1) 0%, rgba(248,250,252,1) 100%);
    border: 1px solid #dbeafe;
    box-shadow: 0 8px 24px rgba(15, 23, 42, .07);
    margin-bottom: .8rem;
    transition: all .18s ease;
}

.match-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 12px 30px rgba(15, 23, 42, .10);
}

.match-meta {
    color: #64748b;
    font-size: .86rem;
}

.team-name {
    font-size: 1.02rem;
    font-weight: 900;
    color: #0f172a;
}

.winner-tag {
    display: inline-block;
    background: #dcfce7;
    color: #166534;
    padding: 0.18rem 0.65rem;
    border-radius: 999px;
    font-weight: 800;
    border: 1px solid #bbf7d0;
}

.loser-tag {
    display: inline-block;
    background: #fee2e2;
    color: #991b1b;
    padding: 0.18rem 0.65rem;
    border-radius: 999px;
    font-weight: 800;
    border: 1px solid #fecaca;
}

.draw-tag {
    display: inline-block;
    background: #fef9c3;
    color: #854d0e;
    padding: 0.18rem 0.65rem;
    border-radius: 999px;
    font-weight: 800;
    border: 1px solid #fde68a;
}

.footer-note {
    color: #64748b;
    font-size: .82rem;
    line-height: 1.45;
    margin-top: 1.2rem;
}

@media (max-width: 768px) {
    .main .block-container {
        padding-left: .75rem;
        padding-right: .75rem;
        padding-top: .75rem;
    }

    .hero {
        padding: 1.45rem 1.1rem;
        border-radius: 22px;
    }

    .hero h1 {
        font-size: 2rem;
    }

    .hero p {
        font-size: .95rem;
    }

    .hero:after {
        font-size: 5rem;
        right: 1rem;
        bottom: -1.4rem;
    }

    .feature-card {
        min-width: 260px;
    }

    .stat-card {
        margin-bottom: .55rem;
    }

    .team-name {
        font-size: .95rem;
    }
}

/* Corrección de lectura según el tema real de Streamlit.
   Usamos variables internas de Streamlit en lugar de prefers-color-scheme,
   porque en celulares el navegador puede no reportar igual el tema de la app. */
.match-card {
    background: var(--secondary-background-color) !important;
    border: 1px solid rgba(148, 163, 184, .35) !important;
    color: var(--text-color) !important;
}

.team-name,
.team-name *,
.match-card strong,
.match-card h3 {
    color: var(--text-color) !important;
    opacity: 1 !important;
}

.match-meta,
.small-note {
    color: rgba(148, 163, 184, .95) !important;
}

.day-separator {
    margin: 0.8rem 0 1.5rem 0;
    padding: 0.8rem;
    border-radius: 16px;
    background: var(--secondary-background-color) !important;
    border: 1px solid rgba(148, 163, 184, .35) !important;
}

.day-separator b {
    color: var(--text-color) !important;
}

.day-separator span {
    color: rgba(148, 163, 184, .95) !important;
    font-size: 0.9rem;
}

.winner-tag {
    background: #dcfce7 !important;
    color: #166534 !important;
    border: 1px solid #bbf7d0 !important;
}

.loser-tag {
    background: #fee2e2 !important;
    color: #991b1b !important;
    border: 1px solid #fecaca !important;
}

.draw-tag {
    background: #fef9c3 !important;
    color: #854d0e !important;
    border: 1px solid #fde68a !important;
}

.winner-tag *,
.loser-tag *,
.draw-tag * {
    color: inherit !important;
}

</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def get_secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, "")
        if value:
            return value
    except Exception:
        pass
    return os.getenv(name, default)


@st.cache_resource
def get_supabase_client():
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")

    if not url or not key:
        st.error("Faltan SUPABASE_URL y/o SUPABASE_KEY en Streamlit Secrets.")
        st.stop()

    return create_client(url, key)


def hash_code(code: str) -> str:
    return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()


# Reemplazos manuales para cruces de eliminación directa.
# Cuando se conozcan más clasificados, agrega aquí el texto exacto del fixture.csv
# y el nombre exacto de la selección como aparece en TEAM_CODE_MAP.
CLASIFICADOS_MANUALES = {
    "2º Grupo A": "Canadá",
    "2º Grupo B": "Sudáfrica",
}


def resolve_team_name(team: str) -> str:
    team = str(team).strip()
    return CLASIFICADOS_MANUALES.get(team, team)


def apply_resolved_teams(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["equipo_1", "equipo_2"]:
        if col in df.columns:
            df[col] = df[col].apply(resolve_team_name)
    return df


@st.cache_data
def load_fixture():
    df = pd.read_csv(FIXTURE_PATH)
    df["partido"] = df["partido"].astype(int)
    df = apply_resolved_teams(df)
    return df


TEAM_CODE_MAP = {
    "México": "mx",
    "Sudáfrica": "za",
    "República de Corea": "kr",
    "República Checa": "cz",
    "Canadá": "ca",
    "Bosnia": "ba",
    "Estados Unidos": "us",
    "Paraguay": "py",
    "Australia": "au",
    "Turquía": "tr",
    "Catar": "qa",
    "Suiza": "ch",
    "Brasil": "br",
    "Marruecos": "ma",
    "Haití": "ht",
    "Escocia": "gb-sct",
    "Alemania": "de",
    "Curazao": "cw",
    "Países Bajos": "nl",
    "Japón": "jp",
    "Italia": "it",
    "Noruega": "no",
    "Argentina": "ar",
    "Argelia": "dz",
    "Portugal": "pt",
    "Panamá": "pa",
    "Francia": "fr",
    "Senegal": "sn",
    "Inglaterra": "gb-eng",
    "Croacia": "hr",
    "España": "es",
    "Cabo Verde": "cv",
    "Bélgica": "be",
    "Egipto": "eg",
    "Uruguay": "uy",
    "Arabia Saudita": "sa",
    "Colombia": "co",
    "Ghana": "gh",
    "Ecuador": "ec",
    "Costa de Marfil": "ci",
    "Austria": "at",
    "Túnez": "tn",
    "Polonia": "pl",
    "Nueva Zelanda": "nz",
    "Irán": "ir",
    "Uzbekistán": "uz",
    "Jordania": "jo",
}


def flag_img(team: str) -> str:
    team = str(team).strip()
    code = TEAM_CODE_MAP.get(team)

    if not code:
        return "<span style='font-size:1.25rem;margin-right:8px;'>🏳️</span>"

    return (
        f"<img src='https://flagcdn.com/w40/{code}.png' "
        f"alt='{html.escape(team)}' "
        f"style='width:28px;height:20px;object-fit:cover;"
        f"border-radius:4px;margin-right:8px;"
        f"box-shadow:0 1px 3px rgba(0,0,0,.25);vertical-align:-4px;'>"
    )


def team_label(team: str) -> str:
    team = str(team).strip()
    return f"{flag_img(team)}{html.escape(team)}"


def parse_match_start(row):
    fecha = str(row.get("fecha", row.get("Fecha", ""))).strip()
    hora_original = str(row.get("hora_peru", row.get("Hora Perú", ""))).strip().lower()

    if not fecha or fecha.lower() in ["nan", "none"]:
        return None

    hora_match = re.search(r"(\d{1,2}):(\d{2})", hora_original)
    if not hora_match:
        return None

    hour = int(hora_match.group(1))
    minute = int(hora_match.group(2))

    hora_norm = (
        hora_original
        .replace(" ", "")
        .replace("a. m.", "a.m.")
        .replace("p. m.", "p.m.")
        .replace("a.m.", "am")
        .replace("p.m.", "pm")
        .replace("a.m", "am")
        .replace("p.m", "pm")
    )

    if "pm" in hora_norm:
        if hour != 12:
            hour += 12
    elif "am" in hora_norm:
        if hour == 12:
            hour = 0
    elif "m." in hora_original or hora_original.endswith("m"):
        if hour == 12:
            hour = 12

    fecha_hora = f"{fecha} {hour:02d}:{minute:02d}"

    formatos = [
        "%d/%m/%Y %H:%M",
        "%Y-%m-%d %H:%M",
        "%d-%m-%Y %H:%M",
        "%d/%m/%y %H:%M",
    ]

    for fmt in formatos:
        try:
            dt = datetime.strptime(fecha_hora, fmt)
            return dt.replace(tzinfo=PERU_TZ)
        except ValueError:
            pass

    try:
        dt = pd.to_datetime(fecha_hora, dayfirst=True, errors="coerce")
        if pd.isna(dt):
            return None
        return dt.to_pydatetime().replace(tzinfo=PERU_TZ)
    except Exception:
        return None


@st.cache_data(ttl=30)
def get_match_override_map():
    """
    Lee todos los estados manuales una sola vez y los mantiene en caché breve.
    Esto evita consultar Supabase partido por partido y reduce errores httpx.ReadError.
    """
    try:
        supabase = get_supabase_client()
        data = (
            supabase.table("match_overrides")
            .select("match_id,status")
            .execute()
            .data
            or []
        )
        return {int(item["match_id"]): item["status"] for item in data}
    except Exception:
        # Si Supabase tiene una caída temporal, no rompemos la app:
        # seguimos con modo automático por hora oficial.
        return {}


def get_match_override(match_id: int):
    override_map = get_match_override_map()
    return override_map.get(int(match_id), "automatico")


def match_has_started(row, now=None) -> bool:
    match_id = int(row.get("partido", row.get("N°", 0)))
    override = get_match_override(match_id)

    if override == "abierto":
        return False

    if override == "cerrado":
        return True

    start = parse_match_start(row)

    if start is None:
        return False

    now = now or datetime.now(PERU_TZ)
    return now >= start


def match_status_text(row) -> str:
    match_id = int(row.get("partido", row.get("N°", 0)))
    override = get_match_override(match_id)

    if override == "abierto":
        return "🟢 Abierto manualmente"

    if override == "cerrado":
        return "🔒 Cerrado manualmente"

    start = parse_match_start(row)

    if start is None:
        return "Horario no reconocido"

    if match_has_started(row):
        return "🔒 Cerrado por hora oficial"

    return "🟢 Abierto hasta la hora oficial"


def df_from_table(table_name: str, order_col: str | None = None) -> pd.DataFrame:
    try:
        supabase = get_supabase_client()
        query = supabase.table(table_name).select("*")
        if order_col:
            query = query.order(order_col)
        data = query.execute().data or []
        return pd.DataFrame(data)
    except Exception as e:
        st.warning(f"No se pudo leer temporalmente la tabla {table_name}. Intenta actualizar la página. Detalle: {type(e).__name__}")
        return pd.DataFrame()


def get_all_participants():
    df = df_from_table("participants", "name")
    if df.empty:
        return pd.DataFrame(columns=["id", "name", "created_at"])
    return df


def get_participant(name: str):
    name_clean = name.strip().lower()
    participants = get_all_participants()

    if participants.empty:
        return None

    matches = participants[participants["name"].str.lower() == name_clean]

    if matches.empty:
        return None

    return matches.iloc[0].to_dict()


def create_participant(name: str, code: str):
    supabase = get_supabase_client()
    now = datetime.now(PERU_TZ).isoformat(timespec="seconds")

    payload = {
        "name": name.strip(),
        "code_hash": hash_code(code),
        "created_at": now,
    }

    supabase.table("participants").insert(payload).execute()
    return get_participant(name)


def delete_participant(participant_id: int):
    supabase = get_supabase_client()
    supabase.table("predictions").delete().eq("participant_id", int(participant_id)).execute()
    supabase.table("participants").delete().eq("id", int(participant_id)).execute()


def verify_or_register(name: str, code: str):
    name = name.strip()
    code = code.strip()

    if not name or not code:
        return None, "Debes ingresar tu nombre y tu código personal."

    existing = get_participant(name)

    if existing is None:
        try:
            participant = create_participant(name, code)
            return participant, f"Registro creado para {name}."
        except Exception:
            return None, "Ese nombre ya está registrado. Intenta iniciar sesión con tu código."

    if existing["code_hash"] != hash_code(code):
        return None, "El código no coincide con ese participante."

    return existing, f"Bienvenido, {existing['name']}."


def outcome(goals_a, goals_b, team_a, team_b):
    if goals_a is None or goals_b is None or pd.isna(goals_a) or pd.isna(goals_b):
        return "", "", ""

    goals_a = int(goals_a)
    goals_b = int(goals_b)

    if goals_a > goals_b:
        return team_a, team_b, "Equipo 1"
    if goals_b > goals_a:
        return team_b, team_a, "Equipo 2"
    return "Empate", "Empate", "Empate"


def get_predictions(participant_id: int):
    supabase = get_supabase_client()
    data = (
        supabase.table("predictions")
        .select("match_id, goals_a, goals_b")
        .eq("participant_id", int(participant_id))
        .execute()
        .data
        or []
    )
    return pd.DataFrame(data)


def save_predictions(participant_id: int, edited: pd.DataFrame):
    supabase = get_supabase_client()
    now = datetime.now(PERU_TZ).isoformat(timespec="seconds")
    fixture = load_fixture()

    fixture_by_match = {
        int(row["partido"]): row
        for _, row in fixture.iterrows()
    }

    records = []
    blocked_count = 0

    for _, row in edited.iterrows():
        match_id = int(row["partido"])

        fixture_row = fixture_by_match.get(match_id)
        if fixture_row is not None and match_has_started(fixture_row):
            blocked_count += 1
            continue

        ga = row.get("Tu gol equipo 1")
        gb = row.get("Tu gol equipo 2")

        ga = None if pd.isna(ga) else int(ga)
        gb = None if pd.isna(gb) else int(gb)

        if ga is None and gb is None:
            continue

        records.append({
            "participant_id": int(participant_id),
            "match_id": int(match_id),
            "goals_a": ga,
            "goals_b": gb,
            "updated_at": now,
        })

    if records:
        supabase.table("predictions").upsert(
            records,
            on_conflict="participant_id,match_id"
        ).execute()

    return len(records), blocked_count


def get_results():
    df = df_from_table("results")
    if df.empty:
        return pd.DataFrame(columns=["match_id", "goals_a", "goals_b"])
    return df


def save_results(edited: pd.DataFrame):
    supabase = get_supabase_client()
    now = datetime.now(PERU_TZ).isoformat(timespec="seconds")
    records = []

    for _, row in edited.iterrows():
        match_id = int(row["partido"])
        ga = row.get("Gol real equipo 1")
        gb = row.get("Gol real equipo 2")

        ga = None if pd.isna(ga) else int(ga)
        gb = None if pd.isna(gb) else int(gb)

        if ga is None and gb is None:
            continue

        records.append({
            "match_id": match_id,
            "goals_a": ga,
            "goals_b": gb,
            "updated_at": now,
        })

    if records:
        supabase.table("results").upsert(records, on_conflict="match_id").execute()


def get_match_overrides():
    df = df_from_table("match_overrides")
    if df.empty:
        return pd.DataFrame(columns=["match_id", "status"])
    return df


def set_match_override(match_id: int, status: str):
    supabase = get_supabase_client()
    now = datetime.now(PERU_TZ).isoformat(timespec="seconds")

    if status == "automatico":
        supabase.table("match_overrides").delete().eq("match_id", int(match_id)).execute()
    else:
        supabase.table("match_overrides").upsert(
            {
                "match_id": int(match_id),
                "status": status,
                "updated_at": now,
            },
            on_conflict="match_id"
        ).execute()

    # Limpia el caché para que el cambio se vea al instante.
    get_match_override_map.clear()


def calculate_points(pred_a, pred_b, real_a, real_b):
    if pd.isna(pred_a) or pd.isna(pred_b) or pd.isna(real_a) or pd.isna(real_b):
        return 0

    pred_a, pred_b, real_a, real_b = int(pred_a), int(pred_b), int(real_a), int(real_b)

    if pred_a == real_a and pred_b == real_b:
        return PUNTOS_MARCADOR_EXACTO

    points = 0

    pred_sign = (pred_a > pred_b) - (pred_a < pred_b)
    real_sign = (real_a > real_b) - (real_a < real_b)

    if pred_sign == real_sign:
        points += PUNTOS_RESULTADO_CORRECTO

    if pred_a == real_a:
        points += PUNTOS_GOLES_UN_EQUIPO

    if pred_b == real_b:
        points += PUNTOS_GOLES_UN_EQUIPO

    if (pred_a - pred_b) == (real_a - real_b):
        points += PUNTOS_DIFERENCIA_GOLES

    return points


def build_ranking():
    results = get_results().rename(columns={"match_id": "partido", "goals_a": "real_a", "goals_b": "real_b"})
    participants = get_all_participants()
    predictions = df_from_table("predictions").rename(columns={"goals_a": "pred_a", "goals_b": "pred_b"})

    if participants.empty:
        return pd.DataFrame(columns=["Puesto", "Participante", "Puntaje", "Pronósticos llenados"])

    if predictions.empty:
        scores = []
        for _, p in participants.iterrows():
            scores.append({
                "Participante": p["name"],
                "Puntaje": 0,
                "Pronósticos llenados": 0,
            })
        ranking = pd.DataFrame(scores).sort_values("Participante").reset_index(drop=True)
        ranking.insert(0, "Puesto", ranking.index + 1)
        return ranking

    merged = predictions.merge(results, left_on="match_id", right_on="partido", how="left")

    scores = []
    for _, p in participants.iterrows():
        p_preds = merged[merged["participant_id"] == p["id"]].copy()
        total = 0

        for _, row in p_preds.iterrows():
            total += calculate_points(row["pred_a"], row["pred_b"], row["real_a"], row["real_b"])

        scores.append({
            "Participante": p["name"],
            "Puntaje": int(total),
            "Pronósticos llenados": int(len(p_preds)),
        })

    ranking = pd.DataFrame(scores).sort_values(
        ["Puntaje", "Pronósticos llenados", "Participante"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    ranking.insert(0, "Puesto", ranking.index + 1)
    return ranking


def hero():
    st.markdown(
        """
        <div class="hero">
            <div class="hero-badge">MUNDIAL FIFA 2026 · PRONÓSTICOS</div>
            <h1>⚽ Polla Mundialista 2026</h1>
            <p>Registra tus marcadores, revisa la tabla de posiciones y compite partido a partido en una experiencia rápida, clara y pensada para usar desde el celular.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )




def stat_cards():
    fixture = load_fixture()
    participants = get_all_participants()
    results = get_results()
    ranking = build_ranking()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="stat-card"><div class="label">Partidos</div><div class="value">{len(fixture)}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-card"><div class="label">Participantes</div><div class="value">{len(participants)}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-card"><div class="label">Resultados cargados</div><div class="value">{len(results)}</div></div>', unsafe_allow_html=True)
    with c4:
        leader = "—" if ranking.empty else ranking.iloc[0]["Participante"]
        st.markdown(f'<div class="stat-card"><div class="label">Líder actual</div><div class="value" style="font-size:1.2rem;">{leader}</div></div>', unsafe_allow_html=True)


def participant_page():
    st.subheader("👤 Registro e ingreso de participante")
    st.caption("Cada participante entra con su nombre y un código personal. El código evita que otra persona cambie sus pronósticos.")

    with st.form("login_form", clear_on_submit=False):
        name = st.text_input("Nombre del participante")
        code = st.text_input("Código personal", type="password", help="Puede ser un código simple, por ejemplo 1234. Guárdalo.")
        submitted = st.form_submit_button("Ingresar / Registrarme")

    if submitted:
        participant, msg = verify_or_register(name, code)
        if participant:
            st.session_state["participant_id"] = int(participant["id"])
            st.session_state["participant_name"] = participant["name"]
            st.session_state["redirect_to_forecasts"] = True
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    if st.session_state.get("participant_id"):
        st.info(f"Sesión activa: {st.session_state['participant_name']}")
        if st.button("Cerrar sesión"):
            st.session_state.pop("participant_id", None)
            st.session_state.pop("participant_name", None)
            st.session_state["redirect_to_participant"] = True
            st.rerun()


def forecasts_page():
    if not st.session_state.get("participant_id"):
        st.warning("Primero debes ingresar o registrarte en la sección Participante.")
        return

    st.subheader(f"📝 Mis pronósticos: {st.session_state['participant_name']}")
    st.caption("Coloca solo los goles. Cada pronóstico se cierra automáticamente cuando inicia el partido.")

    fixture = load_fixture()
    predictions = get_predictions(st.session_state["participant_id"])

    if not predictions.empty:
        predictions = predictions.rename(
            columns={"match_id": "partido", "goals_a": "pred_a", "goals_b": "pred_b"}
        )

    data = fixture.merge(predictions, on="partido", how="left") if not predictions.empty else fixture.copy()
    if "pred_a" not in data.columns:
        data["pred_a"] = None
    if "pred_b" not in data.columns:
        data["pred_b"] = None

    data["fecha_dt"] = pd.to_datetime(data["fecha"], errors="coerce")

    st.markdown("### Filtros rápidos")

    f1, f2, f3 = st.columns([1.4, 1.3, 1.3])

    with f1:
        rango = st.radio(
            "Mostrar",
            ["Próximos 3 días", "Hoy", "Próximos 7 días", "Todos"],
            horizontal=False,
            key="forecast_range_filter",
        )

    with f2:
        mostrar_cerrados = st.checkbox(
            "Mostrar partidos cerrados",
            value=False,
            help="Por defecto se ocultan los partidos que ya iniciaron para reducir el scroll.",
            key="show_closed_matches",
        )

    with f3:
        agrupar_por_fecha = st.checkbox(
            "Agrupar por día",
            value=True,
            help="Recomendado para celular.",
            key="group_by_date_forecasts",
        )

    fase_options = ["Todas"] + sorted(data["fase"].dropna().unique().tolist())
    fase = st.selectbox("Filtrar por fase", fase_options)

    if fase != "Todas":
        data = data[data["fase"] == fase].copy()

    group_options = ["Todos"] + sorted([g for g in data["grupo"].dropna().unique().tolist() if str(g).strip()])
    grupo = st.selectbox("Filtrar por grupo", group_options)

    if grupo != "Todos":
        data = data[data["grupo"] == grupo].copy()

    now = datetime.now(PERU_TZ)
    today = pd.Timestamp(now.date())

    if rango != "Todos":
        if rango == "Hoy":
            start_date = today
            end_date = today
        elif rango == "Próximos 3 días":
            start_date = today
            end_date = today + pd.Timedelta(days=2)
        else:
            start_date = today
            end_date = today + pd.Timedelta(days=6)

        data = data[
            (data["fecha_dt"].notna())
            & (data["fecha_dt"] >= start_date)
            & (data["fecha_dt"] <= end_date)
        ].copy()

    if not mostrar_cerrados and not data.empty:
        data = data[~data.apply(match_has_started, axis=1)].copy()

    data = data.sort_values(["fecha_dt", "partido"]).reset_index(drop=True)

    visible_matches = len(data)
    if visible_matches == 0:
        st.info("No hay partidos para mostrar con los filtros actuales. Puedes activar 'Mostrar partidos cerrados' o cambiar el rango a 'Todos'.")
        return

    st.markdown("### Marcadores")
    st.markdown(
        f"<p class='small-note'>Mostrando <b>{visible_matches}</b> partido(s). Llena los goles de cada selección. La app muestra al instante el ganador y el perdedor.</p>",
        unsafe_allow_html=True,
    )

    def guardar_pronosticos_actuales(match_ids=None):
        temp_rows = []

        if match_ids is None:
            rows_source = data
        else:
            rows_source = data[data["partido"].astype(int).isin([int(x) for x in match_ids])]

        for _, r in rows_source.iterrows():
            mid = int(r["partido"])
            temp_rows.append({
                "partido": mid,
                "Tu gol equipo 1": st.session_state.get(f"pred_a_{mid}"),
                "Tu gol equipo 2": st.session_state.get(f"pred_b_{mid}"),
            })

        temp_df = pd.DataFrame(temp_rows)
        saved_count, blocked_count = save_predictions(st.session_state["participant_id"], temp_df)

        if saved_count > 0:
            st.success(f"Pronósticos guardados correctamente: {saved_count} partido(s).")
        else:
            st.info("No se guardaron nuevos pronósticos.")

        if blocked_count > 0:
            st.warning(f"{blocked_count} partido(s) ya estaban cerrados y no fueron modificados.")

        st.rerun()

    def render_match_card(row):
        match_id = int(row["partido"])
        team_a = row["equipo_1"]
        team_b = row["equipo_2"]

        default_a = None if pd.isna(row.get("pred_a")) else int(row.get("pred_a"))
        default_b = None if pd.isna(row.get("pred_b")) else int(row.get("pred_b"))
        started = match_has_started(row)
        status_text = match_status_text(row)

        st.markdown('<div class="match-card">', unsafe_allow_html=True)

        top1, top2 = st.columns([1.1, 4.9])
        with top1:
            st.markdown(f"**N° {match_id}**")
            st.markdown(f"<div class='match-meta'>{row['fecha']} · {row['hora_peru']}</div>", unsafe_allow_html=True)
            if started:
                st.markdown(f"<span class='loser-tag'>{status_text}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span class='winner-tag'>{status_text}</span>", unsafe_allow_html=True)
        with top2:
            st.markdown(f"**{row['fase']}**")
            st.markdown(f"<div class='match-meta'>{row['grupo']} · {row['sede']}</div>", unsafe_allow_html=True)

        c1, c2, c3, c4, c5 = st.columns([2.4, 1.05, 0.35, 1.05, 2.4])

        with c1:
            st.markdown(f"<div class='team-name'>{team_label(team_a)}</div>", unsafe_allow_html=True)
        with c2:
            ga = st.number_input(
                "Goles equipo 1",
                min_value=0,
                max_value=20,
                step=1,
                value=default_a,
                placeholder="",
                label_visibility="collapsed",
                key=f"pred_a_{match_id}",
                disabled=started,
            )
        with c3:
            st.markdown("<h3 style='text-align:center;margin-top:0.05rem;'>-</h3>", unsafe_allow_html=True)
        with c4:
            gb = st.number_input(
                "Goles equipo 2",
                min_value=0,
                max_value=20,
                step=1,
                value=default_b,
                placeholder="",
                label_visibility="collapsed",
                key=f"pred_b_{match_id}",
                disabled=started,
            )
        with c5:
            st.markdown(f"<div class='team-name'>{team_label(team_b)}</div>", unsafe_allow_html=True)

        winner, loser, _ = outcome(ga, gb, team_a, team_b)

        r1, r2 = st.columns(2)
        with r1:
            if winner == "Empate":
                st.markdown("Resultado: <span class='draw-tag'>Empate</span>", unsafe_allow_html=True)
            elif winner:
                st.markdown(f"Ganador: <span class='winner-tag'>{team_label(winner)}</span>", unsafe_allow_html=True)
            else:
                st.markdown("Ganador: —")
        with r2:
            if loser == "Empate":
                st.markdown("Perdedor: <span class='draw-tag'>No aplica</span>", unsafe_allow_html=True)
            elif loser:
                st.markdown(f"Perdedor: <span class='loser-tag'>{team_label(loser)}</span>", unsafe_allow_html=True)
            else:
                st.markdown("Perdedor: —")

        st.markdown('</div>', unsafe_allow_html=True)

        return {
            "partido": match_id,
            "Tu gol equipo 1": ga,
            "Tu gol equipo 2": gb,
        }

    edited_rows = []

    if agrupar_por_fecha:
        grouped = list(data.groupby("fecha", sort=False))

        for idx, (fecha, day_data) in enumerate(grouped):
            day_match_ids = [int(x) for x in day_data["partido"].tolist()]
            day_label = f"📅 {fecha} · {len(day_data)} partido(s)"
            expanded = idx == 0

            with st.expander(day_label, expanded=expanded):
                for _, row in day_data.iterrows():
                    edited_rows.append(render_match_card(row))

                st.markdown(
                    "<div class='day-separator'>"
                    "<b>Fin de partidos de esta fecha.</b><br>"
                    "<span>Puedes guardar solo los pronósticos de este día.</span>"
                    "</div>",
                    unsafe_allow_html=True,
                )

                if st.button(
                    f"💾 Guardar pronósticos del {fecha}",
                    type="primary",
                    key=f"save_predictions_day_{fecha}",
                ):
                    guardar_pronosticos_actuales(day_match_ids)
    else:
        for _, row in data.iterrows():
            edited_rows.append(render_match_card(row))

    edited = pd.DataFrame(edited_rows)

    st.divider()

    if st.button("💾 Guardar todos mis pronósticos visibles", type="primary", key="save_predictions_bottom"):
        guardar_pronosticos_actuales()



def admin_page():
    st.subheader("🔐 Administrador: resultados reales")
    st.caption("Aquí se cargan los marcadores oficiales para calcular el ranking.")

    admin_code = st.text_input("Código de administrador", type="password")

    if admin_code != ADMIN_CODE:
        st.info("Ingresa el código de administrador para editar resultados.")
        return

    fixture = load_fixture()
    results = get_results().rename(
        columns={"match_id": "partido", "goals_a": "Gol real equipo 1", "goals_b": "Gol real equipo 2"}
    )

    data = fixture.merge(results, on="partido", how="left")
    data["Ganador real"] = data.apply(
        lambda r: outcome(r["Gol real equipo 1"], r["Gol real equipo 2"], r["equipo_1"], r["equipo_2"])[0],
        axis=1,
    )
    data["Perdedor real"] = data.apply(
        lambda r: outcome(r["Gol real equipo 1"], r["Gol real equipo 2"], r["equipo_1"], r["equipo_2"])[1],
        axis=1,
    )

    view = data[[
        "partido", "fase", "fecha", "hora_peru", "grupo", "equipo_1",
        "Gol real equipo 1", "Gol real equipo 2", "equipo_2",
        "Ganador real", "Perdedor real", "sede"
    ]].copy()

    edited = st.data_editor(
        view,
        use_container_width=True,
        hide_index=True,
        column_config={
            "partido": st.column_config.NumberColumn("N°", disabled=True),
            "fase": st.column_config.TextColumn("Fase", disabled=True),
            "fecha": st.column_config.TextColumn("Fecha", disabled=True),
            "hora_peru": st.column_config.TextColumn("Hora Perú", disabled=True),
            "grupo": st.column_config.TextColumn("Grupo", disabled=True),
            "equipo_1": st.column_config.TextColumn("Equipo 1", disabled=True),
            "equipo_2": st.column_config.TextColumn("Equipo 2", disabled=True),
            "Gol real equipo 1": st.column_config.NumberColumn("Goles reales Eq. 1", min_value=0, max_value=20, step=1),
            "Gol real equipo 2": st.column_config.NumberColumn("Goles reales Eq. 2", min_value=0, max_value=20, step=1),
            "Ganador real": st.column_config.TextColumn("Ganador", disabled=True),
            "Perdedor real": st.column_config.TextColumn("Perdedor", disabled=True),
            "sede": st.column_config.TextColumn("Sede", disabled=True),
        },
        disabled=["partido", "fase", "fecha", "hora_peru", "grupo", "equipo_1", "equipo_2", "Ganador real", "Perdedor real", "sede"],
    )

    if st.button("💾 Guardar resultados reales", type="primary"):
        save_results(edited)
        st.success("Resultados guardados correctamente.")
        st.rerun()

    st.divider()
    st.subheader("🔒 Apertura y cierre manual de partidos")
    st.caption("La app cierra automáticamente por hora oficial Perú. Aquí puedes forzar un partido como cerrado o abierto si ocurre un retraso, error de horario o caso especial.")

    fixture_admin_status = load_fixture().copy()
    overrides_df = get_match_overrides()

    if not overrides_df.empty:
        fixture_admin_status = fixture_admin_status.merge(
            overrides_df.rename(columns={"match_id": "partido"}),
            on="partido",
            how="left"
        )
    else:
        fixture_admin_status["status"] = None

    fixture_admin_status["Estado actual"] = fixture_admin_status.apply(match_status_text, axis=1)

    fixture_admin_status["Partido"] = fixture_admin_status.apply(
        lambda r: f"N° {int(r['partido'])} - {r['equipo_1']} vs {r['equipo_2']} | {r['fecha']} {r['hora_peru']}",
        axis=1
    )

    selected_match_label = st.selectbox(
        "Selecciona el partido",
        fixture_admin_status["Partido"].tolist(),
        key="manual_match_select"
    )

    selected_match_id = int(
        fixture_admin_status.loc[
            fixture_admin_status["Partido"] == selected_match_label,
            "partido"
        ].iloc[0]
    )

    selected_row = fixture_admin_status[
        fixture_admin_status["partido"] == selected_match_id
    ].iloc[0]

    st.info(f"Estado actual: {match_status_text(selected_row)}")

    c_auto, c_open, c_close = st.columns(3)

    with c_auto:
        if st.button("⏱️ Usar cierre automático", key="btn_auto_match"):
            set_match_override(selected_match_id, "automatico")
            st.success("El partido volvió al modo automático por hora oficial Perú.")
            st.rerun()

    with c_open:
        if st.button("🟢 Abrir manualmente", key="btn_open_match"):
            set_match_override(selected_match_id, "abierto")
            st.success("Partido abierto manualmente. Los participantes podrán registrar o modificar este pronóstico.")
            st.rerun()

    with c_close:
        if st.button("🔒 Cerrar manualmente", key="btn_close_match"):
            set_match_override(selected_match_id, "cerrado")
            st.success("Partido cerrado manualmente. Ya no se podrán modificar pronósticos de este partido.")
            st.rerun()

    with st.expander("Ver estado de todos los partidos"):
        status_view = fixture_admin_status[[
            "partido", "fase", "fecha", "hora_peru", "grupo",
            "equipo_1", "equipo_2", "Estado actual"
        ]].rename(columns={
            "partido": "N°",
            "fase": "Fase",
            "fecha": "Fecha",
            "hora_peru": "Hora Perú",
            "grupo": "Grupo",
            "equipo_1": "Equipo 1",
            "equipo_2": "Equipo 2",
        })
        st.dataframe(status_view, hide_index=True, use_container_width=True)

    st.divider()
    st.subheader("👥 Gestión de participantes")
    st.caption("Desde aquí puedes eliminar usuarios de prueba. Al eliminar un participante, también se borran sus pronósticos.")

    participants = get_all_participants()

    if participants.empty:
        st.info("No hay participantes registrados.")
    else:
        selected_name = st.selectbox(
            "Selecciona participante para eliminar",
            participants["name"].tolist(),
            key="delete_participant_select"
        )

        selected_id = int(
            participants.loc[participants["name"] == selected_name, "id"].iloc[0]
        )

        confirm_delete = st.checkbox(
            f"Confirmo que deseo eliminar a {selected_name}",
            key="confirm_delete_participant"
        )

        if st.button("🗑️ Eliminar participante", type="secondary"):
            if confirm_delete:
                delete_participant(selected_id)
                st.success(f"Participante {selected_name} eliminado correctamente.")
                st.rerun()
            else:
                st.warning("Marca la confirmación antes de eliminar.")


def ranking_page():
    st.subheader("🏆 Ranking general")
    ranking = build_ranking()

    if ranking.empty:
        st.info("Aún no hay participantes registrados.")
        return

    st.dataframe(ranking, hide_index=True, use_container_width=True)

    st.markdown("### Reglas de puntaje")
    st.write(
        f"""
        - Marcador exacto: **{PUNTOS_MARCADOR_EXACTO} puntos**
        - Resultado correcto sin marcador exacto: **{PUNTOS_RESULTADO_CORRECTO} puntos**
        - Goles exactos de un equipo: **{PUNTOS_GOLES_UN_EQUIPO} puntos**
        - Diferencia de goles correcta: **{PUNTOS_DIFERENCIA_GOLES} puntos**
        """
    )


def fixture_page():
    st.subheader("📅 Fixture Mundial 2026")
    fixture = load_fixture().copy()

    fixture = fixture.rename(columns={
        "partido": "N°",
        "fase": "Fase",
        "fecha": "Fecha",
        "hora_peru": "Hora Perú",
        "grupo": "Grupo",
        "equipo_1": "Equipo 1",
        "equipo_2": "Equipo 2",
        "sede": "Sede",
    })

    st.dataframe(fixture, hide_index=True, use_container_width=True)


def main():
    hero()
    stat_cards()

    admin_mode = st.query_params.get("admin", "") == "1"

    menu_items = ["Participante", "Mis pronósticos", "Ranking", "Fixture"]
    if admin_mode:
        menu_items.append("Administrador")

    if st.session_state.pop("redirect_to_forecasts", False):
        st.session_state["menu"] = "Mis pronósticos"

    if st.session_state.pop("redirect_to_participant", False):
        st.session_state["menu"] = "Participante"

    if "menu" not in st.session_state or st.session_state["menu"] not in menu_items:
        st.session_state["menu"] = "Participante"

    st.sidebar.markdown('<div class="sidebar-title">🏆 Polla Mundial</div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sidebar-subtitle">Pronósticos, ranking y fixture del Mundial 2026.</div>', unsafe_allow_html=True)

    menu_labels = {
        "Participante": "👤 Participante",
        "Mis pronósticos": "📝 Mis pronósticos",
        "Ranking": "🏆 Ranking",
        "Fixture": "📅 Fixture",
        "Administrador": "🔐 Administrador",
    }

    menu = st.sidebar.radio(
        "Menú",
        menu_items,
        index=menu_items.index(st.session_state["menu"]),
        key="menu",
        format_func=lambda x: menu_labels.get(x, x)
    )

    if menu == "Participante":
        participant_page()
    elif menu == "Mis pronósticos":
        forecasts_page()
    elif menu == "Ranking":
        ranking_page()
    elif menu == "Administrador":
        admin_page()
    elif menu == "Fixture":
        fixture_page()

    st.sidebar.divider()
    st.sidebar.caption("Concurso recreativo de pronósticos. No administra pagos ni apuestas.")


if __name__ == "__main__":
    main()

