"""Streamlit chat frontend for Climora."""
import html
import sys
import uuid
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.graph import ask  # noqa: E402

st.set_page_config(page_title="Climora", page_icon="🌦️", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
      --bg: #0b1220;
      --bg-soft: #111b2a;
      --panel: rgba(17, 26, 36, 0.92);
      --panel-strong: #121e2d;
      --line: rgba(148, 163, 184, 0.14);
      --text: #edf4ff;
      --muted: #afc0d4;
      --primary: #7dd3fc;
      --primary-soft: rgba(125, 211, 252, 0.12);
      --secondary: #9ae6b4;
      --shadow: rgba(0, 0, 0, 0.38);
      --bubble-user: linear-gradient(135deg, #2d7df6, #1f5fd7);
      --bubble-assistant: rgba(19, 29, 41, 0.96);
    }

    .stApp {
      background:
        radial-gradient(circle at top left, rgba(45, 125, 246, 0.22), transparent 25%),
        radial-gradient(circle at bottom right, rgba(154, 230, 180, 0.12), transparent 30%),
        linear-gradient(180deg, var(--bg) 0%, #09141d 100%);
      color: var(--text);
      font-family: 'Inter', sans-serif;
    }

    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] {
      background: rgba(13, 20, 29, 0.92);
      border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.2rem; }

    h1, h2, h3, h4 {
      font-family: 'Inter', sans-serif;
      color: var(--text);
      letter-spacing: -0.04em;
    }

    .topline {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin: 0.2rem 0 1rem;
      color: var(--muted);
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }

    .brand-mark {
      color: var(--primary);
      font-weight: 800;
    }

    .hero {
      background: linear-gradient(135deg, rgba(17, 27, 39, 0.96), rgba(17, 31, 43, 0.9));
      border: 1px solid var(--line);
      border-radius: 22px;
      padding: 1.6rem 1.5rem;
      box-shadow: 0 18px 40px var(--shadow);
      margin-bottom: 0.8rem;
    }

    .hero-kicker {
      color: var(--secondary);
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      margin-bottom: 0.5rem;
    }

    .hero h1 {
      margin: 0;
      font-size: clamp(2rem, 4vw, 2.9rem);
      line-height: 1.05;
      letter-spacing: -0.05em;
      color: var(--text);
    }

    .hero-copy {
      max-width: 700px;
      color: var(--muted);
      font-size: 1rem;
      line-height: 1.6;
      margin-top: 0.7rem;
    }

    .section-label {
      color: var(--muted);
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      margin: 1.2rem 0 0.7rem;
    }

    .starter-btn button {
      background: rgba(18, 28, 38, 0.95) !important;
      border: 1px solid var(--line) !important;
      border-radius: 16px !important;
      padding: 0.9rem 1rem !important;
      min-height: 96px !important;
      box-shadow: 0 10px 26px rgba(0,0,0,0.08) !important;
      color: var(--text) !important;
      line-height: 1.5 !important;
      width: 100% !important;
      text-align: left !important;
      font-size: 0.9rem !important;
      white-space: normal !important;
      height: auto !important;
    }

    .starter-btn button:hover {
      border-color: var(--primary) !important;
      background: rgba(125, 211, 252, 0.06) !important;
    }

    .starter-label {
      color: var(--primary);
      font-size: 0.68rem;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      display: block;
      margin-bottom: 0.38rem;
    }

    .status-bar {
      border-top: 1px solid var(--line);
      margin-top: 1.3rem;
      padding-top: 0.9rem;
      color: var(--muted);
      font-size: 0.82rem;
      line-height: 1.8;
    }

    .weather-card {
      background: rgba(17, 27, 39, 0.95);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 0.9rem 1.1rem;
      margin-bottom: 0.8rem;
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
    }

    .weather-stat {
      display: flex;
      flex-direction: column;
      align-items: center;
      min-width: 70px;
    }

    .weather-stat .val {
      font-size: 1.3rem;
      font-weight: 700;
      color: var(--text);
      line-height: 1.1;
    }

    .weather-stat .lbl {
      font-size: 0.65rem;
      font-weight: 600;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-top: 0.2rem;
    }

    .meta-row {
      display: flex;
      flex-wrap: wrap;
      gap: 0.45rem;
      margin-top: 0.8rem;
    }

    .meta-pill {
      background: rgba(125, 211, 252, 0.08);
      border: 1px solid rgba(125, 211, 252, 0.2);
      border-radius: 999px;
      padding: 0.33rem 0.7rem;
      font-size: 0.72rem;
      font-weight: 600;
      color: var(--text);
    }

    .meta-pill strong { color: var(--primary); }

    .sev-critical { background: rgba(239,68,68,0.15); border-color: rgba(239,68,68,0.4); color: #fca5a5; }
    .sev-high     { background: rgba(249,115,22,0.15); border-color: rgba(249,115,22,0.4); color: #fdba74; }
    .sev-medium   { background: rgba(234,179,8,0.15); border-color: rgba(234,179,8,0.4); color: #fde047; }
    .sev-low      { background: rgba(34,197,94,0.15); border-color: rgba(34,197,94,0.4); color: #86efac; }

    [data-testid="stChatMessage"] {
      border: 0;
      padding-top: 0.9rem;
      padding-bottom: 0.9rem;
    }

    [data-testid="stChatMessageContent"] {
      border-radius: 18px;
      padding: 0.9rem 1rem;
      border: 1px solid rgba(148, 163, 184, 0.1);
    }

    [data-testid="stChatMessage"]:has(div[data-testid="chat-avatar-user"]) [data-testid="stChatMessageContent"] {
      background: var(--bubble-user);
      color: white;
    }

    [data-testid="stChatMessage"]:has(div[data-testid="chat-avatar-assistant"]) [data-testid="stChatMessageContent"] {
      background: var(--bubble-assistant);
      color: var(--text);
    }

    [data-testid="stChatInput"] {
      border: 1px solid rgba(148, 163, 184, 0.18);
      border-radius: 18px;
      box-shadow: 0 12px 28px rgba(0, 0, 0, 0.2);
      background: rgba(15, 23, 32, 0.9);
    }

    .stButton > button {
      border-radius: 12px;
      border: 1px solid rgba(148, 163, 184, 0.18);
      background: rgba(17, 26, 36, 0.96);
      color: var(--text);
      font-weight: 600;
    }

    .stButton > button:hover {
      border-color: var(--primary);
      color: var(--primary);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
SEV_EMOJI = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
SEV_CLASS = {"critical": "sev-critical", "high": "sev-high", "medium": "sev-medium", "low": "sev-low"}


def _weather_card(weather_data: dict) -> str:
    if not weather_data:
        return ""
    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})
    temp = current.get("temperature_2m", "—")
    uv = current.get("uv_index", None)
    if uv is None:
        uv = (daily.get("uv_index_max") or [None])[0]
    rain = (daily.get("precipitation_probability_max") or [None])[0]
    wind = current.get("wind_speed_10m", "—")
    humidity = current.get("relative_humidity_2m", "—")

    def stat(val, label):
        return f'<div class="weather-stat"><span class="val">{val}</span><span class="lbl">{label}</span></div>'

    parts = [stat(f"{temp}°C", "Temp")]
    if uv is not None:
        parts.append(stat(round(uv, 1), "UV Index"))
    if rain is not None:
        parts.append(stat(f"{rain}%", "Rain"))
    parts.append(stat(f"{wind} km/h", "Wind"))
    parts.append(stat(f"{humidity}%", "Humidity"))
    return '<div class="weather-card">' + "".join(parts) + "</div>"


def _meta_html(result: dict) -> str:
    bits = []
    sop = result.get("primary_sop")
    if sop:
        sev = sop.get("severity", "low")
        emoji = SEV_EMOJI.get(sev, "")
        cls = SEV_CLASS.get(sev, "")
        bits.append(f'<span class="meta-pill {cls}">{emoji} <strong>{sev}</strong></span>')
        bits.append(f'<span class="meta-pill"><strong>{sop["id"]}</strong> {sop["title"]}</span>')
    if result.get("secondary_sops"):
        ids = ", ".join(s["id"] for s in result["secondary_sops"])
        bits.append(f'<span class="meta-pill"><strong>also</strong> {ids}</span>')
    if result.get("resolved_place_name"):
        bits.append(f'<span class="meta-pill">📍 {html.escape(result["resolved_place_name"])}</span>')
    bits.append(f'<span class="meta-pill"><strong>route</strong> {result["route"]}</span>')
    return '<div class="meta-row">' + "".join(bits) + "</div>"


def _run_question(question: str):
    with st.chat_message("user"):
        st.markdown(question)
    st.session_state.chat_history.append(("user", question, None))
    with st.chat_message("assistant"):
        with st.spinner("Checking live conditions and matching policy..."):
            try:
                result = ask(question, thread_id=st.session_state.thread_id)
            except Exception as exc:  # noqa: BLE001
                st.error(f"The advisory desk is temporarily unavailable: {exc}")
                st.stop()
        weather_html = _weather_card(result.get("weather_data"))
        if weather_html:
            st.markdown(weather_html, unsafe_allow_html=True)
        st.markdown(result["answer"])
        meta = _meta_html(result)
        st.markdown(meta, unsafe_allow_html=True)
    st.session_state.chat_history.append(("assistant", result["answer"], (weather_html or "") + meta))


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🌦️ Climora")
    st.caption("Simple weather + safety check")
    st.markdown('<div class="section-label">Current session</div>', unsafe_allow_html=True)
    st.code(st.session_state.thread_id[:8] + "…", language=None)
    if st.button("＋  New session", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.rerun()
    st.markdown('<div class="status-bar">Live weather<br>Safety policy check<br>Session memory on</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<div class="topline"><span class="brand-mark">CLIMORA</span><span>Weather check, plain and simple</span></div>', unsafe_allow_html=True)
st.markdown('<section class="hero"><div class="hero-kicker">Outdoor advice, grounded in today\'s weather</div><h1>Should I head out?</h1><p class="hero-copy">Ask about cycling, kids, pets, travel, or a quick park outing. I\'ll check the live conditions and tell you what the relevant safety rule says.</p></section>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Starter cards (clickable)
# ---------------------------------------------------------------------------
if not st.session_state.chat_history:
    st.markdown('<div class="section-label">Try one</div>', unsafe_allow_html=True)
    starters = [
        ("🚴 Ride", "Is it safe to cycle in Chennai today?"),
        ("👨‍👧 Family", "Can I take my child to the park in Bengaluru?"),
        ("🧺 Leisure", "Would this afternoon be good for a picnic in Bhopal?"),
    ]
    cols = st.columns(3)
    for col, (label, text) in zip(cols, starters):
        with col:
            st.markdown(f'<div class="starter-btn">', unsafe_allow_html=True)
            if st.button(f"{label}\n\n{text}", key=f"starter_{label}", use_container_width=True):
                st.session_state.pending_question = text
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Chat history
# ---------------------------------------------------------------------------
st.markdown('<div class="section-label">Conversation</div>', unsafe_allow_html=True)
for role, text, meta in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(text)
        if meta:
            st.markdown(meta, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Handle pending starter click
# ---------------------------------------------------------------------------
if st.session_state.pending_question:
    q = st.session_state.pending_question
    st.session_state.pending_question = None
    _run_question(q)
    st.rerun()

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------
question = st.chat_input("Ask about an activity, city, and time...")
if question:
    _run_question(question)
