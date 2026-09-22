"""Streamlit chat frontend for Climora."""
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

    .starter {
      background: rgba(18, 28, 38, 0.95);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 0.9rem 1rem;
      min-height: 96px;
      box-shadow: 0 10px 26px rgba(0,0,0,0.08);
      color: var(--text);
      line-height: 1.5;
    }

    .starter strong {
      display: block;
      color: var(--primary);
      font-size: 0.68rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
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

    .meta-pill strong {
      color: var(--primary);
    }

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

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

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

st.markdown('<div class="topline"><span class="brand-mark">CLIMORA</span><span>Weather check, plain and simple</span></div>', unsafe_allow_html=True)
st.markdown('<section class="hero"><div class="hero-kicker">Outdoor advice, grounded in today\'s weather</div><h1>Should I head out?</h1><p class="hero-copy">Ask about cycling, kids, pets, travel, or a quick park outing. I’ll check the live conditions and tell you what the relevant safety rule says.</p></section>', unsafe_allow_html=True)

if not st.session_state.chat_history:
    st.markdown('<div class="section-label">Try one</div>', unsafe_allow_html=True)
    starter_cols = st.columns(3)
    starters = [("Ride", "Is it safe to cycle in Chennai today?"), ("Family", "Can I take my child to the park in Bengaluru?"), ("Leisure", "Would this afternoon be good for a picnic in Bhopal?")]
    for column, (label, text) in zip(starter_cols, starters):
        with column:
            st.markdown(f'<div class="starter"><strong>{label}</strong>{text}</div>', unsafe_allow_html=True)

st.markdown('<div class="section-label">Conversation</div>', unsafe_allow_html=True)
for role, text, meta in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(text)
        if meta:
            st.markdown(meta, unsafe_allow_html=True)

question = st.chat_input("Ask about an activity, city, and time...")
if question:
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
        st.markdown(result["answer"])
        meta_bits = [f'<span class="meta-pill"><strong>route</strong> {result["route"]}</span>']
        if result.get("primary_sop"):
            sop = result["primary_sop"]
            meta_bits.append(f'<span class="meta-pill"><strong>{sop["id"]}</strong> {sop["title"]}</span>')
        if result.get("secondary_sops"):
            ids = ", ".join(s["id"] for s in result["secondary_sops"])
            meta_bits.append(f'<span class="meta-pill"><strong>also</strong> {ids}</span>')
        if result.get("resolved_place_name"):
            meta_bits.append(f'<span class="meta-pill"><strong>location</strong> {result["resolved_place_name"]}</span>')
        meta = '<div class="meta-row">' + "".join(meta_bits) + "</div>"
        st.markdown(meta, unsafe_allow_html=True)
    st.session_state.chat_history.append(("assistant", result["answer"], meta))
