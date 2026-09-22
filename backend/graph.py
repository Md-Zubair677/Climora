r"""
LangGraph definition.

    START
      |
      v
  parse_query -----------------------------------------------+
      |                                                       |
      | (location resolved, this turn or carried forward)     | (no location at all,
      v                                                       |  never mentioned)
  geocode_location                                            v
      |                                                   no_location_node --> END
      | success              \ failure
      v                       v
  fetch_weather          location_error_node --> END
      |            \ failure
      | success      v
      v          weather_error_node --> END
  match_sops
      |            \ no matches
      | matches      v
      v          no_sop_node --> END
  compose_answer
      |
      v
     END

Every terminal node writes `final_answer` and `route` so the caller (and the
eval suite) can assert both the text AND the branch that was taken.
"""
from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from backend import llm, weather
from backend.sop_loader import format_sops_for_prompt, load_sops, severity_rank
from backend.state import AgentState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _is_greeting(question: str) -> bool:
    normalized = re.sub(r"[^a-z\s]", " ", question.lower()).strip()
    return normalized in {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}


def _lc_history(messages: list) -> list[dict[str, Any]]:
    """Convert LangGraph messages into plain role/content dictionaries,
    excluding the current turn because the caller appends it."""
    out = []
    for m in messages:
        if isinstance(m, HumanMessage):
            out.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            out.append({"role": "assistant", "content": m.content})
    return out


def _summarize_weather(data: dict[str, Any]) -> str:
    """Render the raw Open-Meteo response into a compact, human/LLM-readable
    block. This is the ONLY place weather numbers are formatted for prompts —
    every number here is copied verbatim from the API response dict, nothing
    computed or guessed."""
    current = data.get("current", {})
    daily = data.get("daily", {})
    lines = ["CURRENT:"]
    for k, v in current.items():
        if k != "time":
            lines.append(f"  {k}: {v}")
    if daily:
        lines.append("TODAY'S FORECAST RANGE:")
        for k, v in daily.items():
            if k != "time" and isinstance(v, list) and v:
                lines.append(f"  {k}: {v[0]}")
    return "\n".join(lines)


def _keyword_match_sops(question: str, activity_hint: str, sops: list) -> list:
    """Deterministic keyword fallback — always runs as a safety net."""
    q = question.lower()
    a = (activity_hint or "").lower()
    sop_map = {s["id"]: s for s in sops}
    ids = set()
    if any(w in q or w in a for w in ["cycl", "bik", "two-wheel", "scooter", "motorcycle"]):
        ids.update(["SOP-001", "SOP-002", "SOP-003"])
    if any(w in q or w in a for w in ["run", "jog", "exercise", "sport", "gym"]):
        ids.update(["SOP-001", "SOP-003"])
    if any(w in q or w in a for w in ["child", "kid", "park", "play", "school"]):
        ids.update(["SOP-009"])
    if any(w in q or w in a for w in ["elder", "grandp", "senior", "old"]):
        ids.update(["SOP-008"])
    if any(w in q or w in a for w in ["dog", "pet", "pup"]):
        ids.update(["SOP-010"])
    if any(w in q or w in a for w in ["drive", "travel", "commut", "road", "trip"]):
        ids.update(["SOP-005"])
    if any(w in q or w in a for w in ["picnic", "leisure", "outing", "walk", "stroll"]):
        ids.update(["SOP-012"])
    return [sop_map[i] for i in ids if i in sop_map]

def parse_query_node(state: AgentState) -> dict[str, Any]:
    question = state["raw_question"]
    if _is_greeting(question):
        return {"is_greeting": True, "location_text": None, "location_text_effective": None}
    history = _lc_history(state.get("messages", []))
    try:
        parsed = llm.parse_query(history, question)
        location_text = parsed.get("location_text")
        activity_hint = parsed.get("activity_hint")
        time_window = parsed.get("time_window")
    except Exception:
        # LLM unavailable — fall back to regex extraction so the pipeline
        # can still geocode and fetch weather.
        from backend.llm import _extract_location_fallback
        location_text = _extract_location_fallback(question)
        activity_hint = None
        time_window = None
    effective_location = location_text or state.get("last_location_text")
    return {
        "location_text": location_text,
        "activity_hint": activity_hint,
        "time_window": time_window,
        "location_text_effective": effective_location,
    }


def route_after_parse(state: AgentState) -> str:
    if state.get("is_greeting"):
        return "no_location"
    if not state.get("location_text_effective") and not state.get("last_lat"):
        return "no_location"
    return "geocode"


