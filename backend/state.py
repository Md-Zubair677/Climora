"""
Shared state for the LangGraph agent.

Design note: we carry both the raw LangGraph message history (for the LLM's
conversational context) AND a small set of structured "session facts"
(last_location, last_lat, last_lon) that get updated deterministically by code,
not recalled by the model. This is what lets a follow-up like "what about this
evening instead?" work without the user repeating the city, without relying on
the LLM to remember/guess coordinates.
"""
from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, TypedDict

from langgraph.graph.message import add_messages


class SOPMatch(TypedDict):
    id: str
    title: str
    severity: str
    category: str
    condition: str
    guidance: str


class AgentState(TypedDict, total=False):
    # Conversational history — LangGraph appends via add_messages reducer.
    messages: Annotated[list, add_messages]

    # --- Parsed from the latest turn (by parse_query node, LLM-assisted) ---
    raw_question: str
    is_greeting: bool
    location_text: Optional[str]      # e.g. "Bhopal" — None if not mentioned this turn
    location_text_effective: Optional[str]
    activity_hint: Optional[str]      # e.g. "cycling", "picnic", "taking my kid to the park"
    time_window: Optional[str]        # e.g. "today", "this evening", "tomorrow morning"

    # --- Session facts carried forward deterministically across turns ---
    last_location_text: Optional[str]
    last_lat: Optional[float]
    last_lon: Optional[float]
    last_resolved_name: Optional[str]  # geocoder's canonical name, for disclosure to user

    # --- Deterministic API outputs (ground truth; LLM never overwrites these) ---
    lat: Optional[float]
    lon: Optional[float]
    resolved_place_name: Optional[str]
    weather_data: Optional[dict[str, Any]]   # raw Open-Meteo response, as-received

    # --- Failure flags (drive branching) ---
    geocode_failed: bool
    weather_failed: bool
    error_detail: Optional[str]

    # --- SOP matching (structured LLM output) ---
    matched_sops: list[SOPMatch]
    primary_sop: Optional[SOPMatch]
    secondary_sops: list[SOPMatch]

    # --- Final output ---
    final_answer: Optional[str]
    route: Optional[Literal[
        "no_location", "weather_error", "no_sop_match", "answered"
    ]]
