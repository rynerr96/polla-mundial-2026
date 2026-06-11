import os
import sqlite3
import hashlib
import html
import re
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

APP_TITLE = "Polla Mundial 2026"
DB_PATH = Path("polla_mundial_2026.db")
FIXTURE_PATH = Path("fixture.csv")

# Puntaje base. Puedes cambiarlo luego.
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
}

.main .block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1350px;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #071638 0%, #0b2d6b 60%, #0f766e 100%);
}

[data-testid="stSidebar"] * {
    color: white !important;
}

.hero {
    padding: 2rem 2rem;
    border-radius: 28px;
    background:
        radial-gradient(circle at top right, rgba(250, 204, 21, .35), transparent 28%),
        radial-gradient(circle at bottom left, rgba(34, 197, 94, .35), transparent 24%),
        linear-gradient(135deg, #071638 0%, #0b2d6b 45%, #006847 100%);
    color: white;
    box-shadow: 0 20px 45px rgba(7, 22, 56, 0.26);
    margin-bottom: 1.1rem;
    border: 1px solid rgba(255,255,255,.18);
}

.hero h1 {
    margin: 0;
    font-size: 2.55rem;
    letter-spacing: -0.05em;
    font-weight: 900;
}

.hero p {
    margin-top: 0.65rem;
    color: #e0f2fe;
    font-size: 1.05rem;
    max-width: 900px;
}

.hero-badge {
    display: inline-block;
    background: rgba(250, 204, 21, .95);
    color: #111827;
    padding: .3rem .75rem;
    border-radius: 999px;
    font-weight: 800;
    font-size: .78rem;
    margin-bottom: .8rem;
    letter-spacing: .03em;
}

.stat-card {
    padding: 1rem;
    border-radius: 20px;
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    border: 1px solid #dbeafe;
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.stat-card .label {
    color: #64748b;
    font-size: 0.84rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .03em;
}

.stat-card .value {
    color: #071638;
    font-size: 1.75rem;
    font-weight: 900;
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

.flag {
    font-size: 1.35rem;
    margin-right: .35rem;
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

.admin-link-note {
    color: #64748b;
    font-size: .85rem;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def hash_code(code: str) -> str:
    return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            code_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            participant_id INTEGER NOT NULL,
            match_id INTEGER NOT NULL,
            goals_a INTEGER,
            goals_b INTEGER,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (participant_id, match_id),
            FOREIGN KEY (participant_id) REFERENCES participants(id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS results (
            match_id INTEGER PRIMARY KEY,
            goals_a INTEGER,
            goals_b INTEGER,
            updated_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


@st.cache_data
def load_fixture():
    df = pd.read_csv(FIXTURE_PATH)
    df["partido"] = df["partido"].astype(int)
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

    # Usamos imágenes reales para evitar que Windows muestre banderas blancas.
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


def team_flag(team: str) -> str:
    return flag_img(team)


def parse_match_start(row):
    """
    Convierte la fecha y hora del fixture a datetime con zona horaria de Perú.
    Funciona con formatos como:
    - 11/06/2026 + 14:00
    - 2026-06-11 + 14:00
    - 11-06-2026 + 14:00
    Si no puede interpretar la fecha/hora, devuelve None.
    """
    fecha = str(row.get("fecha", row.get("Fecha", ""))).strip()
    hora = str(row.get("hora_peru", row.get("Hora Perú", ""))).strip()

    if not fecha or fecha.lower() in ["nan", "none"]:
        return None

    # Extrae una hora tipo 14:00 aunque venga con texto adicional.
    hora_match = re.search(r"(\d{1,2}):(\d{2})", hora)
    hora_limpia = hora_match.group(0) if hora_match else "00:00"

    fecha_hora = f"{fecha} {hora_limpia}"

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

    # Último intento usando pandas, por si la fecha viene en otro formato.
    try:
        dt = pd.to_datetime(fecha_hora, dayfirst=True, errors="coerce")
        if pd.isna(dt):
            return None
        return dt.to_pydatetime().replace(tzinfo=PERU_TZ)
    except Exception:
        return None


def match_has_started(row, now=None) -> bool:
    """
    Devuelve True si el partido ya empezó según fecha y hora Perú.
    """
    start = parse_match_start(row)

    if start is None:
        # Si no se puede leer la fecha, no bloqueamos para evitar errores.
        return False

    now = now or datetime.now(PERU_TZ)
    return now >= start


def match_status_text(row) -> str:
    start = parse_match_start(row)

    if start is None:
        return "Horario no reconocido"

    if match_has_started(row):
        return "🔒 Pronóstico cerrado"

    return "🟢 Pronóstico abierto"


def get_participant(name: str):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM participants WHERE LOWER(name)=LOWER(?)",
        (name.strip(),),
    ).fetchone()
    conn.close()
    return row


def create_participant(name: str, code: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO participants(name, code_hash, created_at) VALUES (?, ?, ?)",
        (name.strip(), hash_code(code), datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM participants WHERE LOWER(name)=LOWER(?)",
        (name.strip(),),
    ).fetchone()
    conn.close()
    return row


def get_all_participants():
    conn = get_conn()
    df = pd.read_sql_query("SELECT id, name, created_at FROM participants ORDER BY name", conn)
    conn.close()
    return df


def delete_participant(participant_id: int):
    conn = get_conn()
    cur = conn.cursor()

    # Primero elimina sus pronósticos para que desaparezca del ranking.
    cur.execute("DELETE FROM predictions WHERE participant_id=?", (participant_id,))

    # Luego elimina al participante.
    cur.execute("DELETE FROM participants WHERE id=?", (participant_id,))

    conn.commit()
    conn.close()


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
        except sqlite3.IntegrityError:
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
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT match_id, goals_a, goals_b FROM predictions WHERE participant_id=?",
        conn,
        params=(participant_id,),
    )
    conn.close()
    return df


def save_predictions(participant_id: int, edited: pd.DataFrame):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.now(PERU_TZ).isoformat(timespec="seconds")

    fixture = load_fixture()
    fixture_by_match = {
        int(row["partido"]): row
        for _, row in fixture.iterrows()
    }

    saved_count = 0
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

        cur.execute(
            """
            INSERT INTO predictions(participant_id, match_id, goals_a, goals_b, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(participant_id, match_id)
            DO UPDATE SET goals_a=excluded.goals_a, goals_b=excluded.goals_b, updated_at=excluded.updated_at
            """,
            (participant_id, match_id, ga, gb, now),
        )
        saved_count += 1

    conn.commit()
    conn.close()

    return saved_count, blocked_count


def get_results():
    conn = get_conn()
    df = pd.read_sql_query("SELECT match_id, goals_a, goals_b FROM results", conn)
    conn.close()
    return df


def save_results(edited: pd.DataFrame):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")

    for _, row in edited.iterrows():
        match_id = int(row["partido"])
        ga = row.get("Gol real equipo 1")
        gb = row.get("Gol real equipo 2")

        ga = None if pd.isna(ga) else int(ga)
        gb = None if pd.isna(gb) else int(gb)

        if ga is None and gb is None:
            continue

        cur.execute(
            """
            INSERT INTO results(match_id, goals_a, goals_b, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(match_id)
            DO UPDATE SET goals_a=excluded.goals_a, goals_b=excluded.goals_b, updated_at=excluded.updated_at
            """,
            (match_id, ga, gb, now),
        )

    conn.commit()
    conn.close()


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
    fixture = load_fixture()
    results = get_results().rename(columns={"match_id": "partido", "goals_a": "real_a", "goals_b": "real_b"})
    participants = get_all_participants()

    conn = get_conn()
    predictions = pd.read_sql_query(
        "SELECT participant_id, match_id, goals_a AS pred_a, goals_b AS pred_b FROM predictions",
        conn,
    )
    conn.close()

    if participants.empty:
        return pd.DataFrame(columns=["Puesto", "Participante", "Puntaje", "Pronósticos llenados"])

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
            <p>Registra tus marcadores, sigue la tabla de posiciones y compite partido a partido en una app sencilla, visual y pensada para compartir por link.</p>
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
            st.session_state["participant_id"] = participant["id"]
            st.session_state["participant_name"] = participant["name"]
            st.success(msg)
        else:
            st.error(msg)

    if st.session_state.get("participant_id"):
        st.info(f"Sesión activa: {st.session_state['participant_name']}")
        if st.button("Cerrar sesión"):
            st.session_state.pop("participant_id", None)
            st.session_state.pop("participant_name", None)
            st.rerun()



def forecasts_page():
    if not st.session_state.get("participant_id"):
        st.warning("Primero debes ingresar o registrarte en la sección Participante.")
        return

    st.subheader(f"📝 Mis pronósticos: {st.session_state['participant_name']}")
    st.caption("Coloca solo los goles. Cada pronóstico se cierra automáticamente cuando inicia el partido.")

    fixture = load_fixture()
    predictions = get_predictions(st.session_state["participant_id"]).rename(
        columns={"match_id": "partido", "goals_a": "pred_a", "goals_b": "pred_b"}
    )

    data = fixture.merge(predictions, on="partido", how="left")

    fase_options = ["Todas"] + sorted(data["fase"].dropna().unique().tolist())
    fase = st.selectbox("Filtrar por fase", fase_options)

    if fase != "Todas":
        data = data[data["fase"] == fase].copy()

    group_options = ["Todos"] + sorted([g for g in data["grupo"].dropna().unique().tolist() if str(g).strip()])
    grupo = st.selectbox("Filtrar por grupo", group_options)

    if grupo != "Todos":
        data = data[data["grupo"] == grupo].copy()

    st.markdown("### Marcadores")
    st.markdown(
        "<p class='small-note'>Llena los goles de cada selección. La app muestra al instante el ganador y el perdedor.</p>",
        unsafe_allow_html=True,
    )

    edited_rows = []

    for _, row in data.iterrows():
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
                st.markdown("<span class='loser-tag'>🔒 Cerrado</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span class='winner-tag'>🟢 Abierto</span>", unsafe_allow_html=True)
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

        edited_rows.append({
            "partido": match_id,
            "Tu gol equipo 1": ga,
            "Tu gol equipo 2": gb,
        })

    edited = pd.DataFrame(edited_rows)

    st.divider()

    if st.button("💾 Guardar mis pronósticos", type="primary"):
        saved_count, blocked_count = save_predictions(st.session_state["participant_id"], edited)

        if saved_count > 0:
            st.success(f"Pronósticos guardados correctamente: {saved_count} partido(s).")
        else:
            st.info("No se guardaron nuevos pronósticos.")

        if blocked_count > 0:
            st.warning(f"{blocked_count} partido(s) ya estaban cerrados y no fueron modificados.")

        st.rerun()

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
    init_db()
    hero()
    stat_cards()

    admin_mode = st.query_params.get("admin", "") == "1"

    menu_items = ["Participante", "Mis pronósticos", "Ranking", "Fixture"]
    if admin_mode:
        menu_items.append("Administrador")

    menu = st.sidebar.radio("Menú", menu_items)

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
    if not admin_mode:
        st.sidebar.caption("Panel de administración oculto.")

if __name__ == "__main__":
    main()