def geocode_node(state: AgentState) -> dict[str, Any]:
    effective_location = state.get("location_text_effective")
    # If no new location was mentioned this turn but we have cached coords
    # from earlier in the session, reuse them directly — no need to re-hit
    # the geocoder for a place we already resolved this session.
    if not state.get("location_text") and state.get("last_lat") is not None:
        return {
            "lat": state["last_lat"],
            "lon": state["last_lon"],
            "resolved_place_name": state["last_resolved_name"],
            "geocode_failed": False,
        }
    try:
        info = weather.geocode_location(effective_location)
        return {
            "lat": info["lat"],
            "lon": info["lon"],
            "resolved_place_name": info["resolved_name"],
            "geocode_failed": False,
        }
    except weather.GeocodeError as exc:
        return {"geocode_failed": True, "error_detail": str(exc)}


def route_after_geocode(state: AgentState) -> str:
    return "weather_error" if state.get("geocode_failed") else "fetch_weather"


def fetch_weather_node(state: AgentState) -> dict[str, Any]:
    try:
        data = weather.fetch_forecast(state["lat"], state["lon"])
        return {
            "weather_data": data,
            "weather_failed": False,
            # Update session facts for future turns in this thread.
            "last_location_text": state.get("location_text_effective"),
            "last_lat": state["lat"],
            "last_lon": state["lon"],
            "last_resolved_name": state["resolved_place_name"],
        }
    except weather.WeatherAPIError as exc:
        return {"weather_failed": True, "error_detail": str(exc)}


def route_after_weather(state: AgentState) -> str:
    return "weather_error" if state.get("weather_failed") else "match_sops"


def match_sops_node(state: AgentState) -> dict[str, Any]:
    sops = load_sops()
    valid_ids = [s["id"] for s in sops]
    weather_summary = _summarize_weather(state["weather_data"])
    try:
        result = llm.match_sops(
            question=state["raw_question"],
            activity_hint=state.get("activity_hint"),
            time_window=state.get("time_window"),
            weather_summary=weather_summary,
            sops_prompt_block=format_sops_for_prompt(),
            valid_ids=valid_ids,
        )
    except Exception as exc:
        return {"weather_failed": True, "error_detail": f"Policy matching unavailable: {exc}"}
    matched_ids = [i for i in result.get("matched_ids", []) if i in valid_ids]
    matched = [s for s in sops if s["id"] in matched_ids]
    matched.sort(key=lambda s: severity_rank(s["severity"]), reverse=True)
    if not matched:
        # Fallback: if LLM returned no matches but activity is clearly covered,
        # match by keyword against SOP conditions deterministically.
        q = state["raw_question"].lower()
        activity = (state.get("activity_hint") or "").lower()
        fallback = []
        if any(w in q or w in activity for w in ["cycl", "bik", "two-wheel", "scooter", "motorcycle"]):
            fallback += [s for s in sops if s["id"] in ("SOP-001", "SOP-002", "SOP-003")]
        if any(w in q or w in activity for w in ["run", "jog", "walk", "exercise", "sport"]):
            fallback += [s for s in sops if s["id"] in ("SOP-001", "SOP-003")]
        if any(w in q or w in activity for w in ["child", "kid", "park", "play"]):
            fallback += [s for s in sops if s["id"] in ("SOP-009",)]
        if any(w in q or w in activity for w in ["drive", "travel", "commut", "road"]):
            fallback += [s for s in sops if s["id"] in ("SOP-005",)]
        # deduplicate preserving order
        seen = set()
        matched = [s for s in fallback if not (s["id"] in seen or seen.add(s["id"]))]
        matched.sort(key=lambda s: severity_rank(s["severity"]), reverse=True)
    if not matched:
        return {"matched_sops": [], "primary_sop": None, "secondary_sops": []}
    return {
        "matched_sops": matched,
        "primary_sop": matched[0],
        "secondary_sops": matched[1:],
    }


def route_after_match(state: AgentState) -> str:
    return "compose" if state.get("primary_sop") else "no_sop"


