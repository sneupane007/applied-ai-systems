"""VibeMatch pipeline:
prompt -> moment -> labels -> history -> manual rules -> target point -> nearest songs -> re-rank
-> AI picks -> grounding check.

Every run is logged to logs/vibematch.log under a run ID. Raw signals, the city, the prompt text,
and the listening history are never logged.
"""
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

from src.context import Moment, apply_nudges, base_point, labels_for, time_of_day, validate
from src.explainer import ClaudeReasoner, Explanation, Reasoner, explain
from src.history import HistoryProfile, Play, blend, profile_for, rerank
from src.intent import ClaudeIntentParser, IntentParser, TextIntent, fill, read_prompt
from src.manual import Rule, load_manual, match_rules, nudges_for, preferences_for
from src.privacy import for_reasoner, music_intent
from src.retrieval import DEFAULT_K, LocalCatalog, MusicSource

LOG_PATH = "logs/vibematch.log"
SEARCH_POOL = 16  # retrieve this many, re-rank locally with history and genres, keep DEFAULT_K
NO_LYRICS_RANGE = ("instrumentalness", 0.5, 1.0)
logger = logging.getLogger("vibematch")

CRISIS_WORDS = (
    "suicide", "suicidal", "kill myself", "end my life", "want to die", "self harm",
    "self-harm", "hurt myself", "don't want to live", "dont want to live", "no reason to live",
)
SUPPORT_MESSAGE = (
    "It sounds like things might be really hard right now. You don't have to handle it alone. "
    "In the US, you can call or text 988 (Suicide & Crisis Lifeline) any time. "
    "Elsewhere, findahelpline.com lists free local helplines. If you're in immediate danger, "
    "call your local emergency number."
)


@dataclass
class Result:
    run_id: str
    labels: List[str]
    rules: List[Rule]
    nudges: List[str]
    base: Dict[str, float]
    target: Dict[str, float]
    candidates: List[Tuple[Dict, float]]
    explanation: Explanation
    support_message: Optional[str] = None
    moment: Optional[Moment] = None  # after the prompt filled in the Auto fields
    intent: TextIntent = field(default_factory=TextIntent)
    prompt_mode: str = "none"  # "ai", "keywords", or "none"
    from_prompt: List[str] = field(default_factory=list)  # Moment fields the prompt set
    prompt_notes: List[str] = field(default_factory=list)
    history: Optional[HistoryProfile] = None
    stated: Optional[Dict[str, float]] = None  # starting point before history


def setup_logging(path: str = LOG_PATH) -> None:
    """Send the 'vibematch' logger to a file (once per process)."""
    if logger.handlers:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def default_reasoner() -> Optional[Reasoner]:
    """Claude when ANTHROPIC_API_KEY is set (from the environment or .env); otherwise offline."""
    load_dotenv()
    return ClaudeReasoner() if os.getenv("ANTHROPIC_API_KEY") else None


def default_parser() -> Optional[IntentParser]:
    """Claude reads the prompt when ANTHROPIC_API_KEY is set; otherwise keywords do."""
    load_dotenv()
    return ClaudeIntentParser() if os.getenv("ANTHROPIC_API_KEY") else None


def needs_support(note: str) -> bool:
    text = note.lower()
    return any(word in text for word in CRISIS_WORDS)


def recommend_for_moment(moment: Moment, catalog: Optional[MusicSource] = None,
                         reasoner: Optional[Reasoner] = None, rules: Optional[List[Rule]] = None,
                         history: Optional[List[Play]] = None, parser: Optional[IntentParser] = None) -> Result:
    """`history` is one listener's past plays; `parser` reads the prompt (None means keywords)."""
    run_id = uuid.uuid4().hex[:8]
    validate(moment)
    catalog = catalog or LocalCatalog()

    support = SUPPORT_MESSAGE if needs_support(moment.note) else None
    if support:
        # Don't send a note like this anywhere: read it with keywords, use offline picks, show support first.
        logger.warning("run=%s support message shown; note not sent to the AI", run_id)
        reasoner = parser = None

    intent, prompt_mode, prompt_notes = read_prompt(moment.note, parser)
    moment, from_prompt = fill(moment, intent)
    moment = replace(moment, goal=moment.goal or "match")
    logger.info("run=%s inputs card=%s energy=%s goal=%s place=%s time=%s weather=%s note_chars=%d "
                "prompt=%s from_prompt=%s", run_id, moment.mood_card, moment.energy_level, moment.goal,
                moment.place, time_of_day(moment.hour), moment.weather or "unknown", len(moment.note),
                prompt_mode, from_prompt)

    labels = labels_for(moment)
    if intent.avoid_sad:
        labels.append("avoid_sad")
    if intent.instrumental:
        labels.append("no_lyrics")
    labels = sorted(labels)
    logger.info("run=%s labels=%s", run_id, labels)

    profile = None
    if history:
        profile = profile_for(history, {s["id"]: s for s in catalog.songs}, moment.hour, moment.weather, moment.place)
        logger.info("run=%s history persona=%s similar_plays=%s strength=%s", run_id, history[0].persona,
                    profile.similar_plays, profile.strength)
    stated = base_point(moment, profile.centroid if profile else None)
    base = blend(stated, profile)

    matched = match_rules(rules if rules is not None else load_manual(), labels)
    nudges = nudges_for(matched, labels)
    target = apply_nudges(base, nudges)
    logger.info("run=%s rules=%s nudges=%s base=%s target=%s", run_id, [r.id for r in matched],
                [n.describe() for n in nudges], base, target)

    prefer = preferences_for(matched)
    if intent.instrumental and not any(feature == "instrumentalness" for feature, _, _ in prefer):
        prefer.append(NO_LYRICS_RANGE)
    pool = catalog.search(music_intent(target, prefer), k=SEARCH_POOL)
    candidates = rerank(pool, profile, intent.genres_like, intent.genres_avoid)[:DEFAULT_K]
    logger.info("run=%s retrieved=%s", run_id, [(s["id"], d) for s, d in candidates])

    played_before = [s["id"] for s, _ in candidates if profile and s["id"] in profile.familiar]
    listener = for_reasoner(moment, labels, profile.summary() if profile else "none", played_before)
    started = time.monotonic()
    explanation = explain(reasoner, listener, matched, candidates, labels, moment.goal, target)
    latency_ms = round((time.monotonic() - started) * 1000)
    logger.info("run=%s mode=%s latency_ms=%d request_id=%s picks=%s", run_id, explanation.mode, latency_ms,
                getattr(reasoner, "last_request_id", None),
                [(p.song["id"], p.rule_ids) for p in explanation.picks])
    if explanation.rejected_song_ids or explanation.rejected_rule_ids:
        logger.warning("run=%s rejected songs=%s rules=%s", run_id,
                       explanation.rejected_song_ids, explanation.rejected_rule_ids)
    for note in prompt_notes + explanation.notes:
        logger.info("run=%s check: %s", run_id, note)

    return Result(run_id, labels, matched, [n.describe() for n in nudges], base, target, candidates, explanation,
                  support, moment=moment, intent=intent, prompt_mode=prompt_mode, from_prompt=from_prompt,
                  prompt_notes=prompt_notes, history=profile, stated=stated)
