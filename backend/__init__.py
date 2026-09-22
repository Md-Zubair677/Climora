"""Loads .env once, on first import of the backend package, so every module
(graph, llm, weather) and every entrypoint (Streamlit app, eval suite) sees
GEMINI_API_KEY etc. without each having to remember to call load_dotenv()."""
import os

from dotenv import load_dotenv

load_dotenv()

# On Streamlit Cloud, secrets are in st.secrets instead of .env.
# Sync them into os.environ so the rest of the backend can use os.environ as usual.
try:
    import streamlit as st
    for key in ("GEMINI_API_KEY", "GEMINI_MODEL", "GEMINI_EVAL_API_KEY"):
        if key in st.secrets and not os.environ.get(key):
            os.environ[key] = st.secrets[key]
except Exception:
    pass