def compose_answer_node(state: AgentState) -> dict[str, Any]:
    weather_summary = _summarize_weather(state["weather_data"])
    history = _lc_history(state.get("messages", []))
    try:
        answer = llm.compose_answer(
            question=state["raw_question"],
            weather_summary=weather_summary,
            resolved_place_name=state["resolved_place_name"],
            primary_sop=state["primary_sop"],
            secondary_sops=state.get("secondary_sops", []),
            history_messages=history,
        )
    except Exception as exc:
        answer = (
            f"I found the relevant safety policy but couldn't generate a response right now ({exc}). "
            f"The applicable rule is [{state['primary_sop']['id']}] {state['primary_sop']['title']}: "
            f"{state['primary_sop']['guidance']}"
        )
    return {
        "final_answer": answer,
        "route": "answered",
    }


def no_sop_node(state: AgentState) -> dict[str, Any]:
    answer = (
        "I don't have a specific SOP covering that question yet, so I don't want to invent "
        "safety advice."
    )
    return {
        "final_answer": answer,
        "route": "no_sop_match",
    }


def location_error_node(state: AgentState) -> dict[str, Any]:
    if state.get("is_greeting"):
        answer = (
            "Hi! Tell me the city and outdoor activity you have in mind, "
            "and I’ll check the live weather and applicable safety policy."
        )
    else:
        answer = (
            "I couldn't figure out which location you mean, and I don't want to guess. "
            "Could you tell me the city or area so I can check the actual forecast there?"
        )
    return {
        "final_answer": answer,
        "route": "no_location",
        "lat": None,
        "lon": None,
        "resolved_place_name": None,
        "weather_data": None,
        "matched_sops": [],
        "primary_sop": None,
        "secondary_sops": [],
    }


def weather_error_node(state: AgentState) -> dict[str, Any]:
    detail = state.get("error_detail", "an unknown error")
    answer = (
        "I wasn't able to get live weather data for that location just now "
        f"({detail}). I don't want to guess at conditions I can't actually confirm — "
        "could you try again in a moment, or double-check the location name?"
    )
    return {
        "final_answer": answer,
        "route": "weather_error",
        "lat": None,
        "lon": None,
        "resolved_place_name": None,
        "weather_data": None,
        "matched_sops": [],
        "primary_sop": None,
        "secondary_sops": [],
    }


def update_session_state_node(state: AgentState) -> dict[str, Any]:
    """Persist the completed turn after every response path."""
    answer = state.get("final_answer")
    if not answer:
        return {}
    return {
        "messages": [
            HumanMessage(content=state["raw_question"]),
            AIMessage(content=answer),
        ]
    }


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------
def build_graph():
    g = StateGraph(AgentState)

    g.add_node("parse_query", parse_query_node)
    g.add_node("geocode", geocode_node)
    g.add_node("fetch_weather", fetch_weather_node)
    g.add_node("match_sops", match_sops_node)
    g.add_node("compose_answer", compose_answer_node)
    g.add_node("no_sop", no_sop_node)
    g.add_node("no_location", location_error_node)
    g.add_node("weather_error", weather_error_node)
    g.add_node("update_session_state", update_session_state_node)

    g.set_entry_point("parse_query")

    g.add_conditional_edges(
        "parse_query", route_after_parse, {"no_location": "no_location", "geocode": "geocode"}
    )
    g.add_conditional_edges(
        "geocode", route_after_geocode, {"weather_error": "weather_error", "fetch_weather": "fetch_weather"}
    )
    g.add_conditional_edges(
        "fetch_weather", route_after_weather, {"weather_error": "weather_error", "match_sops": "match_sops"}
    )
    g.add_conditional_edges(
        "match_sops", route_after_match, {"compose": "compose_answer", "no_sop": "no_sop"}
    )

    g.add_edge("compose_answer", "update_session_state")
    g.add_edge("no_sop", "update_session_state")
    g.add_edge("no_location", "update_session_state")
    g.add_edge("weather_error", "update_session_state")
    g.add_edge("update_session_state", END)

    return g.compile(checkpointer=MemorySaver())


# Module-level singleton graph + one shared checkpointer for the process.
_GRAPH = None


def get_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH


def ask(question: str, thread_id: str) -> dict[str, Any]:
    """Main entrypoint used by the frontend and eval suite.

    thread_id scopes memory to one chat session (per spec: session, not
    cross-session persistence — MemorySaver here is in-process/in-memory and
    resets when the process restarts).
    """
    graph = get_graph()
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke({"raw_question": question}, config=config)
    return {
        "answer": result.get("final_answer"),
        "route": result.get("route"),
        "primary_sop": result.get("primary_sop"),
        "secondary_sops": result.get("secondary_sops", []),
        "resolved_place_name": result.get("resolved_place_name"),
        "weather_data": result.get("weather_data"),
    }
